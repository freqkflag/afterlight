"""Executor router — manage executor access and portal."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.config import settings
from app.core.responses import CoercedStr, OptionalCoercedStr
from app.core.security import get_current_user
from app.database import get_db
from app.models.asset import Asset
from app.models.dead_mans_switch import DeadMansSwitch
from app.models.executor import AccessLevel, AuditAction, AuditLog, Executor, GrantStatus
from app.models.legacy import LegacyMessage
from app.models.user import User
from app.models.vault import VaultItem
from app.services.audit import AuditService
from app.services.email import send_email

router = APIRouter(prefix="/executor", tags=["executor"])


class ExecutorCreate(BaseModel):
    executor_email: EmailStr
    executor_name: str
    relationship: str
    phone: str | None = None
    access_level: AccessLevel = AccessLevel.FULL


class ExecutorUpdate(BaseModel):
    access_level: AccessLevel | None = None
    status: GrantStatus | None = None


class ExecutorResponse(BaseModel):
    id: CoercedStr
    executor_email: str
    executor_name: str
    relationship: str
    phone: str | None
    access_level: str
    status: str
    accepted_at: OptionalCoercedStr
    created_at: CoercedStr

    class Config:
        from_attributes = True


class AcceptInviteRequest(BaseModel):
    executor_id: str | None = None


@router.get("/dashboard/summary")
def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Owner dashboard summary (estate at a glance)."""
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


@router.get("/portal/estates")
def list_portal_estates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Estates where the current user is an invited/active executor."""
    grants = (
        db.query(Executor)
        .filter(Executor.executor_email == current_user.email)
        .filter(Executor.status.in_([GrantStatus.PENDING, GrantStatus.ACTIVE]))
        .all()
    )
    results = []
    for grant in grants:
        owner = db.query(User).filter_by(id=grant.user_id).first()
        if not owner:
            continue
        switch = db.query(DeadMansSwitch).filter_by(user_id=owner.id).first()
        results.append(
            {
                "executor_id": str(grant.id),
                "grantor_user_id": str(owner.id),
                "grantor_name": owner.full_name,
                "grantor_email": owner.email,
                "access_level": grant.access_level.value,
                "status": grant.status.value,
                "total_assets": db.query(Asset).filter_by(user_id=owner.id).count(),
                "total_vault_items": db.query(VaultItem).filter_by(user_id=owner.id).count(),
                "total_legacy_messages": db.query(LegacyMessage)
                .filter_by(user_id=owner.id)
                .count(),
                "switch_status": switch.status.value if switch else None,
            }
        )
    return results


@router.post("/portal/accept")
def accept_portal_invite(
    req: AcceptInviteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept a pending executor invitation for the current user's email."""
    query = db.query(Executor).filter(
        Executor.executor_email == current_user.email,
        Executor.status == GrantStatus.PENDING,
    )
    if req.executor_id:
        query = query.filter(Executor.id == req.executor_id)
    grant = query.first()
    if not grant:
        raise HTTPException(status_code=404, detail="No pending invitation found")

    grant.status = GrantStatus.ACTIVE
    grant.accepted_at = datetime.now(timezone.utc)
    grant.executor_user_id = current_user.id
    db.commit()

    audit = AuditService(db)
    audit.log(
        user_id=grant.user_id,
        action=AuditAction.EXECUTOR_ACCEPTED,
        description=f"Executor {current_user.email} accepted invitation",
    )
    db.commit()
    return {"status": "active", "executor_id": str(grant.id)}


@router.get("/portal/estates/{grantor_user_id}")
def get_portal_estate(
    grantor_user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Executor-facing estate checklist for a grantor."""
    grant = (
        db.query(Executor)
        .filter_by(user_id=grantor_user_id, executor_email=current_user.email)
        .first()
    )
    if not grant or grant.status not in (GrantStatus.ACTIVE, GrantStatus.PENDING):
        raise HTTPException(status_code=403, detail="No access to this estate")
    if grant.status == GrantStatus.PENDING:
        raise HTTPException(status_code=403, detail="Accept the invitation first")

    owner = db.query(User).filter_by(id=grantor_user_id).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Grantor not found")

    switch = db.query(DeadMansSwitch).filter_by(user_id=owner.id).first()
    assets = db.query(Asset).filter_by(user_id=owner.id).all()
    vault_items = db.query(VaultItem).filter_by(user_id=owner.id).all()
    messages = db.query(LegacyMessage).filter_by(user_id=owner.id).all()
    contacts = switch.trusted_contacts if switch else []

    released = bool(switch and switch.status.value == "released")
    checklist = [
        {
            "step": 1,
            "title": "Confirm you are the appointed executor",
            "detail": f"Access level: {grant.access_level.value}",
            "done": grant.status == GrantStatus.ACTIVE,
        },
        {
            "step": 2,
            "title": "Review digital inventory",
            "detail": f"{len(assets)} assets catalogued",
            "done": len(assets) > 0,
        },
        {
            "step": 3,
            "title": "Locate vault item titles",
            "detail": (
                f"{len(vault_items)} encrypted items (ciphertext only until release keys are shared)"
                if not released
                else f"{len(vault_items)} vault items available for title review"
            ),
            "done": len(vault_items) > 0,
        },
        {
            "step": 4,
            "title": "Deliver legacy messages",
            "detail": f"{len(messages)} messages scheduled",
            "done": len(messages) > 0,
        },
        {
            "step": 5,
            "title": "Contact trusted people",
            "detail": f"{len(contacts)} trusted contacts on file",
            "done": len(contacts) > 0,
        },
    ]

    return {
        "grantor_name": owner.full_name,
        "grantor_email": owner.email,
        "access_level": grant.access_level.value,
        "switch_status": switch.status.value if switch else None,
        "checklist": checklist,
        "assets": [
            {"id": str(a.id), "kind": a.kind.value, "name": a.name, "status": a.status.value}
            for a in assets
        ],
        "vault_items": [
            {"id": str(v.id), "kind": v.kind.value, "title_hint": v.title_hint}
            for v in vault_items
        ],
        "legacy_messages": [
            {
                "id": str(m.id),
                "recipient_name": m.recipient_name,
                "subject": m.subject,
                "status": m.status.value,
            }
            for m in messages
        ],
        "trusted_contacts": [
            {"name": c.name, "email": c.email, "relationship": c.relationship}
            for c in contacts
        ],
    }


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
    """Add a new executor and email an invite when SMTP is configured."""
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

    audit = AuditService(db)
    audit.log(
        user_id=current_user.id,
        action=AuditAction.EXECUTOR_ADDED,
        description=f"Added executor {req.executor_name} ({req.executor_email})",
    )
    db.commit()

    send_email(
        req.executor_email,
        f"You were named an executor on {settings.app_name}",
        (
            f"Hello {req.executor_name},\n\n"
            f"{current_user.full_name} named you as an executor on Afterlight.\n"
            f"Create or sign in at {settings.app_url}/executor/portal and accept the invite.\n"
        ),
    )

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


def _group_by_kind(assets: list[Asset]) -> dict[str, int]:
    result: dict[str, int] = {}
    for asset in assets:
        result[asset.kind.value] = result.get(asset.kind.value, 0) + 1
    return result


def _get_recent_activity(db: Session, user_id: str, limit: int = 10) -> list[dict]:
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
