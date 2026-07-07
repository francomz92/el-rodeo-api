"""Unit tests for TokenService refresh token methods.

Tests for generate_refresh_token, decode_refresh_token, rotate_refresh_token,
revoke_refresh_token, and revoke_user_refresh_tokens.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import jwt as pyjwt
import pytest

from src.auth.application.exceptions.authentication import InvalidCredentialError
from src.auth.domain.entities import RefreshTokenEntity
from src.common.infrastructure.adapters.security.tokens import TokenService
from src.common.utils.date_utils import get_current_datetime

# ── Constants ──────────────────────────────────────────────────────────────────

SECRET = "test-secret-key-thats-at-least-32-chars-long!!"
ALGORITHM = "HS256"


@pytest.fixture
def token_service() -> TokenService:
    return TokenService(secret=SECRET, algorithm=ALGORITHM)


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    repo.save = AsyncMock()
    repo.revoke_token = AsyncMock()
    repo.revoke_family = AsyncMock()
    repo.revoke_all_user_tokens = AsyncMock()
    repo.find_by_id = AsyncMock(return_value=None)
    return repo


# ── generate_refresh_token ──────────────────────────────────────────────────


class TestGenerateRefreshToken:
    def test_generates_valid_jwt(self, token_service: TokenService) -> None:
        """Generated token is a valid JWT with expected claims."""
        user_id = str(uuid4())
        token = token_service.generate_refresh_token(user_id=user_id)
        payload = pyjwt.decode(token, SECRET, [ALGORITHM])

        assert payload["type"] == "refresh"
        assert payload["user_id"] == user_id
        assert "jti" in payload
        assert "refresh_token_id" in payload
        assert payload["refresh_token_id"] == payload["jti"]
        assert "family_id" in payload
        assert "exp" in payload
        assert "iat" in payload

    def test_generates_token_with_custom_family_id(self, token_service: TokenService) -> None:
        """When family_id is provided, it appears in the token claims."""
        user_id = str(uuid4())
        family_id = str(uuid4())
        token = token_service.generate_refresh_token(user_id=user_id, family_id=family_id)
        payload = pyjwt.decode(token, SECRET, [ALGORITHM])

        assert payload["family_id"] == family_id
        assert payload["user_id"] == user_id

    def test_generates_unique_tokens(self, token_service: TokenService) -> None:
        """Two tokens for the same user have different jti values."""
        user_id = str(uuid4())
        token1 = token_service.generate_refresh_token(user_id=user_id)
        token2 = token_service.generate_refresh_token(user_id=user_id)

        payload1 = pyjwt.decode(token1, SECRET, [ALGORITHM])
        payload2 = pyjwt.decode(token2, SECRET, [ALGORITHM])

        assert payload1["jti"] != payload2["jti"]

    def test_token_expires_in_future(self, token_service: TokenService) -> None:
        """Token's expiry is at least 6 days from now (7d default)."""
        user_id = str(uuid4())
        token = token_service.generate_refresh_token(user_id=user_id)
        payload = pyjwt.decode(token, SECRET, [ALGORITHM])
        exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        now = get_current_datetime()

        # Should be at least 6 days in the future (allows 1 day tolerance)
        assert exp > now + timedelta(days=6)


# ── decode_refresh_token ──────────────────────────────────────────────────────


class TestDecodeRefreshToken:
    def test_decodes_valid_token(self, token_service: TokenService) -> None:
        """A valid refresh token is decoded successfully."""
        user_id = str(uuid4())
        token = token_service.generate_refresh_token(user_id=user_id)
        payload = token_service.decode_refresh_token(token)

        assert payload["type"] == "refresh"
        assert payload["user_id"] == user_id
        assert "jti" in payload
        assert "family_id" in payload

    def test_rejects_access_token(self, token_service: TokenService) -> None:
        """decode_refresh_token raises on an access token (type=access)."""
        access = token_service.generate({"user_id": str(uuid4())}, exp_minutes=15)
        with pytest.raises(InvalidCredentialError):
            token_service.decode_refresh_token(access)

    def test_rejects_expired_token(self, token_service: TokenService) -> None:
        """An expired refresh token raises InvalidCredentialError."""
        user_id = str(uuid4())
        expired_payload = {
            "user_id": user_id,
            "type": "refresh",
            "jti": str(uuid4()),
            "refresh_token_id": str(uuid4()),
            "family_id": str(uuid4()),
            "exp": get_current_datetime() - timedelta(hours=1),
            "iat": get_current_datetime() - timedelta(hours=2),
        }
        expired_token = pyjwt.encode(expired_payload, SECRET, algorithm=ALGORITHM)

        with pytest.raises(InvalidCredentialError):
            token_service.decode_refresh_token(expired_token)

    def test_rejects_malformed_token(self, token_service: TokenService) -> None:
        """A completely invalid token string raises InvalidCredentialError."""
        with pytest.raises(InvalidCredentialError):
            token_service.decode_refresh_token("not-a-valid-jwt-token")


