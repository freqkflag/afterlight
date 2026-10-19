"""Audit logging service."""

from sqlalchemy.orm import Session

from app.models.executor import AuditAction, AuditLog


class AuditService:
    """Service for creating and querying audit logs."""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        user_id: str,
        action: AuditAction,
        description: str,
        executor_id: str | None = None,
        source_info: str | None = None,
        metadata: dict | None = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        log = AuditLog(
            user_id=user_id,
            executor_id=executor_id,
            action=action,
            description=description,
            source_info=source_info,
            metadata_json=str(metadata) if metadata else None,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def get_user_logs(self, user_id: str, limit: int = 100) -> list[AuditLog]:
        """Get recent audit logs for a user."""
        return (
            self.db.query(AuditLog)
            .filter_by(user_id=user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
