"""
Zero-Knowledge Encryption Service

Afterlight uses a zero-knowledge architecture:
- The user's master password NEVER leaves the client
- The client derives a key encryption key (KEK) using Argon2id
- The KEK encrypts the user's data encryption key (DEK)
- The DEK encrypts all vault items (client-side)
- The server stores ONLY ciphertext + the encrypted DEK

This module provides server-side helpers for:
- Password hashing (Argon2id) for authentication
- Key derivation verification
- Envelope encryption for the DEK (server-side, using a master key)
"""

import base64
import hashlib
import os

import nacl.secret
import nacl.utils
from nacl.pwhash import argon2id
from nacl.exceptions import InvalidkeyError

from app.config import settings


# --- Password Hashing (for authentication) ---

def hash_password(password: str) -> str:
    """Hash a password using Argon2id. Returns a string to store in the DB."""
    # nacl's argon2id returns a bytes object that includes the hash
    hashed = argon2id.str(
        password.encode("utf-8"),
        opslimit=settings.argon2_time_cost,
        memlimit=settings.argon2_memory_cost,
    )
    return base64.b64encode(hashed).decode("ascii")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its Argon2id hash."""
    try:
        hashed_bytes = base64.b64decode(hashed.encode("ascii"))
        argon2id.verify(hashed_bytes, password.encode("utf-8"))
        return True
    except (InvalidkeyError, ValueError):
        return False


# --- Key Derivation (client-side, but we provide the parameters) ---

def generate_salt() -> str:
    """Generate a new random salt for key derivation."""
    return base64.b64encode(os.urandom(32)).decode("ascii")


def derive_key_params() -> dict:
    """Return the Argon2id parameters the client should use for key derivation."""
    return {
        "algorithm": "argon2id",
        "opslimit": settings.argon2_time_cost,
        "memlimit": settings.argon2_memory_cost,
        "parallelism": settings.argon2_parallelism,
    }


# --- Envelope Encryption (server-side, for the DEK) ---

def _get_master_key() -> bytes:
    """Get the master encryption key for envelope encryption."""
    key_bytes = base64.b64decode(settings.encryption_key)
    if len(key_bytes) != 32:
        raise ValueError("encryption_key must be base64-encoded 32 bytes")
    return key_bytes


def encrypt_dek(dek: bytes) -> tuple[str, str]:
    """
    Encrypt a Data Encryption Key (DEK) using the server's master key.
    Returns (ciphertext_b64, nonce_b64).
    """
    box = nacl.secret.SecretBox(_get_master_key())
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    encrypted = box.encrypt(dek, nonce)
    return (
        base64.b64encode(encrypted.ciphertext).decode("ascii"),
        base64.b64encode(nonce).decode("ascii"),
    )


def decrypt_dek(ciphertext_b64: str, nonce_b64: str) -> bytes:
    """Decrypt a DEK using the server's master key."""
    box = nacl.secret.SecretBox(_get_master_key())
    ciphertext = base64.b64decode(ciphertext_b64.encode("ascii"))
    nonce = base64.b64decode(nonce_b64.encode("ascii"))
    return box.decrypt(ciphertext, nonce)


# --- Helpers ---

def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return base64.urlsafe_b64encode(os.urandom(length)).decode("ascii").rstrip("=")


def constant_time_compare(a: str, b: str) -> bool:
    """Constant-time string comparison to prevent timing attacks."""
    return hashlib.sha256(a.encode()).digest() == hashlib.sha256(b.encode()).digest()