# ── rotate_refresh_token ──────────────────────────────────────────────────────


class TestRotateRefreshToken:
    async def test_rotates_token_successfully(self, token_service: TokenService, mock_repo: AsyncMock) -> None:
        """A valid refresh token is rotated: old revoked, new pair returned."""
        user_id = str(uuid4())
        old_token = token_service.generate_refresh_token(user_id=user_id)
        old_payload = pyjwt.decode(old_token, SECRET, [ALGORITHM])
        old_jti = old_payload["jti"]
        family_id_str = old_payload["family_id"]

        # Mock: token is active (not revoked)
        entity = RefreshTokenEntity(
            id=UUID(old_jti),
            user_id=UUID(user_id),
            token_hash="fake_hash",
            family_id=UUID(family_id_str),
            expires_at=get_current_datetime() + timedelta(days=7),
            is_revoked=False,
        )
        mock_repo.find_by_id.return_value = entity

        access_token, new_refresh = await token_service.rotate_refresh_token(old_token, mock_repo)

        # Verify new access token
        access_payload = pyjwt.decode(access_token, SECRET, [ALGORITHM])
        assert access_payload["type"] == "access"
        assert access_payload["user_id"] == user_id

        # Verify new refresh token has same family_id
        new_refresh_payload = pyjwt.decode(new_refresh, SECRET, [ALGORITHM])
        assert new_refresh_payload["type"] == "refresh"
        assert new_refresh_payload["family_id"] == family_id_str
        assert new_refresh_payload["jti"] != old_jti

        # Verify old token was revoked
        mock_repo.revoke_token.assert_awaited_once()

        # Verify new token was saved
        mock_repo.save.assert_awaited_once()

    async def test_reuse_detection_revokes_family(self, token_service: TokenService, mock_repo: AsyncMock) -> None:
        """When a rotated token is presented again, the entire family is revoked."""
        user_id = str(uuid4())
        old_token = token_service.generate_refresh_token(user_id=user_id)
        old_payload = pyjwt.decode(old_token, SECRET, [ALGORITHM])
        family_id_str = old_payload["family_id"]
        refresh_token_id_str = old_payload["refresh_token_id"]

        # Mock: token is already revoked
        entity = RefreshTokenEntity(
            id=UUID(refresh_token_id_str),
            user_id=UUID(user_id),
            token_hash="fake_hash",
            family_id=UUID(family_id_str),
            expires_at=get_current_datetime() + timedelta(days=7),
            is_revoked=True,  # Already revoked!
        )
        mock_repo.find_by_id.return_value = entity

        with pytest.raises(InvalidCredentialError) as exc:
            await token_service.rotate_refresh_token(old_token, mock_repo)

        assert "token_family_revoked" in str(exc.value)
        # Entire family should be revoked
        mock_repo.revoke_family.assert_awaited_once()


# ── revoke_refresh_token ──────────────────────────────────────────────────────


class TestRevokeRefreshToken:
    async def test_revokes_token_via_repo(self, token_service: TokenService, mock_repo: AsyncMock) -> None:
        """revoke_refresh_token decodes the token and revokes through the repo."""
        user_id = str(uuid4())
        token = token_service.generate_refresh_token(user_id=user_id)
        payload = pyjwt.decode(token, SECRET, [ALGORITHM])
        refresh_token_id_str = payload["refresh_token_id"]

        entity = RefreshTokenEntity(
            id=UUID(refresh_token_id_str),
            user_id=UUID(user_id),
            token_hash="fake_hash",
            family_id=UUID(payload["family_id"]),
            expires_at=get_current_datetime() + timedelta(days=7),
            is_revoked=False,
        )
        mock_repo.find_by_id.return_value = entity

        await token_service.revoke_refresh_token(token, mock_repo)

        mock_repo.revoke_token.assert_awaited_once()


# ── revoke_user_refresh_tokens ────────────────────────────────────────────────


class TestRevokeUserRefreshTokens:
    async def test_revokes_all_tokens_for_user(self, token_service: TokenService, mock_repo: AsyncMock) -> None:
        """revoke_user_refresh_tokens calls repo with the user ID."""
        user_id = uuid4()
        await token_service.revoke_user_refresh_tokens(user_id, mock_repo)
        mock_repo.revoke_all_user_tokens.assert_awaited_once_with(user_id)
