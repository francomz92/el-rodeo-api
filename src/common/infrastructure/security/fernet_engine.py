"""Fernet encryption utility for encrypting webhook secrets at rest.

Derives a Fernet-compatible 32-byte key from ``settings.SECRET``
via SHA-256 with domain separation so that no additional key
management is needed. The derived key is cached at module level
for performance.
"""

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from src.common.infrastructure.core import settings

# Domain-separation context string — ensures the derived key for
# Fernet is NEVER the same as any other derivation from SECRET
# (e.g. JWT HMAC signing).
_DOMAIN_SEPARATION_CONTEXT = b"fernet-key-derivation:v1"


def _derive_key() -> bytes:
    """Derive a Fernet-compatible 32-byte url-safe base64 key from settings.SECRET.

    Uses SHA-256 of ``_DOMAIN_SEPARATION_CONTEXT + settings.SECRET``
    so the key is always exactly 32 bytes (Fernet requirement) and
    domain-separated from other uses of SECRET.
    """
    digest = hashlib.sha256(_DOMAIN_SEPARATION_CONTEXT + settings.SECRET.encode()).digest()
    return base64.urlsafe_b64encode(digest)


# Cached Fernet instance derived from the current SECRET.
_fernet: Fernet = Fernet(_derive_key())


class FernetEncryptionError(Exception):
    """Raised when decryption fails — corrupted data or SECRET rotation."""


class FernetEngine:
    """Static encrypt/decrypt utility for webhook secrets.

    Usage::

        encrypted = FernetEngine.encrypt_secret("my-plaintext-secret")
        decrypted = FernetEngine.decrypt_secret(encrypted)
    """

    @staticmethod
    def encrypt_secret(secret: str) -> str:
        """Encrypt *secret* and return a url-safe base64 ciphertext string."""
        return _fernet.encrypt(secret.encode()).decode()

    @staticmethod
    def decrypt_secret(encrypted: str) -> str:
        """Decrypt an encrypted secret back to plain text.

        Raises:
            FernetEncryptionError: If the token is invalid, corrupted,
                or was encrypted with a different key.
        """
        try:
            return _fernet.decrypt(encrypted.encode()).decode()
        except InvalidToken:
            raise FernetEncryptionError(
                "Failed to decrypt webhook secret — the token may be corrupted or SECRET has changed since encryption."
            ) from None
