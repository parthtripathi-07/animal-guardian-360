"""
Pet, LostFoundPost, PetEmbedding, and Match models for AI-driven lost pet recovery.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import (
    String, Boolean, Float, Integer, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base, TimestampMixin


class Pet(Base, TimestampMixin):
    __tablename__ = "pets"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False
    )
    species: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )  # 'dog', 'cat', 'bird', 'other'
    breed: Mapped[Optional[str]] = mapped_column(
        String(120),
        nullable=True
    )
    primary_color: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )
    secondary_color: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )
    gender: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True
    )
    microchip_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True
    )
    photo_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    posts: Mapped[List["LostFoundPost"]] = relationship("LostFoundPost", back_populates="pet")

    def __repr__(self) -> str:
        return f"<Pet(id='{self.id}', name='{self.name}', species='{self.species}')>"


class LostFoundPost(Base, TimestampMixin):
    __tablename__ = "lost_found_posts"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    pet_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("pets.id", ondelete="SET NULL"),
        nullable=True
    )
    post_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        index=True
    )  # 'lost', 'found', 'sighting'
    species: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True
    )
    breed: Mapped[Optional[str]] = mapped_column(
        String(120),
        nullable=True
    )
    primary_color: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )
    secondary_color: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )
    gender: Mapped[Optional[str]] = mapped_column(
        String(16),
        nullable=True
    )
    distinctive_marks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    collar_info: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )
    incident_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
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
    photo_urls: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="active",
        nullable=False,
        index=True
    )  # 'active', 'reunited', 'closed'
    masked_contact_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    pet = relationship("Pet", back_populates="posts")
    embeddings: Mapped[List["PetEmbedding"]] = relationship(
        "PetEmbedding",
        back_populates="post",
        cascade="all, delete-orphan"
    )
    matches_as_lost: Mapped[List["Match"]] = relationship(
        "Match",
        foreign_keys="[Match.lost_post_id]",
        back_populates="lost_post",
        cascade="all, delete-orphan"
    )
    matches_as_found: Mapped[List["Match"]] = relationship(
        "Match",
        foreign_keys="[Match.found_post_id]",
        back_populates="found_post",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<LostFoundPost(id='{self.id}', type='{self.post_type}', status='{self.status}')>"


class PetEmbedding(Base):
    __tablename__ = "pet_embeddings"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    post_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("lost_found_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    image_url: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    # Stored as JSON list of 512 normalized float values for portability across SQLite and PostgreSQL
    vector_data: Mapped[List[float]] = mapped_column(
        JSON,
        nullable=False
    )
    model_name: Mapped[str] = mapped_column(
        String(64),
        default="open_clip:ViT-B-32",
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    post: Mapped["LostFoundPost"] = relationship("LostFoundPost", back_populates="embeddings")

    def __repr__(self) -> str:
        return f"<PetEmbedding(post_id='{self.post_id}', model='{self.model_name}')>"


class Match(Base):
    __tablename__ = "pet_matches"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    lost_post_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("lost_found_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    found_post_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("lost_found_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    similarity_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True
    )  # Cosine similarity 0.0 - 1.0
    distance_meters: Mapped[float] = mapped_column(
        Float,
        nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32),
        default="potential",
        nullable=False,
        index=True
    )  # 'potential', 'confirmed_reunited', 'dismissed'
    owner_notified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    notified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    # Relationships
    lost_post: Mapped["LostFoundPost"] = relationship(
        "LostFoundPost",
        foreign_keys=[lost_post_id],
        back_populates="matches_as_lost"
    )
    found_post: Mapped["LostFoundPost"] = relationship(
        "LostFoundPost",
        foreign_keys=[found_post_id],
        back_populates="matches_as_found"
    )

    def __repr__(self) -> str:
        return f"<Match(lost='{self.lost_post_id}', found='{self.found_post_id}', score={self.similarity_score:.3f})>"
