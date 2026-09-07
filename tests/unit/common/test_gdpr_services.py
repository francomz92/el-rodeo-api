"""Tests for GDPR Export and Delete use cases.

Covers Phase 3 tasks: 3.1 (GDPRExportUserDataCase), 3.2 (GDPRDeleteUserDataCase).
Uses mock UoW + repositories matching the current Clean Architecture pattern.
"""

from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest

from src.common.application.uses_cases.gdpr_cases.delete_user_data_case import (
    GDPRDeleteUserDataCase,
)
from src.common.application.uses_cases.gdpr_cases.export_user_data_case import (
    GDPRExportUserDataCase,
)

# ── Mock UoW ──────────────────────────────────────────────────────────────────


class MockUoW:
    """Mock Unit of Work that returns a given repository via get_repository()."""

    def __init__(self, repo: object) -> None:
        self._repo = repo
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def __aenter__(self) -> "MockUoW":
        return self

    async def __aexit__(self, *args) -> None:
        pass

    def get_repository(self, _repository_type: type) -> object:
        return self._repo

    async def refresh(self, _entity) -> None:
        pass

    async def dispose(self) -> None:
        pass

    @property
    def db(self):
        return None

    @db.setter
    def db(self, value):
        pass

    @property
    def bypass_filter(self):
        return False

    @bypass_filter.setter
    def bypass_filter(self, value):
        pass

    @property
    def current_user(self):
        return None

    @current_user.setter
    def current_user(self, value):
        pass

    @property
    def tenant_id(self):
        return None

    @tenant_id.setter
    def tenant_id(self, value):
        pass

    @property
    def audit_repository(self):
        return None

    @audit_repository.setter
    def audit_repository(self, value):
        pass

    @property
    def outbox_events(self):
        return []

    @outbox_events.setter
    def outbox_events(self, value):
        pass

    def add_before_commit_hook(self, hook):
        pass

    def add_outbox_event(self, event):
        pass


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def mock_export_repo() -> AsyncMock:
    """Create a mock IGDPRExportRepository with all fetch methods."""
    repo = AsyncMock()
    repo.fetch_user_profile = AsyncMock()
    repo.fetch_buyers = AsyncMock(return_value=[])
    repo.fetch_sales = AsyncMock(return_value=[])
    repo.fetch_animals = AsyncMock(return_value=[])
    repo.fetch_animal_protocols = AsyncMock(return_value=[])
    repo.fetch_purchases = AsyncMock(return_value=[])
    repo.fetch_animal_supplies = AsyncMock(return_value=[])
    repo.fetch_schedule_events = AsyncMock(return_value=[])
    repo.fetch_audit_log = AsyncMock(return_value=[])
    return repo


@pytest.fixture
def mock_delete_repo() -> AsyncMock:
    """Create a mock IGDPRDeleteRepository."""
    repo = AsyncMock()
    repo.delete_user_data = AsyncMock()
    return repo


@pytest.fixture
def export_case(mock_export_repo) -> GDPRExportUserDataCase:
    uow = MockUoW(mock_export_repo)
    return GDPRExportUserDataCase(uow)


@pytest.fixture
def delete_case(mock_delete_repo) -> GDPRDeleteUserDataCase:
    uow = MockUoW(mock_delete_repo)
    return GDPRDeleteUserDataCase(uow)


# ── Test data helpers ─────────────────────────────────────────────────────────


