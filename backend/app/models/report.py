"""
CrueltyReport and ReportMedia models for reporting illegal wildlife/domestic animal cruelty.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import (
    String, Boolean, Float, Integer, DateTime, ForeignKey, Text, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin


class CrueltyReport(Base, TimestampMixin):
    __tablename__ = "cruelty_reports"

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
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    category: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )  # 'cruelty', 'illegal_trade', 'abandonment', 'illegal_breeding', 'other'
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False
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
    nearest_police_station_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    nearest_police_station_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    nearest_police_station_phone: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True
    )
    complaint_pdf_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="pending_review",
        nullable=False,
        index=True
    )  # 'pending_review', 'verified', 'dismissed', 'action_taken', 'fake'
    admin_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    reviewed_by_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
    media: Mapped[List["ReportMedia"]] = relationship(
        "ReportMedia",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ReportMedia.created_at.asc()"
    )

    def __repr__(self) -> str:
        return f"<CrueltyReport(id='{self.id}', category='{self.category}', status='{self.status}')>"


class ReportMedia(Base):
    __tablename__ = "report_media"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    report_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("cruelty_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    media_type: Mapped[str] = mapped_column(
        String(16),
        default="image",
        nullable=False
    )  # 'image' or 'video'
    storage_key: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    mime_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )
    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    virus_scan_status: Mapped[str] = mapped_column(
        String(32),
        default="clean",
        nullable=False
    )  # 'pending', 'clean', 'infected'
    exif_stripped: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )
    public_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    report: Mapped["CrueltyReport"] = relationship("CrueltyReport", back_populates="media")

    def __repr__(self) -> str:
        return f"<ReportMedia(id='{self.id}', report_id='{self.report_id}', type='{self.media_type}')>"
