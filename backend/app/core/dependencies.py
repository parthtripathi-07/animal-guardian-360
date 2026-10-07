"""
FastAPI dependency injectors for DB session, authentication, and role authorization.
"""
from typing import Annotated, List, Callable
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import AuthenticationError, ForbiddenError, AccountSuspendedError
from app.models.user import User

security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> User:
    """
    Decodes the Bearer JWT access token and loads the authenticated User.
    """
    if not credentials or not credentials.credentials:
        raise AuthenticationError("Authentication token is required")

    payload = decode_token(credentials.credentials, expected_type="access")
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationError("Invalid token payload: missing subject")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise AuthenticationError("User associated with this token no longer exists")

    if not user.is_active:
        raise ForbiddenError("User account is deactivated")

    return user


def require_roles(allowed_roles: List[str]) -> Callable:
    """
    Dependency factory that checks if current user belongs to one of the required roles.
    Example: Depends(require_roles(["admin", "hospital"]))
    """
    async def role_checker(
        current_user: Annotated[User, Depends(get_current_user)]
    ) -> User:
        user_role = current_user.role.name if current_user.role else "user"
        if user_role not in allowed_roles:
            raise ForbiddenError(
                f"Action requires one of the following roles: {', '.join(allowed_roles)}"
            )
        return current_user

    return role_checker


async def require_active_reporter(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Ensures the user has not been temporarily suspended under the 3-strike anti-abuse system.
    """
    if current_user.is_reporting_suspended:
        raise AccountSuspendedError(
            "Your reporting privileges have been temporarily suspended due to previous false reports."
        )
    return current_user