def make_user_profile(
    user_id: UUID,
    name: str = "Test User",
    dni: str = "12345678",
    email: str = "test@example.com",
    role: str = "viewer",
) -> dict:
    return {
        "id": user_id,
        "name": name,
        "dni": dni,
        "email": email,
        "role": role,
        "created_at": "2024-01-01T00:00:00+00:00",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3.1 GDPR Export Use Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestGDPRExportUseCase:
    """Task 3.1: GDPRExportUserDataCase should collect user data across contexts."""

    async def test_export_returns_all_expected_sections(
        self,
        user_id: UUID,
        export_case: GDPRExportUserDataCase,
        mock_export_repo: AsyncMock,
    ):
        """export_user_data() should return a dict with all required sections."""
        profile = make_user_profile(user_id)
        mock_export_repo.fetch_user_profile.return_value = profile
        mock_export_repo.fetch_buyers.return_value = [{"id": uuid4()}]
        mock_export_repo.fetch_sales.return_value = [{"id": uuid4()}]
        mock_export_repo.fetch_animals.return_value = [{"id": uuid4()}]
        mock_export_repo.fetch_animal_protocols.return_value = [{"id": uuid4()}]
        mock_export_repo.fetch_purchases.return_value = [{"id": uuid4()}]
        mock_export_repo.fetch_animal_supplies.return_value = [{"id": uuid4()}]
        mock_export_repo.fetch_schedule_events.return_value = [{"id": uuid4()}]
        mock_export_repo.fetch_audit_log.return_value = [{"id": uuid4()}]

        result = await export_case.execute(user_id)

        assert result is not None
        assert result["user_profile"] == profile
        assert len(result["buyers"]) == 1
        assert len(result["sales"]) == 1
        assert len(result["animals"]) == 1
        assert len(result["animal_protocols"]) == 1
        assert len(result["purchases"]) == 1
        assert len(result["animal_supplies"]) == 1
        assert len(result["schedule_events"]) == 1
        assert len(result["audit_log"]) == 1

    async def test_export_does_not_include_password_hash(
        self,
        user_id: UUID,
        export_case: GDPRExportUserDataCase,
        mock_export_repo: AsyncMock,
    ):
        """The password hash MUST NOT be present in the export."""
        profile = make_user_profile(user_id)
        mock_export_repo.fetch_user_profile.return_value = profile

        result = await export_case.execute(user_id)

        assert result is not None
        assert "password" not in result["user_profile"]
        assert "_hashed_password" not in result["user_profile"]

    async def test_export_with_no_associated_data(
        self,
        user_id: UUID,
        export_case: GDPRExportUserDataCase,
        mock_export_repo: AsyncMock,
    ):
        """When user has no associated data, sections should be empty lists."""
        profile = make_user_profile(user_id)
        mock_export_repo.fetch_user_profile.return_value = profile

        result = await export_case.execute(user_id)

        assert result is not None
        assert result["user_profile"] == profile
        assert result["buyers"] == []
        assert result["sales"] == []
        assert result["animals"] == []
        assert result["animal_protocols"] == []
        assert result["purchases"] == []
        assert result["animal_supplies"] == []
        assert result["schedule_events"] == []
        assert result["audit_log"] == []

    async def test_export_with_none_user_returns_none(
        self,
        user_id: UUID,
        export_case: GDPRExportUserDataCase,
        mock_export_repo: AsyncMock,
    ):
        """When user is not found, export_user_data should return None."""
        mock_export_repo.fetch_user_profile.return_value = None

        result = await export_case.execute(user_id)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# 3.2 GDPR Delete Use Case Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestGDPRDeleteUseCase:
    """Task 3.2: GDPRDeleteUserDataCase should anonymize user data."""

    async def test_delete_calls_repo_and_commits(
        self,
        user_id: UUID,
        delete_case: GDPRDeleteUserDataCase,
        mock_delete_repo: AsyncMock,
    ):
        """delete_user_data() should call repo.delete_user_data and commit."""
        await delete_case.execute(user_id)

        mock_delete_repo.delete_user_data.assert_awaited_once_with(user_id)

    async def test_delete_idempotent(
        self,
        user_id: UUID,
        delete_case: GDPRDeleteUserDataCase,
        mock_delete_repo: AsyncMock,
    ):
        """Calling delete multiple times should not raise errors."""
        await delete_case.execute(user_id)
        await delete_case.execute(user_id)

        assert mock_delete_repo.delete_user_data.await_count == 2
