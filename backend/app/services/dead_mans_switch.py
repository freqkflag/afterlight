"""
Dead Man's Switch Engine

This is the core service that manages the check-in lifecycle:
1. ACTIVE → user checks in regularly
2. OVERDUE → missed check-in, sending reminders
3. ESCALATING → trusted contacts notified
4. RELEASED → full release protocol executed

The engine is designed to be extremely conservative. False positives
(releasing while the user is alive) are catastrophic.
"""

import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.dead_mans_switch import (
    CheckInEvent,
    CheckInMethod,
    DeadMansSwitch,
    ReleaseAction,
    ReleaseActionKind,
    ReleaseProtocol,
    SwitchStatus,
    TrustedContact,
)
from app.models.executor import AuditAction, AuditLog, Executor, GrantStatus
from app.models.legacy import DeliveryStatus, LegacyMessage
from app.models.user import User
from app.services.email import send_email

logger = logging.getLogger(__name__)


class DeadMansSwitchService:
    """Service for managing the dead man's switch lifecycle."""

    def __init__(self, db: Session):
        self.db = db

    def create_switch(
        self,
        user_id: str,
        check_in_interval_days: int | None = None,
        grace_period_days: int | None = None,
    ) -> DeadMansSwitch:
        """Create a new dead man's switch for a user."""
        interval = check_in_interval_days or settings.default_check_in_interval_days
        grace = grace_period_days or settings.default_grace_period_days

        # Clamp to valid range
        interval = max(settings.min_check_in_interval_days, min(interval, settings.max_check_in_interval_days))
        grace = max(1, min(grace, 90))

        now = datetime.now(timezone.utc)
        switch = DeadMansSwitch(
            user_id=user_id,
            status=SwitchStatus.ACTIVE,
            check_in_interval_days=interval,
            grace_period_days=grace,
            missed_checkins_before_escalation=2,
            last_check_in_at=now,
            next_check_in_due_at=now + timedelta(days=interval),
        )
        self.db.add(switch)
        self.db.flush()

        # Create default release protocol
        default_actions = [
            {"action": ReleaseActionKind.NOTIFY_EXECUTOR.value, "config": {}},
            {"action": ReleaseActionKind.RELEASE_VAULT.value, "config": {}},
            {"action": ReleaseActionKind.SEND_LEGACY_MESSAGES.value, "config": {}},
        ]
        protocol = ReleaseProtocol(
            switch_id=switch.id,
            actions=json.dumps(default_actions),
        )
        self.db.add(protocol)
        self.db.flush()

        return switch

    def record_check_in(
        self,
        switch_id: str,
        method: CheckInMethod = CheckInMethod.APP,
        source_info: str | None = None,
        is_manual: bool = True,
    ) -> DeadMansSwitch:
        """Record a check-in event and reset the switch to ACTIVE."""
        switch = self.db.query(DeadMansSwitch).filter_by(id=switch_id).first()
        if not switch:
            raise ValueError(f"Switch {switch_id} not found")

        now = datetime.now(timezone.utc)

        # Record the event
        event = CheckInEvent(
            switch_id=switch_id,
            method=method,
            source_info=source_info,
            is_manual=is_manual,
        )
        self.db.add(event)

        # Reset the switch
        switch.status = SwitchStatus.ACTIVE
        switch.last_check_in_at = now
        switch.next_check_in_due_at = now + timedelta(days=switch.check_in_interval_days)
        switch.overdue_since = None
        switch.escalated_at = None

        # Reset trusted contacts
        for contact in switch.trusted_contacts:
            contact.has_confirmed_alive = None
            contact.notified_of_death = False

        self.db.flush()

        # Audit log
        self._audit(switch.user_id, AuditAction.CHECK_IN, f"Check-in recorded via {method.value}")

        return switch

    def process_overdue_switches(self) -> list[DeadMansSwitch]:
        """
        Find all switches that are overdue and advance their state.
        Called by a scheduled job (e.g., every hour).

        Returns list of switches that changed state.
        """
        now = datetime.now(timezone.utc)
        changed = []

        # Find switches where next_check_in_due_at has passed
        overdue_switches = (
            self.db.query(DeadMansSwitch)
            .filter(
                DeadMansSwitch.status.in_([SwitchStatus.ACTIVE, SwitchStatus.OVERDUE, SwitchStatus.ESCALATING]),
                DeadMansSwitch.next_check_in_due_at < now,
            )
            .all()
        )

        for switch in overdue_switches:
            old_status = switch.status

            if switch.status == SwitchStatus.ACTIVE:
                # First missed check-in → OVERDUE
                switch.status = SwitchStatus.OVERDUE
                switch.overdue_since = now
                logger.info(f"Switch {switch.id} is now OVERDUE for user {switch.user_id}")

            elif switch.status == SwitchStatus.OVERDUE:
                # Check if we should escalate
                missed_count = self._count_missed_checkins(switch)
                if missed_count >= switch.missed_checkins_before_escalation:
                    switch.status = SwitchStatus.ESCALATING
                    switch.escalated_at = now
                    self._notify_trusted_contacts(switch)
                    logger.warning(
                        f"Switch {switch.id} is now ESCALATING for user {switch.user_id}"
                    )

            elif switch.status == SwitchStatus.ESCALATING:
                # Check if grace period has expired
                if switch.escalated_at and (now - switch.escalated_at) >= timedelta(days=switch.grace_period_days):
                    self._execute_release(switch)
                    switch.status = SwitchStatus.RELEASED
                    switch.released_at = now
                    logger.critical(
                        f"Switch {switch.id} RELEASED for user {switch.user_id}"
                    )

            if switch.status != old_status:
                changed.append(switch)

        self.db.commit()
        return changed

    def _count_missed_checkins(self, switch: DeadMansSwitch) -> int:
        """Count how many check-in intervals have been missed."""
        if not switch.overdue_since:
            return 0
        now = datetime.now(timezone.utc)
        delta = now - switch.overdue_since
        return int(delta.days / switch.check_in_interval_days)

    def _notify_trusted_contacts(self, switch: DeadMansSwitch):
        """Notify trusted contacts that the user may be deceased."""
        owner = self.db.query(User).filter_by(id=switch.user_id).first()
        owner_name = owner.full_name if owner else "an Afterlight user"
        for contact in switch.trusted_contacts:
            if not contact.notified_of_death:
                sent = send_email(
                    contact.email,
                    f"Afterlight check-in concern for {owner_name}",
                    (
                        f"Hello {contact.name},\n\n"
                        f"{owner_name} has missed check-ins on Afterlight. "
                        f"As a trusted contact, please try to reach them. "
                        f"If they are well, ask them to check in at {settings.app_url}.\n"
                    ),
                )
                if sent:
                    contact.notified_of_death = True
                else:
                    logger.warning(
                        "Queued notify for %s (%s) but SMTP did not send",
                        contact.name,
                        contact.email,
                    )
                    contact.notified_of_death = True

        self._audit(
            switch.user_id,
            AuditAction.TRUSTED_CONTACT_NOTIFIED,
            f"Trusted contacts notified for switch {switch.id}",
        )

    def _execute_release(self, switch: DeadMansSwitch):
        """Execute the release protocol."""
        protocol = switch.release_protocol
        if not protocol:
            logger.error(f"No release protocol for switch {switch.id}")
            return

        actions = json.loads(protocol.actions)
        for action_config in actions:
            action_kind = action_config.get("action")
            action = ReleaseAction(
                protocol_id=protocol.id,
                action_kind=ReleaseActionKind(action_kind),
                config=json.dumps(action_config.get("config", {})),
            )
            self.db.add(action)

            # Execute the action
            try:
                self._execute_action(switch, action)
                action.status = "done"
                action.executed_at = datetime.now(timezone.utc)
            except Exception as e:
                logger.error(f"Release action {action_kind} failed: {e}")
                action.status = "failed"
                action.result = str(e)

        protocol.executed = True
        protocol.executed_at = datetime.now(timezone.utc)

        self._audit(
            switch.user_id,
            AuditAction.RELEASE_TRIGGERED,
            f"Release protocol executed for switch {switch.id}",
        )

    def _execute_action(self, switch: DeadMansSwitch, action: ReleaseAction):
        """Execute a single release action."""
        owner = self.db.query(User).filter_by(id=switch.user_id).first()
        owner_name = owner.full_name if owner else "an Afterlight user"

        if action.action_kind == ReleaseActionKind.NOTIFY_EXECUTOR:
            executors = (
                self.db.query(Executor)
                .filter_by(user_id=switch.user_id)
                .filter(Executor.status.in_([GrantStatus.PENDING, GrantStatus.ACTIVE]))
                .all()
            )
            for executor in executors:
                send_email(
                    executor.executor_email,
                    f"Afterlight release for {owner_name}",
                    (
                        f"Hello {executor.executor_name},\n\n"
                        f"The dead man's switch for {owner_name} has released. "
                        f"Open the executor portal: {settings.app_url}/executor/portal\n"
                    ),
                )
            action.result = f"notified {len(executors)} executors"

        elif action.action_kind == ReleaseActionKind.RELEASE_VAULT:
            # Executors already see vault title hints via portal; ciphertext stays client-encrypted.
            action.result = "vault titles available to active executors"

        elif action.action_kind == ReleaseActionKind.SEND_LEGACY_MESSAGES:
            messages = (
                self.db.query(LegacyMessage)
                .filter_by(user_id=switch.user_id, status=DeliveryStatus.SCHEDULED)
                .all()
            )
            for message in messages:
                sent = send_email(
                    message.recipient_email,
                    message.subject,
                    (
                        f"Hello {message.recipient_name},\n\n"
                        f"You have a legacy message from {owner_name} on Afterlight. "
                        f"The content is encrypted; contact the executor for delivery "
                        f"instructions if needed.\n"
                    ),
                )
                if sent:
                    message.status = DeliveryStatus.DELIVERED
                    message.delivered_at = datetime.now(timezone.utc)
            action.result = f"processed {len(messages)} legacy messages"

        elif action.action_kind == ReleaseActionKind.DOWNLOAD_PACKAGE:
            action.result = "download package not implemented in alpha"

        elif action.action_kind == ReleaseActionKind.NOTIFY_FAMILY:
            action.result = "family notify not implemented in alpha"

        elif action.action_kind == ReleaseActionKind.CUSTOM:
            action.result = "custom action recorded"

    def _audit(self, user_id: str, action: AuditAction, description: str):
        """Create an audit log entry."""
        log = AuditLog(
            user_id=user_id,
            action=action,
            description=description,
        )
        self.db.add(log)

    def get_switch_status(self, switch_id: str) -> dict:
        """Get the current status of a switch (for dashboard display)."""
        switch = self.db.query(DeadMansSwitch).filter_by(id=switch_id).first()
        if not switch:
            raise ValueError(f"Switch {switch_id} not found")

        now = datetime.now(timezone.utc)
        return {
            "status": switch.status.value,
            "last_check_in_at": switch.last_check_in_at.isoformat() if switch.last_check_in_at else None,
            "next_check_in_due_at": switch.next_check_in_due_at.isoformat() if switch.next_check_in_due_at else None,
            "check_in_interval_days": switch.check_in_interval_days,
            "grace_period_days": switch.grace_period_days,
            "overdue_since": switch.overdue_since.isoformat() if switch.overdue_since else None,
            "escalated_at": switch.escalated_at.isoformat() if switch.escalated_at else None,
            "released_at": switch.released_at.isoformat() if switch.released_at else None,
            "trusted_contacts": [
                {
                    "name": c.name,
                    "email": c.email,
                    "relationship": c.relationship,
                    "has_confirmed_alive": c.has_confirmed_alive,
                    "notified_of_death": c.notified_of_death,
                }
                for c in switch.trusted_contacts
            ],
        }
