"""Asset model — discovered or manually added digital accounts and assets."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AssetKind(str, enum.Enum):
    EMAIL = "email"
    BANKING = "banking"
    INVESTMENT = "investment"
    CRYPTO = "crypto"
    SUBSCRIPTION = "subscription"
    SOCIAL_MEDIA = "social_media"
    CLOUD_STORAGE = "cloud_storage"
    DOMAIN = "domain"
    E_COMMERCE = "e_commerce"
    UTILITY = "utility"
    INSURANCE = "insurance"
    MEDICAL = "medical"
    LEGAL = "legal"
    OTHER = "other"


class AssetStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TRANSFERRED = "transferred"
    CLOSED = "closed"
    DECEASED = "deceased"  # marked after death confirmed


class Asset(Base):
    """A digital account or asset in the user's inventory."""

    __tablename__ = "assets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[AssetKind] = mapped_column(Enum(AssetKind), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # URL or identifier (e.g., "chase.com", "Coinbase")
    identifier: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Estimated value in USD (user-provided)
    estimated_value_cents: Mapped[int | None] = mapped_column(nullable=True)
    status: Mapped[AssetStatus] = mapped_column(Enum(AssetStatus), default=AssetStatus.ACTIVE, nullable=False)
    # Discovery source: manual, email_scan, browser_import, etc.
    discovery_source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)
    # Notes (encrypted client-side if sensitive)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Whether this asset has a corresponding vault item with credentials
    has_credentials: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="assets")
    vault_items: Mapped[list["VaultItem"]] = relationship(back_populates="asset")
