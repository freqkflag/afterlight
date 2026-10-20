"""Assets router — CRUD for digital assets."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.responses import CoercedStr
from app.core.security import get_current_user
from app.database import get_db
from app.models.asset import Asset, AssetKind, AssetStatus
from app.models.user import User

router = APIRouter(prefix="/assets", tags=["assets"])


class AssetCreate(BaseModel):
    kind: AssetKind
    name: str
    identifier: str | None = None
    estimated_value_cents: int | None = None
    notes: str | None = None
    discovery_source: str = "manual"


class AssetUpdate(BaseModel):
    kind: AssetKind | None = None
    name: str | None = None
    identifier: str | None = None
    estimated_value_cents: int | None = None
    status: AssetStatus | None = None
    notes: str | None = None
    has_credentials: bool | None = None


class AssetResponse(BaseModel):
    id: CoercedStr
    kind: str
    name: str
    identifier: str | None
    estimated_value_cents: int | None
    status: str
    discovery_source: str
    notes: str | None
    has_credentials: bool
    created_at: CoercedStr
    updated_at: CoercedStr

    class Config:
        from_attributes = True


@router.get("", response_model=list[AssetResponse])
def list_assets(
    kind: AssetKind | None = None,
    status: AssetStatus | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all assets for the current user."""
    query = db.query(Asset).filter_by(user_id=current_user.id)
    if kind:
        query = query.filter_by(kind=kind)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(Asset.created_at.desc()).all()


@router.post("", response_model=AssetResponse, status_code=status.HTTP_201_CREATED)
def create_asset(
    req: AssetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new asset."""
    asset = Asset(
        user_id=current_user.id,
        kind=req.kind,
        name=req.name,
        identifier=req.identifier,
        estimated_value_cents=req.estimated_value_cents,
        notes=req.notes,
        discovery_source=req.discovery_source,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("/{asset_id}", response_model=AssetResponse)
def get_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific asset."""
    asset = db.query(Asset).filter_by(id=asset_id, user_id=current_user.id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.patch("/{asset_id}", response_model=AssetResponse)
def update_asset(
    asset_id: str,
    req: AssetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an asset."""
    asset = db.query(Asset).filter_by(id=asset_id, user_id=current_user.id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    for field, value in req.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)

    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_asset(
    asset_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an asset."""
    asset = db.query(Asset).filter_by(id=asset_id, user_id=current_user.id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    db.delete(asset)
    db.commit()


@router.get("/summary/value")
def get_asset_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a summary of asset values by kind."""
    from sqlalchemy import func

    results = (
        db.query(Asset.kind, func.count(Asset.id), func.sum(Asset.estimated_value_cents))
        .filter_by(user_id=current_user.id)
        .group_by(Asset.kind)
        .all()
    )

    return {
        "by_kind": [
            {
                "kind": kind,
                "count": count,
                "total_value_cents": total or 0,
            }
            for kind, count, total in results
        ],
        "total_assets": sum(r[1] for r in results),
        "total_value_cents": sum(r[2] or 0 for r in results),
    }
