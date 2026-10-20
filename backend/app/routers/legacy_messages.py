"""Legacy Messages router — create and manage scheduled messages."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.responses import CoercedStr
from app.core.security import get_current_user
from app.database import get_db
from app.models.legacy import DeliveryStatus, DeliveryTrigger, LegacyMessage
from app.models.user import User

router = APIRouter(prefix="/legacy-messages", tags=["legacy-messages"])


class LegacyMessageCreate(BaseModel):
    recipient_email: str
    recipient_name: str
    subject: str
    encrypted_content: str
    nonce: str
    trigger: DeliveryTrigger
    trigger_date: datetime | None = None
    milestone_person: str | None = None
    milestone_age: int | None = None


class LegacyMessageUpdate(BaseModel):
    subject: str | None = None
    encrypted_content: str | None = None
    nonce: str | None = None
    trigger: DeliveryTrigger | None = None
    trigger_date: datetime | None = None


class LegacyMessageResponse(BaseModel):
    id: CoercedStr
    recipient_email: str
    recipient_name: str
    subject: str
    trigger: str
    trigger_date: datetime | None
    status: str
    delivered_at: datetime | None
    created_at: CoercedStr

    class Config:
        from_attributes = True


@router.get("", response_model=list[LegacyMessageResponse])
def list_messages(
    status: DeliveryStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all legacy messages for the current user."""
    query = db.query(LegacyMessage).filter_by(user_id=current_user.id)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(LegacyMessage.created_at.desc()).all()


@router.post("", response_model=LegacyMessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    req: LegacyMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new legacy message."""
    message = LegacyMessage(
        user_id=current_user.id,
        recipient_email=req.recipient_email,
        recipient_name=req.recipient_name,
        subject=req.subject,
        encrypted_content=req.encrypted_content,
        nonce=req.nonce,
        trigger=req.trigger,
        trigger_date=req.trigger_date,
        milestone_person=req.milestone_person,
        milestone_age=req.milestone_age,
        status=DeliveryStatus.SCHEDULED,
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("/{message_id}", response_model=LegacyMessageResponse)
def get_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific legacy message."""
    message = db.query(LegacyMessage).filter_by(id=message_id, user_id=current_user.id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.patch("/{message_id}", response_model=LegacyMessageResponse)
def update_message(
    message_id: str,
    req: LegacyMessageUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a legacy message."""
    message = db.query(LegacyMessage).filter_by(id=message_id, user_id=current_user.id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(message, field, value)

    db.commit()
    db.refresh(message)
    return message


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a legacy message."""
    message = db.query(LegacyMessage).filter_by(id=message_id, user_id=current_user.id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()
