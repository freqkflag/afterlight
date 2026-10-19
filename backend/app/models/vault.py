"""VaultItem model — encrypted storage for passwords, seed phrases, documents."""

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VaultItemKind(str, enum.Enum):
    PASSWORD = "password"
    SEED_PHRASE = "seed_phrase"
    DOCUMENT = "document"
    API_KEY = "api_key"
    NOTE = "note"
    CRYPTO_WALLET = "crypto_wallet"
    CUSTOM = "custom"


class VaultItem(Base):
    """
    Zero-knowledge vault item.

    The `encrypted_data` field contains the ciphertext produced by client-side
    encryption (XChaCha20-Poly1305 via libsodium). The server NEVER sees the
    plaintext. Only metadata (kind, title hint, timestamps) is readable server-side.
    """

    __tablename__ = "vault_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    kind: Mapped[VaultItemKind] = mapped_column(Enum(VaultItemKind), nullable=False, index=True)
    # Non-sensitive display hint (e.g., "Chase Bank" — never the actual credentials)
    title_hint: Mapped[str] = mapped_column(String(255), nullable=False)
    # Encrypted blob — opaque to the server
    encrypted_data: Mapped[str] = mapped_column(Text, nullable=False)
    # Nonce used for client-side encryption (safe to store alongside ciphertext)
    nonce: Mapped[str] = mapped_column(String(255), nullable=False)
    # Version for key rotation
    encryption_version: Mapped[int] = mapped_column(default=1, nullable=False)
    # Optional: which asset this vault item relates to
    asset_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assets.id", ondelete="SET NULL"), nullable=True
    )
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="vault_items")
    asset: Mapped["Asset | None"] = relationship(back_populates="vault_items")
