"""Executor and audit models — the executor dashboard and access control."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AccessLevel(str, enum.Enum):
    FULL = "full"           # Full access to vault and assets
    LIMITED = "limited"     # Only specific assets/messages
    MESSAGES_ONLY = "messages_only"  # Only legacy messages
    VIEW_ONLY = "view_only" # Can see inventory but not credentials


class GrantStatus(str, enum.Enum):
    PENDING = "pending"     # Invitation sent, not yet accepted
    ACTIVE = "active"       # Access granted
    REVOKED = "revoked"     # Access revoked
    EXPIRED = "expired"     # Time-limited access expired


class Executor(Base):
    """An executor or trusted person who can access the estate."""

    __tablename__ = "executors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # The executor (may or may not be an Afterlight user)
    executor_email: Mapped[str] = mapped_column(String(255), nullable=False)
    executor_name: Mapped[str] = mapped_column(String(255), nullable=False)
    executor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    relationship: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Access configuration
    access_level: Mapped[AccessLevel] = mapped_column(Enum(AccessLevel), default=AccessLevel.FULL, nullable=False)
    status: Mapped[GrantStatus] = mapped_column(Enum(GrantStatus), default=GrantStatus.PENDING, nullable=False)
    # Time-limited access (optional)
    access_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Whether the executor has accepted/activated
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Encrypted access key (encrypted to the executor's public key)
    encrypted_access_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="executor_grants", foreign_keys=[user_id])
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="executor", cascade="all, delete-orphan"
    )


class ExecutorAccessGrant(Base):
    """Links users to executors with specific permissions."""

    __tablename__ = "executor_access_grants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    executor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("executors.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # What the executor can access
    vault_item_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of UUIDs, null = all
    asset_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array of UUIDs, null = all
    legacy_message_ids: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="executor_grants")


class AuditAction(str, enum.Enum):
    CHECK_IN = "check_in"
    CHECK_IN_MISSED = "check_in_missed"
    ESCALATION_STARTED = "escalation_started"
    TRUSTED_CONTACT_NOTIFIED = "trusted_contact_notified"
    RELEASE_TRIGGERED = "release_triggered"
    VAULT_ACCESSED = "vault_accessed"
    ASSET_ACCESSED = "asset_accessed"
    LEGACY_MESSAGE_DELIVERED = "legacy_message_delivered"
    EXECUTOR_ADDED = "executor_added"
    EXECUTOR_ACCEPTED = "executor_accepted"
    EXECUTOR_REVOKED = "executor_revoked"
    SETTINGS_CHANGED = "settings_changed"
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    PASSWORD_CHANGED = "password_changed"
    VAULT_ITEM_CREATED = "vault_item_created"
    VAULT_ITEM_ACCESSED = "vault_item_accessed"
    VAULT_ITEM_DELETED = "vault_item_deleted"
    ASSET_CREATED = "asset_created"
    ASSET_UPDATED = "asset_updated"
    ASSET_DELETED = "asset_deleted"


class AuditLog(Base):
    """Immutable audit trail for all sensitive operations."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    executor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("executors.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False, index=True)
    # Human-readable description
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # IP address, user agent, etc.
    source_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Additional structured data (JSON)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="audit_logs")
    executor: Mapped["Executor | None"] = relationship(back_populates="audit_logs")
