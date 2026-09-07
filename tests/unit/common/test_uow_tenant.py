"""Unit tests for UnitOfWork tenant_id propagation.

The UoW must accept an optional tenant_id at construction and pass it
to TenantAwareRepository constructors when get_repository() is called.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)
from src.common.infrastructure.persistence.uow import UnitOfWork


class MockTenantRepo(TenantAwareRepository):
    """A concrete TenantAwareRepository for testing UoW propagation."""

    _model = MagicMock()


class MockSessionMixinRepo:
    """A repo that only uses SessionMixin (not tenant-aware)."""

    def __init__(self, session: MagicMock) -> None:
        self.db = session


import src.common.infrastructure.persistence.uow as _uow_mod


class TestUnitOfWorkTenantId:
    """UoW accepts and propagates tenant_id."""

    def setup_method(self) -> None:
        self.session = MagicMock()
        self.tenant_id = uuid4()
        self.uow = UnitOfWork(session=self.session, tenant_id=self.tenant_id)

    def test_tenant_id_is_set(self) -> None:
        """UoW stores the tenant_id passed at construction."""
        assert self.uow.tenant_id == self.tenant_id

    def test_tenant_id_defaults_to_none(self) -> None:
        """Without tenant_id, UoW.tenant_id is None."""
        uow = UnitOfWork(session=self.session)
        assert uow.tenant_id is None

    def test_get_repository_passes_tenant_id_to_tenant_aware_repo(self) -> None:
        """TenantAwareRepository repos get tenant_id from UoW."""
        with patch.object(_uow_mod, "repositories_list", {MockTenantRepo: MockTenantRepo}):
            repo = self.uow.get_repository(MockTenantRepo)  # type: ignore[arg-type]
            assert isinstance(repo, MockTenantRepo)
            assert repo._tenant_id == self.tenant_id

    def test_get_repository_passes_session_only_for_non_tenant_repo(self) -> None:
        """Non-tenant-aware repos receive only the session."""
        with patch.object(_uow_mod, "repositories_list", {MockSessionMixinRepo: MockSessionMixinRepo}):
            repo = self.uow.get_repository(MockSessionMixinRepo)
            assert isinstance(repo, MockSessionMixinRepo)
            assert repo.db == self.session

    def test_bypass_filter_defaults_to_false(self) -> None:
        """UoW.bypass_filter is False by default."""
        assert self.uow.bypass_filter is False

    def test_bypass_filter_set_true(self) -> None:
        """UoW.bypass_filter can be set to True."""
        self.uow.bypass_filter = True
        assert self.uow.bypass_filter is True

    def test_bypass_filter_passed_to_tenant_aware_repo(self) -> None:
        """When bypass_filter=True, TenantAwareRepository receives bypass."""
        with patch.object(_uow_mod, "repositories_list", {MockTenantRepo: MockTenantRepo}):
            self.uow.bypass_filter = True
            repo = self.uow.get_repository(MockTenantRepo)  # type: ignore[arg-type]
            assert repo._bypass is True
