"""Unit tests for RefreshTokenEntity domain logic.

The entity encapsulates expiration check and revocation logic.
Pure domain — no dependencies to mock.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.auth.domain.entities import RefreshTokenEntity


class TestRefreshTokenEntityExpiration:
    """RefreshTokenEntity.is_expired checks the token's expiry time."""

    def test_returns_true_when_expired(self) -> None:
        """A token with expires_at in the past is expired."""
        token = _make_token(expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))

        assert token.is_expired() is True

    def test_returns_false_when_not_expired(self) -> None:
        """A token with expires_at in the future is not expired."""
        token = _make_token(expires_at=datetime.now(timezone.utc) + timedelta(days=1))

        assert token.is_expired() is False

    def test_returns_false_when_expires_at_is_now_plus_one_ms(self) -> None:
        """A token expiring 1ms from now is not yet expired (boundary test)."""
        future = datetime.now(timezone.utc) + timedelta(milliseconds=1)
        token = _make_token(expires_at=future)

        assert token.is_expired() is False


class TestRefreshTokenEntityRevocation:
    """RefreshTokenEntity.revoke marks the token as revoked."""

    def test_revoke_sets_flag(self) -> None:
        """Calling revoke() sets is_revoked to True."""
        token = _make_token()

        token.revoke()

        assert token.is_revoked is True

    def test_new_token_is_not_revoked(self) -> None:
        """A freshly created token starts with is_revoked=False."""
        token = _make_token()

        assert token.is_revoked is False


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_token(
    *,
    expires_at: datetime | None = None,
    is_revoked: bool = False,
) -> RefreshTokenEntity:
    """Build a minimal RefreshTokenEntity with sensible defaults."""
    return RefreshTokenEntity(
        id=uuid4(),
        user_id=uuid4(),
        token_hash="hashed_token_value",
        family_id=uuid4(),
        expires_at=expires_at or datetime.now(timezone.utc) + timedelta(days=7),
        is_revoked=is_revoked,
        created_at=datetime.now(timezone.utc),
    )
