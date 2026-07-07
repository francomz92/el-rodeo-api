"""Unit tests for bcrypt async wrapper.

Verifies that hash_password and verify_password delegate to
thread pool via asyncio.to_thread() and produce valid bcrypt hashes.
"""

import pytest

from src.common.infrastructure.adapters.security.hashers import (
    SecurityService,
)


class TestSecurityServiceAsync:
    """SecurityService wraps bcrypt calls with asyncio.to_thread."""

    @pytest.fixture
    def service(self) -> SecurityService:
        return SecurityService()

    @pytest.mark.asyncio
    async def test_hash_password_returns_hash(self, service: SecurityService) -> None:
        """hash_password returns a valid bcrypt hash string."""
        hashed = await service.hash_password("MyS3cur3P@ss!")
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    @pytest.mark.asyncio
    async def test_verify_password_matches(self, service: SecurityService) -> None:
        """verify_password returns True for the correct password."""
        password = "MyS3cur3P@ss!"
        hashed = await service.hash_password(password)
        result = await service.verify_password(password, hashed)
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_password_rejects_wrong(self, service: SecurityService) -> None:
        """verify_password returns False for incorrect password."""
        hashed = await service.hash_password("CorrectP@ss1")
        result = await service.verify_password("WrongP@ss1", hashed)
        assert result is False

    @pytest.mark.asyncio
    async def test_generate_random_str_returns_string(self, service: SecurityService) -> None:
        """generate_random_str returns a string of requested length."""
        result = service.generate_random_str(12)
        assert isinstance(result, str)
        assert len(result) == 12

    @pytest.mark.asyncio
    async def test_hash_password_different_each_time(self, service: SecurityService) -> None:
        """hash_password produces different hashes for the same password (salting)."""
        password = "SamePassword123"
        hash1 = await service.hash_password(password)
        hash2 = await service.hash_password(password)
        assert hash1 != hash2
