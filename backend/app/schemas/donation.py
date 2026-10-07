"""
Pydantic v2 schemas for Razorpay Orders, UPI Checkout, 80G Receipts,
Campaigns, and Public Transparency Allocations.
"""
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re


class DonationOrderCreate(BaseModel):
    amount_inr: float = Field(..., ge=10.0, description="Donation amount in INR (minimum ₹10)")
    donor_name: str = Field(..., min_length=2, max_length=120)
    donor_email: str = Field(...)
    donor_phone: Optional[str] = None
    donor_pan: Optional[str] = Field(None, description="Indian PAN (10 alphanumeric characters for 80G benefit)")
    donor_address: Optional[str] = None
    campaign_id: Optional[str] = None

    @field_validator("donor_pan")
    @classmethod
    def validate_pan(cls, v: Optional[str]) -> Optional[str]:
        if not v:
            return None
        clean = v.strip().upper()
        if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$", clean):
            raise ValueError("Invalid PAN format. Must be a valid 10-character Indian PAN (e.g. ABCDE1234F)")
        return clean


class DonationOrderResponse(BaseModel):
    order_id: str
    amount_inr: float
    amount_paise: int
    currency: str = "INR"
    key_id: str
    donation_id: str


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class DonationResponse(BaseModel):
    id: str
    amount_inr: float
    currency: str
    donor_name: str
    donor_email: str
    donor_pan: Optional[str] = None
    payment_status: str
    receipt_number: Optional[str] = None
    receipt_pdf_url: Optional[str] = None
    tax_exemption_80g_issued: bool
    campaign_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CampaignCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    target_amount_inr: float = Field(..., ge=1000.0)
    cover_image_url: Optional[str] = None
    hospital_id: Optional[str] = None


class CampaignResponse(BaseModel):
    id: str
    title: str
    slug: str
    description: str
    target_amount_inr: float
    raised_amount_inr: float
    progress_percent: float
    cover_image_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class FundAllocationCreate(BaseModel):
    category: str = Field(
        ...,
        pattern="^(rescue_ops|shelters|medical_supplies|food_feeding|infrastructure|admin)$"
    )
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    amount_inr: float = Field(..., ge=1.0)
    allocation_date: date
    receipt_url: Optional[str] = None


class FundAllocationResponse(BaseModel):
    id: str
    category: str
    title: str
    description: Optional[str] = None
    amount_inr: float
    allocation_date: date
    receipt_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TransparencySummaryResponse(BaseModel):
    total_raised_inr: float
    total_allocated_inr: float
    donations_count: int
    category_breakdown: Dict[str, float]
    recent_allocations: List[FundAllocationResponse]
    active_campaigns: List[CampaignResponse]
