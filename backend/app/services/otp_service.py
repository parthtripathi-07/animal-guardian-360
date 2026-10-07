"""
OTP Service: Generation, Hashing, Dispatching, Rate Limiting, and Verification.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import generate_numeric_otp, hash_otp, verify_otp_hash
from app.core.redis import cache_service
from app.core.exceptions import InvalidOTPError, RateLimitExceededError
from app.models.user import OTPCode

logger = logging.getLogger(__name__)


class OTPService:
    @staticmethod
    async def request_otp(
        db: AsyncSession,
        identifier: str,
        purpose: str = "login"
    ) -> Tuple[str, int]:
        """
        Generates and stores an OTP for the given phone or email.
        Enforces a rate limit of max 3 OTP requests per 10 minutes per identifier.
        Returns: (raw_otp: str, expires_in_seconds: int)
        """
        # Rate limiting check
        rate_key = f"otp_rate:{identifier}"
        allowed, remaining = await cache_service.check_rate_limit(
            rate_key,
            max_requests=settings.OTP_MAX_ATTEMPTS,
            window_seconds=settings.OTP_EXPIRE_MINUTES * 60
        )
        if not allowed:
            raise RateLimitExceededError(
                f"Too many OTP requests for {identifier}. Please wait a few minutes before trying again."
            )

        # Invalidate previous unused OTPs for this identifier and purpose
        await db.execute(
            update(OTPCode)
            .where(
                OTPCode.identifier == identifier,
                OTPCode.purpose == purpose,
                OTPCode.is_used == False
            )
            .values(is_used=True)
        )

        raw_otp = generate_numeric_otp(6)
        hashed = hash_otp(raw_otp)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)

        otp_record = OTPCode(
            identifier=identifier,
            code_hash=hashed,
            purpose=purpose,
            expires_at=expires_at,
            max_attempts=settings.OTP_MAX_ATTEMPTS,
            attempts=0,
            is_used=False
        )
        db.add(otp_record)
        await db.commit()

        # Dispatch via simulated or configured provider
        if settings.MOCK_OTP_MODE:
            logger.info("==========================================")
            logger.info(" [MOCK OTP] For: %s | Code: %s | Purpose: %s", identifier, raw_otp, purpose)
            logger.info("==========================================")
        else:
            # Here we integrate SMS (MSG91/Twilio) or Email (SES/SendGrid)
            logger.info("Dispatching live OTP to %s", identifier)

        expires_in = settings.OTP_EXPIRE_MINUTES * 60
        return raw_otp, expires_in

    @staticmethod
    async def verify_otp(
        db: AsyncSession,
        identifier: str,
        code: str,
        purpose: str = "login"
    ) -> bool:
        """
        Verifies the provided 6-digit OTP code against the stored hash.
        Throttles attempts and invalidates the code once consumed.
        """
        now = datetime.now(timezone.utc)
        stmt = (
            select(OTPCode)
            .where(
                OTPCode.identifier == identifier,
                OTPCode.purpose == purpose,
                OTPCode.is_used == False
            )
            .order_by(OTPCode.created_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            raise InvalidOTPError("No active verification code found. Please request a new one.")

        expires_at = record.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if now > expires_at:
            record.is_used = True
            await db.commit()
            raise InvalidOTPError("Verification code has expired. Please request a new code.")

        if record.attempts >= record.max_attempts:
            record.is_used = True
            await db.commit()
            raise InvalidOTPError("Too many incorrect attempts. This code has been invalidated.")

        # Check hash
        if not verify_otp_hash(code, record.code_hash):
            record.attempts += 1
            await db.commit()
            remaining = record.max_attempts - record.attempts
            raise InvalidOTPError(f"Incorrect verification code. {remaining} attempt(s) remaining.")

        # Success - mark as used
        record.is_used = True
        await db.commit()
        return True


otp_service = OTPService()
