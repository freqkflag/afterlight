"""LegacyMessage model — scheduled messages delivered after death or at milestones."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DeliveryTrigger(str, enum.Enum):
    AFTER_DEATH = "after_death"
    SPECIFIC_DATE = "specific_date"
    MILESTONE = "birthday"  # e.g., child's 18th birthday
    ANNIVERSARY = "anniversary"


class DeliveryStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    PENDING_RELEASE = "pending_release"  # waiting for dead man's switch to trigger


class LegacyMessage(Base):
    """A message to be delivered to a beneficiary at a future trigger."""

    __tablename__ = "legacy_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The beneficiary (may be a user or just an email)
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Encrypted message content (client-side encryption)
    encrypted_content: Mapped[str] = mapped_column(Text, nullable=False)
    nonce: Mapped[str] = mapped_column(String(255), nullable=False)
    # Subject line (not encrypted — used for email subject)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    # Delivery configuration
    trigger: Mapped[DeliveryTrigger] = mapped_column(Enum(DeliveryTrigger), nullable=False)
    trigger_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # For milestone triggers: whose birthday, what age
    milestone_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    milestone_age: Mapped[int | None] = mapped_column(nullable=True)
    # Status
    status: Mapped[DeliveryStatus] = mapped_column(
        Enum(DeliveryStatus), default=DeliveryStatus.SCHEDULED, nullable=False
    )
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="legacy_messages")
