"""Dead Man's Switch router — check-in, status, and configuration."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.dead_mans_switch import CheckInMethod, SwitchStatus
from app.core.security import get_current_user
from app.services.dead_mans_switch import DeadMansSwitchService

router = APIRouter(prefix="/dead-mans-switch", tags=["dead-mans-switch"])


class CheckInRequest(BaseModel):
    method: CheckInMethod = CheckInMethod.APP


class UpdateSwitchConfig(BaseModel):
    check_in_interval_days: int | None = None
    grace_period_days: int | None = None
    missed_checkins_before_escalation: int | None = None


class TrustedContactCreate(BaseModel):
    name: str
    email: str
    phone: str | None = None
    relationship: str
    priority: int = 1


@router.post("/check-in")
def check_in(
    req: CheckInRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record a check-in (proof of life)."""
    service = DeadMansSwitchService(db)

    # Get or create switch
    switch = current_user.dead_mans_switch
    if not switch:
        switch = service.create_switch(str(current_user.id))
        db.commit()

    switch = service.record_check_in(
        str(switch.id),
        method=req.method,
    )
    db.commit()

    return {"status": "ok", "next_check_in_due_at": switch.next_check_in_due_at}


@router.get("/status")
def get_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current dead man's switch status."""
    service = DeadMansSwitchService(db)

    switch = current_user.dead_mans_switch
    if not switch:
        return {"status": "not_configured"}

    return service.get_switch_status(str(switch.id))


@router.post("/configure")
def configure_switch(
    req: UpdateSwitchConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update dead man's switch configuration."""
    switch = current_user.dead_mans_switch
    if not switch:
        raise HTTPException(status_code=404, detail="Switch not configured")

    if req.check_in_interval_days is not None:
        switch.check_in_interval_days = req.check_in_interval_days
    if req.grace_period_days is not None:
        switch.grace_period_days = req.grace_period_days
    if req.missed_checkins_before_escalation is not None:
        switch.missed_checkins_before_escalation = req.missed_checkins_before_escalation

    db.commit()
    return {"status": "ok"}


@router.post("/pause")
def pause_switch(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Pause the switch (e.g., for extended travel)."""
    switch = current_user.dead_mans_switch
    if not switch:
        raise HTTPException(status_code=404, detail="Switch not configured")

    switch.status = SwitchStatus.PAUSED
    db.commit()
    return {"status": "paused"}


@router.post("/resume")
def resume_switch(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Resume a paused switch."""
    switch = current_user.dead_mans_switch
    if not switch:
        raise HTTPException(status_code=404, detail="Switch not configured")

    switch.status = SwitchStatus.ACTIVE
    db.commit()
    return {"status": "active"}


@router.post("/trusted-contacts", status_code=status.HTTP_201_CREATED)
def add_trusted_contact(
    req: TrustedContactCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a trusted contact."""
    from app.models.dead_mans_switch import TrustedContact

    switch = current_user.dead_mans_switch
    if not switch:
        raise HTTPException(status_code=404, detail="Switch not configured")

    contact = TrustedContact(
        switch_id=switch.id,
        name=req.name,
        email=req.email,
        phone=req.phone,
        relationship=req.relationship,
        priority=req.priority,
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return {"id": str(contact.id), "status": "created"}


@router.get("/trusted-contacts")
def list_trusted_contacts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List trusted contacts."""
    switch = current_user.dead_mans_switch
    if not switch:
        return []

    return [
        {
            "id": str(c.id),
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "relationship": c.relationship,
            "priority": c.priority,
            "has_confirmed_alive": c.has_confirmed_alive,
            "notified_of_death": c.notified_of_death,
        }
        for c in switch.trusted_contacts
    ]
