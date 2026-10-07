"""
Security utilities: JWT token generation and verification, OTP hashing, and random tokens.
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from app.core.config import settings
from app.core.exceptions import AuthenticationError


def hash_otp(code: str) -> str:
    """
    Hash a 6-digit OTP code using HMAC-SHA256 with the app's secret key.
    Prevents storage of plaintext codes in the database.
    """
    return hmac.new(
        settings.SECRET_KEY.encode(),
        code.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_otp_hash(plain_code: str, hashed_code: str) -> bool:
    """
    Constant-time comparison of OTP code to avoid timing attacks.
    """
    computed = hash_otp(plain_code)
    return hmac.compare_digest(computed, hashed_code)


def generate_numeric_otp(digits: int = 6) -> str:
    """
    Generate a cryptographically secure numeric OTP of given length.
    """
    range_start = 10 ** (digits - 1)
    range_end = (10 ** digits) - 1
    return str(secrets.randbelow(range_end - range_start + 1) + range_start)


def generate_secure_token(nbytes: int = 32) -> str:
    """
    Generate a URL-safe random string for one-time links (e.g., hospital emergency accept).
    """
    return secrets.token_urlsafe(nbytes)


def create_access_token(
    subject: str,
    role: str,
    extra_claims: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generate a signed JWT access token.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: str,
    role: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Generate a signed JWT refresh token.
    """
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str, expected_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Decode and validate a JWT token. Raises AuthenticationError on expiration or invalid signature.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if expected_type and payload.get("type") != expected_type:
            raise AuthenticationError(f"Invalid token type: expected {expected_type}")
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired. Please log in again.")
    except jwt.PyJWTError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")
