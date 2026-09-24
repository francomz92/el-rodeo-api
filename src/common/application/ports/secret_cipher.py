from typing import Protocol


class SecretCipher(Protocol):
    """Application boundary for encrypting and decrypting webhook secrets."""

    def encrypt_secret(self, secret: str) -> str:
        """Encrypt a plaintext secret for persistence."""
        ...

    def decrypt_secret(self, encrypted: str) -> str:
        """Decrypt a persisted secret for application use."""
        ...
