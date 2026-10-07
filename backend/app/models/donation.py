"""
Campaign, Donation, and FundAllocation models for Razorpay UPI donations,
80G tax exemption receipts, and public fund transparency tracking.
"""
import uuid
from datetime import datetime, date, timezone
from typing import Optional, List
from sqlalchemy import (
    String, Boolean, Float, Integer, DateTime, Date, ForeignKey, Text, Numeric
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    target_amount_inr: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    raised_amount_inr: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False
    )
    cover_image_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    hospital_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("vet_hospitals.id", ondelete="SET NULL"),
        nullable=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    donations: Mapped[List["Donation"]] = relationship("Donation", back_populates="campaign")
    hospital = relationship("VetHospital")

    def __repr__(self) -> str:
        return f"<Campaign(slug='{self.slug}', raised={self.raised_amount_inr})>"


class Donation(Base, TimestampMixin):
    __tablename__ = "donations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    campaign_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    amount_inr: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(5),
        default="INR",
        nullable=False
    )
    donor_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False
    )
    donor_email: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    donor_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    donor_pan: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        index=True
    )  # Required for Indian 80G tax benefit
    donor_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    razorpay_order_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True
    )
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        index=True
    )
    razorpay_signature: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    payment_status: Mapped[str] = mapped_column(
        String(32),
        default="created",
        nullable=False,
        index=True
    )  # 'created', 'authorized', 'captured', 'failed', 'refunded'
    payment_method: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True
    )  # 'upi', 'card', 'netbanking'
    receipt_number: Mapped[Optional[str]] = mapped_column(
        String(64),
        unique=True,
        nullable=True,
        index=True
    )
    receipt_pdf_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    tax_exemption_80g_issued: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    campaign = relationship("Campaign", back_populates="donations")

    def __repr__(self) -> str:
        return f"<Donation(id='{self.id}', amount={self.amount_inr}, status='{self.payment_status}')>"


class FundAllocation(Base):
    __tablename__ = "fund_allocations"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )  # 'rescue_ops', 'shelters', 'medical_supplies', 'food_feeding', 'infrastructure'
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    amount_inr: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    allocation_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True
    )
    receipt_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    verified_by_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id"),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    verified_by = relationship("User", foreign_keys=[verified_by_id])

    def __repr__(self) -> str:
        return f"<FundAllocation(category='{self.category}', amount={self.amount_inr})>"
