"""
Authentication API endpoints: OTP request, OTP verification, Token refresh, and Profile.
"""
from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user
from app.core.exceptions import AuthenticationError, ConflictError
from app.models.user import User, Role
from app.schemas.auth import (
    SendOTPRequest,
    SendOTPResponse,
    VerifyOTPRequest,
    RefreshTokenRequest,
    TokenPairResponse,
    UserProfileResponse,
    UpdateProfileRequest
)
from app.services.otp_service import otp_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


async def get_or_create_default_role(db: AsyncSession, role_name: str = "user") -> Role:
    """Helper to ensure role exists in DB."""
    stmt = select(Role).where(Role.name == role_name)
    res = await db.execute(stmt)
    role = res.scalar_one_or_none()
    if not role:
        role = Role(name=role_name, description=f"Default {role_name} role")
        db.add(role)
        await db.commit()
        await db.refresh(role)
    return role


def user_to_profile(user: User) -> UserProfileResponse:
    """Helper to convert User model to UserProfileResponse schema."""
    return UserProfileResponse(
        id=user.id,
        phone=user.phone,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        role=user.role.name if user.role else "user",
        is_active=user.is_active,
        is_verified=user.is_verified,
        strike_count=user.strike_count,
        is_reporting_suspended=user.is_reporting_suspended,
        preferred_locale=user.preferred_locale
    )


@router.post(
    "/otp/send",
    response_model=SendOTPResponse,
    status_code=status.HTTP_200_OK,
    summary="Request a 6-digit OTP for phone or email"
)
async def send_otp(
    payload: SendOTPRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Sends a 6-digit verification code to the specified Indian mobile number or email address.
    In local development / mock mode, the OTP is returned directly in the response for convenience.
    """
    raw_otp, expires_in = await otp_service.request_otp(
        db=db,
        identifier=payload.identifier,
        purpose=payload.purpose
    )

    return SendOTPResponse(
        success=True,
        message=f"Verification code sent to {payload.identifier}",
        identifier=payload.identifier,
        expires_in_seconds=expires_in,
        dev_otp=raw_otp if settings.MOCK_OTP_MODE else None
    )


@router.post(
    "/otp/verify",
    response_model=TokenPairResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify OTP and obtain JWT tokens"
)
async def verify_otp(
    payload: VerifyOTPRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Verifies the OTP code. If the user does not exist, an account is automatically created.
    Returns access and refresh JWT tokens along with the user profile.
    """
    await otp_service.verify_otp(
        db=db,
        identifier=payload.identifier,
        code=payload.code,
        purpose=payload.purpose
    )

    is_email = "@" in payload.identifier
    query = select(User).where(User.email == payload.identifier if is_email else User.phone == payload.identifier)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        default_role = await get_or_create_default_role(db, "user")
        user = User(
            email=payload.identifier if is_email else None,
            phone=payload.identifier if not is_email else None,
            role_id=default_role.id,
            is_verified=True,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        if not user.is_verified:
            user.is_verified = True
            await db.commit()
            await db.refresh(user)

    user_role = user.role.name if user.role else "user"
    access_token = create_access_token(subject=user.id, role=user_role)
    refresh_token = create_refresh_token(subject=user.id, role=user_role)

    return TokenPairResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_to_profile(user)
    )


@router.post(
    "/refresh",
    response_model=TokenPairResponse,
    status_code=status.HTTP_200_OK,
    summary="Exchange refresh token for a new token pair"
)
async def refresh_token(
    payload: RefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Validates the refresh token and issues a fresh access & refresh token pair.
    """
    token_data = decode_token(payload.refresh_token, expected_type="refresh")
    user_id = token_data.get("sub")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise AuthenticationError("User is no longer active or valid")

    user_role = user.role.name if user.role else "user"
    new_access_token = create_access_token(subject=user.id, role=user_role)
    new_refresh_token = create_refresh_token(subject=user.id, role=user_role)

    return TokenPairResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user_to_profile(user)
    )


@router.get(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile"
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Returns the authenticated user's profile details.
    """
    return user_to_profile(current_user)


@router.patch(
    "/me",
    response_model=UserProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile"
)
async def update_me(
    payload: UpdateProfileRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Updates profile details such as full name, email, and preferred locale (en/hi).
    """
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.preferred_locale is not None:
        current_user.preferred_locale = payload.preferred_locale
    if payload.email is not None and payload.email != current_user.email:
        # Check if email is already claimed by another user
        existing_stmt = select(User).where(User.email == payload.email, User.id != current_user.id)
        existing = await db.execute(existing_stmt)
        if existing.scalar_one_or_none():
            raise ConflictError("Email address is already in use by another account")
        current_user.email = payload.email

    await db.commit()
    await db.refresh(current_user)
    return user_to_profile(current_user)
