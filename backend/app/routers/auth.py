"""Authentication router — register, login, token management."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.config import settings
from app.core.responses import CoercedStr
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
)
from app.database import get_db
from app.models.user import User, UserRole
from app.services.encryption import generate_salt, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: CoercedStr
    email: str
    full_name: str
    role: str
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class KeyBundleResponse(BaseModel):
    encryption_salt: str
    encrypted_key_bundle: str | None
    has_vault_key: bool


class KeyBundleUpdate(BaseModel):
    encrypted_key_bundle: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    existing = db.query(User).filter_by(email=req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    if len(req.password) < 14:
        raise HTTPException(status_code=400, detail="Password must be at least 14 characters")

    salt = generate_salt()
    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
        phone=req.phone,
        encryption_salt=salt,
        role=UserRole.OWNER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token."""
    user = db.query(User).filter_by(email=req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    user.last_login_at = datetime.now(timezone.utc)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(req: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access token."""
    payload = decode_token(req.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token required")

    user_id = payload.get("sub")
    user = db.query(User).filter_by(id=user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change the account login password (not the vault master password)."""
    if not verify_password(req.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if len(req.new_password) < 14:
        raise HTTPException(status_code=400, detail="Password must be at least 14 characters")
    current_user.hashed_password = hash_password(req.new_password)
    db.commit()
    return {"status": "ok"}


@router.get("/key-bundle", response_model=KeyBundleResponse)
def get_key_bundle(current_user: User = Depends(get_current_user)):
    """Return encryption salt and wrapped DEK blob (ciphertext only)."""
    return KeyBundleResponse(
        encryption_salt=current_user.encryption_salt,
        encrypted_key_bundle=current_user.encrypted_key_bundle,
        has_vault_key=bool(current_user.encrypted_key_bundle),
    )


@router.put("/key-bundle", response_model=KeyBundleResponse)
def put_key_bundle(
    req: KeyBundleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Store client-wrapped DEK. Server never sees the master password."""
    if current_user.encrypted_key_bundle:
        raise HTTPException(
            status_code=400,
            detail="Vault key already set. Recovery/rotation is not supported in alpha.",
        )
    current_user.encrypted_key_bundle = req.encrypted_key_bundle
    db.commit()
    db.refresh(current_user)
    return KeyBundleResponse(
        encryption_salt=current_user.encryption_salt,
        encrypted_key_bundle=current_user.encrypted_key_bundle,
        has_vault_key=True,
    )
