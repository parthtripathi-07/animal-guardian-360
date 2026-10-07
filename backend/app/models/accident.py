"""
AccidentAlert and AlertDispatch models for emergency animal road accident SOS flow.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, DateTime, ForeignKey, Text, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin


class AccidentAlert(Base, TimestampMixin):
    __tablename__ = "accident_alerts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    reporter_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    reporter_phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True
    )
    animal_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )
    condition_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    photo_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True
    )
    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True
    )
    address_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="alerted",
        nullable=False,
        index=True
    )  # 'alerted', 'accepted', 'reached', 'closed', 'cancelled'
    accepted_hospital_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("vet_hospitals.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    reached_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    eta_minutes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True
    )

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id])
    accepted_hospital = relationship("VetHospital", back_populates="accepted_accidents")
    dispatches: Mapped[List["AlertDispatch"]] = relationship(
        "AlertDispatch",
        back_populates="alert",
        cascade="all, delete-orphan",
        order_by="AlertDispatch.dispatched_at.desc()"
    )

    def __repr__(self) -> str:
        return f"<AccidentAlert(id='{self.id}', animal='{self.animal_type}', status='{self.status}')>"


class AlertDispatch(Base):
    __tablename__ = "alert_dispatches"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    alert_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("accident_alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    hospital_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("vet_hospitals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    escalation_round: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False
    )
    secure_token: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="pending",
        nullable=False,
        index=True
    )  # 'pending', 'accepted', 'declined', 'expired'
    dispatched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )  # 5-minute timeout window
    responded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    decline_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    alert: Mapped["AccidentAlert"] = relationship("AccidentAlert", back_populates="dispatches")
    hospital = relationship("VetHospital", back_populates="dispatches")

    @property
    def is_expired(self) -> bool:
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > exp

    def __repr__(self) -> str:
        return f"<AlertDispatch(alert_id='{self.alert_id}', hospital_id='{self.hospital_id}', status='{self.status}')>"
