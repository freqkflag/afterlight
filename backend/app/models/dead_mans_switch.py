"""Dead Man's Switch models — the heart of Afterlight.

The dead man's switch is a check-in system with an escalation cascade:
1. User checks in periodically (default: every 30 days)
2. If they miss a check-in, reminders are sent
3. If still no response, trusted contacts are notified
4. If the full grace period expires, the release protocol executes

This is designed to be extremely conservative — false positives are catastrophic.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship as orm_relationship

from app.database import Base


class SwitchStatus(str, enum.Enum):
    ACTIVE = "active"           # Normal operation, user checking in
    OVERDUE = "overdue"         # Missed a check-in, sending reminders
    ESCALATING = "escalating"   # Trusted contacts being notified
    RELEASED = "released"       # Full release protocol executed
    PAUSED = "paused"           # User paused (e.g., long trip with no access)
    CANCELLED = "cancelled"     # User cancelled the switch


class CheckInMethod(str, enum.Enum):
    EMAIL = "email"
    SMS = "sms"
    APP = "app"
    TRUSTED_CONTACT = "trusted_contact"


class ReleaseActionKind(str, enum.Enum):
    NOTIFY_EXECUTOR = "notify_executor"
    RELEASE_VAULT = "release_vault"
    SEND_LEGACY_MESSAGES = "send_legacy_messages"
    DOWNLOAD_PACKAGE = "download_package"  # Full encrypted package for executor
    NOTIFY_FAMILY = "notify_family"
    CUSTOM = "custom"


class DeadMansSwitch(Base):
    """Configuration for a user's dead man's switch."""

    __tablename__ = "dead_mans_switches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    status: Mapped[SwitchStatus] = mapped_column(Enum(SwitchStatus), default=SwitchStatus.ACTIVE, nullable=False)

    # Check-in configuration
    check_in_interval_days: Mapped[int] = mapped_column(default=30, nullable=False)
    # How many missed check-ins before escalation begins
    missed_checkins_before_escalation: Mapped[int] = mapped_column(default=2, nullable=False)
    # Total days from first missed check-in to full release
    grace_period_days: Mapped[int] = mapped_column(default=14, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    last_check_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_check_in_due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # When the current overdue period started (for escalation tracking)
    overdue_since: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # When trusted contacts were first notified
    escalated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # When the release protocol was executed
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = orm_relationship(back_populates="dead_mans_switch")
    check_in_events: Mapped[list["CheckInEvent"]] = orm_relationship(
        back_populates="switch", cascade="all, delete-orphan", order_by="CheckInEvent.created_at.desc()"
    )
    release_protocol: Mapped["ReleaseProtocol | None"] = orm_relationship(
        back_populates="switch", uselist=False, cascade="all, delete-orphan"
    )
    trusted_contacts: Mapped[list["TrustedContact"]] = orm_relationship(
        back_populates="switch", cascade="all, delete-orphan"
    )


class CheckInEvent(Base):
    """A single check-in event (proof of life)."""

    __tablename__ = "check_in_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    switch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dead_mans_switches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    method: Mapped[CheckInMethod] = mapped_column(Enum(CheckInMethod), nullable=False)
    # IP address or device info (for audit)
    source_info: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Whether this was a manual or automatic check-in
    is_manual: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    switch: Mapped["DeadMansSwitch"] = orm_relationship(back_populates="check_in_events")


class ReleaseProtocol(Base):
    """The ordered set of actions to execute when the switch triggers."""

    __tablename__ = "release_protocols"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    switch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dead_mans_switches.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    # JSON array of { "action": "...", "config": {...} }
    actions: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    # Whether the protocol has been executed
    executed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    switch: Mapped["DeadMansSwitch"] = orm_relationship(back_populates="release_protocol")


class ReleaseAction(Base):
    """Individual actions within a release protocol (for audit trail)."""

    __tablename__ = "release_actions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    protocol_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("release_protocols.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_kind: Mapped[ReleaseActionKind] = mapped_column(Enum(ReleaseActionKind), nullable=False)
    # Configuration for this action (JSON)
    config: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Execution status
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)  # pending, done, failed
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    result: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class TrustedContact(Base):
    """A person who can confirm the user is alive (or not)."""

    __tablename__ = "trusted_contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    switch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("dead_mans_switches.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    relationship: Mapped[str] = mapped_column(String(100), nullable=False)  # spouse, sibling, friend, lawyer
    # Priority order for escalation (1 = first to contact)
    priority: Mapped[int] = mapped_column(default=1, nullable=False)
    # Whether this contact has confirmed the user is alive
    has_confirmed_alive: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Whether this contact has been notified of a potential death
    notified_of_death: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    switch: Mapped["DeadMansSwitch"] = orm_relationship(back_populates="trusted_contacts")
