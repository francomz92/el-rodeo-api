from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID


@dataclass
class RefreshTokenEntity:
    id: UUID
    user_id: UUID
    token_hash: str
    family_id: UUID
    expires_at: datetime
    is_revoked: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_expired(self) -> bool:
        """Return True if the current time has passed the token's expiry."""
        return datetime.now(timezone.utc) > self.expires_at

    def revoke(self) -> None:
        """Mark this token as revoked (e.g. on rotation or logout)."""
        self.is_revoked = True
