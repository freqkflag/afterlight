"""Vault router — CRUD for encrypted vault items."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.responses import CoercedStr, OptionalCoercedStr
from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.vault import VaultItem, VaultItemKind

router = APIRouter(prefix="/vault", tags=["vault"])


class VaultItemCreate(BaseModel):
    kind: VaultItemKind
    title_hint: str
    encrypted_data: str
    nonce: str
    asset_id: str | None = None


class VaultItemUpdate(BaseModel):
    title_hint: str | None = None
    encrypted_data: str | None = None
    nonce: str | None = None
    asset_id: str | None = None


class VaultItemResponse(BaseModel):
    id: CoercedStr
    kind: str
    title_hint: str
    encrypted_data: str
    nonce: str
    encryption_version: int
    asset_id: OptionalCoercedStr
    created_at: CoercedStr
    updated_at: CoercedStr

    class Config:
        from_attributes = True


@router.get("", response_model=list[VaultItemResponse])
def list_vault_items(
    kind: VaultItemKind | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all vault items for the current user."""
    query = db.query(VaultItem).filter_by(user_id=current_user.id)
    if kind:
        query = query.filter_by(kind=kind)
    items = query.order_by(VaultItem.created_at.desc()).all()
    return items


@router.post("", response_model=VaultItemResponse, status_code=status.HTTP_201_CREATED)
def create_vault_item(
    req: VaultItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new vault item."""
    item = VaultItem(
        user_id=current_user.id,
        kind=req.kind,
        title_hint=req.title_hint,
        encrypted_data=req.encrypted_data,
        nonce=req.nonce,
        asset_id=uuid.UUID(req.asset_id) if req.asset_id else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=VaultItemResponse)
def get_vault_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific vault item."""
    item = db.query(VaultItem).filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Vault item not found")
    return item


@router.patch("/{item_id}", response_model=VaultItemResponse)
def update_vault_item(
    item_id: str,
    req: VaultItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a vault item."""
    item = db.query(VaultItem).filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Vault item not found")

    if req.title_hint is not None:
        item.title_hint = req.title_hint
    if req.encrypted_data is not None:
        item.encrypted_data = req.encrypted_data
    if req.nonce is not None:
        item.nonce = req.nonce
    if req.asset_id is not None:
        item.asset_id = uuid.UUID(req.asset_id)

    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vault_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a vault item."""
    item = db.query(VaultItem).filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Vault item not found")

    db.delete(item)
    db.commit()
