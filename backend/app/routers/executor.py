"""Executor router — manage executor access and dashboard."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.executor import AccessLevel, AuditAction, Executor, GrantStatus
from app.core.security import get_current_user
from app.services.audit import AuditService

router = APIRouter(prefix="/executor", tags=["executor"])


class ExecutorCreate(BaseModel):
    executor_email: str
    executor_name: str
    relationship: str
    phone: str | None = None
    access_level: AccessLevel = AccessLevel.FULL
    access_expires_at: str | None = None


class ExecutorUpdate(BaseModel):
    access_level: AccessLevel | None = None
    status: GrantStatus | None = None


class ExecutorResponse(BaseModel):
    id: str
    executor_email: str
    executor_name: str
    relationship: str
    phone: str | None
    access_level: str
    status: str
    accepted_at: str | None
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=list[ExecutorResponse])
def list_executors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all executors for the current user."""
    return (
        db.query(Executor)
        .filter_by(user_id=current_user.id)
        .order_by(Executor.created_at.desc())
        .all()
    )


@router.post("", response_model=ExecutorResponse, status_code=status.HTTP_201_CREATED)
def create_executor(
    req: ExecutorCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new executor."""
    executor = Executor(
        user_id=current_user.id,
        executor_email=req.executor_email,
        executor_name=req.executor_name,
        relationship=req.relationship,
        phone=req.phone,
        access_level=req.access_level,
        status=GrantStatus.PENDING,
    )
    db.add(executor)
    db.commit()
    db.refresh(executor)

    # Audit log
    audit = AuditService(db)
    audit.log(
        user_id=current_user.id,
        action=AuditAction.EXECUTOR_ADDED,
        description=f"Added executor {req.executor_name} ({req.executor_email})",
    )
    db.commit()

    return executor


@router.get("/{executor_id}", response_model=ExecutorResponse)
def get_executor(
    executor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific executor."""
    executor = db.query(Executor).filter_by(id=executor_id, user_id=current_user.id).first()
    if not executor:
        raise HTTPException(status_code=404, detail="Executor not found")
    return executor


@router.patch("/{executor_id}", response_model=ExecutorResponse)
def update_executor(
    executor_id: str,
    req: ExecutorUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an executor."""
    executor = db.query(Executor).filter_by(id=executor_id, user_id=current_user.id).first()
    if not executor:
        raise HTTPException(status_code=404, detail="Executor not found")

    if req.access_level is not None:
        executor.access_level = req.access_level
    if req.status is not None:
        executor.status = req.status

    db.commit()
    db.refresh(executor)
    return executor


@router.delete("/{executor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_executor(
    executor_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove an executor."""
    executor = db.query(Executor).filter_by(id=executor_id, user_id=current_user.id).first()
    if not executor:
        raise HTTPException(status_code=404, detail="Executor not found")

    db.delete(executor)
    db.commit()


@router.get("/dashboard/summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a summary for the executor dashboard."""
    from app.models.asset import Asset
    from app.models.vault import VaultItem
    from app.models.legacy import LegacyMessage

    assets = db.query(Asset).filter_by(user_id=current_user.id).all()
    vault_items = db.query(VaultItem).filter_by(user_id=current_user.id).all()
    messages = db.query(LegacyMessage).filter_by(user_id=current_user.id).all()

    total_value = sum(a.estimated_value_cents or 0 for a in assets)

    return {
        "total_assets": len(assets),
        "total_vault_items": len(vault_items),
        "total_legacy_messages": len(messages),
        "total_estimated_value_cents": total_value,
        "assets_by_kind": _group_by_kind(assets),
        "recent_activity": _get_recent_activity(db, current_user.id),
    }


def _group_by_kind(assets: list[Asset]) -> dict[str, int]:
    """Group assets by kind."""
    result: dict[str, int] = {}
    for asset in assets:
        result[asset.kind.value] = result.get(asset.kind.value, 0) + 1
    return result


def _get_recent_activity(db: Session, user_id: str, limit: int = 10) -> list[dict]:
    """Get recent audit log entries."""
    from app.models.executor import AuditLog

    logs = (
        db.query(AuditLog)
        .filter_by(user_id=user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "action": log.action.value,
            "description": log.description,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
