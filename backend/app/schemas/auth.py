"""
Pydantic v2 schemas for Authentication, OTP validation, and User profiles.
"""
import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class SendOTPRequest(BaseModel):
    identifier: str = Field(
        ...,
        description="Indian mobile number (e.g. +919876543210 or 9876543210) or valid email address",
        examples=["+919876543210", "user@example.com"]
    )
    purpose: str = Field(
        default="login",
        pattern="^(login|verify_phone|verify_email)$",
        description="Purpose of OTP"
    )

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        clean = v.strip()
        # Email format check
        if "@" in clean:
            email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
            if not re.match(email_regex, clean):
                raise ValueError("Invalid email format")
            return clean.lower()

        # Phone format check (Indian numbers: +91 optional, 10 digits starting with 6-9)
        digits = re.sub(r"[^\d]", "", clean)
        if len(digits) == 10 and digits[0] in "6789":
            return f"+91{digits}"
        elif len(digits) == 12 and digits.startswith("91") and digits[2] in "6789":
            return f"+{digits}"
        raise ValueError("Invalid phone number. Must be a 10-digit Indian mobile number")


class SendOTPResponse(BaseModel):
    success: bool = True
    message: str
    identifier: str
    expires_in_seconds: int
    # Included only when settings.MOCK_OTP_MODE is True for local dev / automated testing
    dev_otp: Optional[str] = None


class VerifyOTPRequest(BaseModel):
    identifier: str = Field(..., description="Phone number or email that requested the OTP")
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$", description="6-digit verification code")
    purpose: str = Field(default="login", pattern="^(login|verify_phone|verify_email)$")

    @field_validator("identifier")
    @classmethod
    def normalize_identifier(cls, v: str) -> str:
        clean = v.strip()
        if "@" in clean:
            return clean.lower()
        digits = re.sub(r"[^\d]", "", clean)
        if len(digits) == 10:
            return f"+91{digits}"
        if len(digits) == 12 and digits.startswith("91"):
            return f"+{digits}"
        return clean


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Valid JWT refresh token")


class UserProfileResponse(BaseModel):
    id: str
    phone: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    strike_count: int
    is_reporting_suspended: bool
    preferred_locale: str

    model_config = {"from_attributes": True}


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfileResponse


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=120)
    email: Optional[str] = None
    preferred_locale: Optional[str] = Field(None, pattern="^(en|hi)$")
