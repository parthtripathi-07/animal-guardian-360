"""
VetHospital model for veterinary clinics and emergency animal centers.
"""
import uuid
from typing import Optional, List
from sqlalchemy import (
    String, Boolean, Float, Integer, ForeignKey, Text, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin


class VetHospital(Base, TimestampMixin):
    __tablename__ = "vet_hospitals"

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
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True
    )
    place_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True
    )
    phone: Mapped[str] = mapped_column(
        String(32),
        nullable=False
    )
    emergency_phone: Mapped[Optional[str]] = mapped_column(
        String(32),
        nullable=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True
    )
    address: Mapped[str] = mapped_column(
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
    is_24x7: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True
    )
    ambulance_available: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    rating: Mapped[float] = mapped_column(
        Float,
        default=4.5,
        nullable=False
    )
    total_ratings: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )
    operating_hours: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    dispatches = relationship("AlertDispatch", back_populates="hospital", cascade="all, delete-orphan")
    accepted_accidents = relationship("AccidentAlert", back_populates="accepted_hospital")

    def __repr__(self) -> str:
        return f"<VetHospital(id='{self.id}', name='{self.name}', rating={self.rating})>"
