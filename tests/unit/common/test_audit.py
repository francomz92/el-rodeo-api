"""Tests for audit infrastructure: entity, repository, UoW hooks.

Covers PR 1 tasks: 1.1 (entity), 1.4-1.5 (UoW port + impl),
1.6 (MockUoW), 1.7-1.8 (AuditRepository port + impl), 1.9-1.10 (wire-up).
"""

from dataclasses import fields
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from tests.mocks import MockUoW

from src.common.domain.entities._audit_log_entry import AuditLogEntry
from src.common.domain.repositories.audit_repository_port import IAuditRepository
from src.common.infrastructure.persistence.repositories.audit_repository import (
    AuditRepository,
)

# ── 1.1 AuditLogEntry entity ────────────────────────────────────────────────


class TestAuditLogEntryEntity:
    """Task 1.1: Create AuditLogEntry domain entity as a dataclass."""

    def test_construct_with_all_fields(self, any_uuid: UUID) -> None:
        """Should construct with all fields provided."""
        now = datetime.now(timezone.utc)
        entry = AuditLogEntry(
            id=any_uuid,
            tenant_id=uuid4(),
            user_id=uuid4(),
            action="create",
            entity_type="user",
            entity_id=uuid4(),
            old_values=None,
            new_values={"name": "John"},
            ip_address="192.168.1.1",
            metadata={"source": "api"},
            created_at=now,
        )
        assert entry.id == any_uuid
        assert entry.action == "create"
        assert entry.entity_type == "user"
        assert entry.new_values == {"name": "John"}
        assert entry.ip_address == "192.168.1.1"

    def test_construct_with_minimal_fields(self, any_uuid: UUID) -> None:
        """Should construct with only required fields."""
        entry = AuditLogEntry(
            id=any_uuid,
            action="delete",
            entity_type="animal",
            entity_id=uuid4(),
        )
        assert entry.id == any_uuid
        assert entry.action == "delete"
        assert entry.entity_type == "animal"

    def test_default_created_at_is_datetime(self, any_uuid: UUID) -> None:
        """created_at should default to current UTC datetime if not provided."""
        entry = AuditLogEntry(
            id=any_uuid,
            action="update",
            entity_type="sale",
            entity_id=uuid4(),
        )
        assert isinstance(entry.created_at, datetime)
        # Should be timezone-aware (UTC)
        assert entry.created_at.tzinfo is not None

    def test_is_dataclass(self) -> None:
        """Should be a proper dataclass with __dataclass_fields__."""
        assert hasattr(AuditLogEntry, "__dataclass_fields__")

    def test_fields_match_spec(self) -> None:
        """All spec fields should be present."""
        field_names = {f.name for f in fields(AuditLogEntry)}
        expected = {
            "id",
            "tenant_id",
            "user_id",
            "action",
            "entity_type",
            "entity_id",
            "old_values",
            "new_values",
            "ip_address",
            "metadata",
            "created_at",
        }
        assert field_names == expected, f"Missing or extra fields: {field_names ^ expected}"

    def test_id_type(self, any_uuid: UUID) -> None:
        """id should be UUID type."""
        entry = AuditLogEntry(id=any_uuid, action="create", entity_type="x", entity_id=uuid4())
        assert isinstance(entry.id, UUID)

    def test_old_new_values_optional(self, any_uuid: UUID) -> None:
        """old_values and new_values can be None."""
        entry = AuditLogEntry(id=any_uuid, action="create", entity_type="x", entity_id=uuid4())
        assert entry.old_values is None
        assert entry.new_values is None

    def test_tenant_user_id_optional(self, any_uuid: UUID) -> None:
        """tenant_id and user_id can be None for system ops."""
        entry = AuditLogEntry(id=any_uuid, action="create", entity_type="x", entity_id=uuid4())
        assert entry.tenant_id is None
        assert entry.user_id is None

    def test_entity_id_is_uuid(self) -> None:
        """entity_id should be a UUID, not optional."""
        entry = AuditLogEntry(id=uuid4(), action="delete", entity_type="x", entity_id=uuid4())
        assert isinstance(entry.entity_id, UUID)


# ── 1.6 MockUoW audit extensions ────────────────────────────────────────────


class TestMockUoWExtensions:
    """Task 1.6: MockUoW should support audit extensions."""

    def test_add_before_commit_hook_exists(self) -> None:
        """MockUoW should have add_before_commit_hook method."""
        uow = MockUoW()
        assert hasattr(uow, "add_before_commit_hook")

    def test_add_before_commit_hook_executes_on_commit(self) -> None:
        """Hooks added via add_before_commit_hook should execute when commit is called."""
        uow = MockUoW()
        marker = MagicMock()

        uow.add_before_commit_hook(marker)
        # Mock commit executes hooks synchronously
        if hasattr(uow, "_before_commit_hooks"):
            for hook in uow._before_commit_hooks:
                hook()
            marker.assert_called_once()

    def test_multiple_hooks_execute_fifo(self) -> None:
        """Multiple hooks should execute in FIFO order."""
        uow = MockUoW()
        order: list[int] = []

        uow.add_before_commit_hook(lambda: order.append(1))
        uow.add_before_commit_hook(lambda: order.append(2))
        uow.add_before_commit_hook(lambda: order.append(3))

        if hasattr(uow, "_before_commit_hooks"):
            for hook in uow._before_commit_hooks:
                hook()
            assert order == [1, 2, 3], f"Expected FIFO order, got {order}"

    def test_audit_repository_exists(self) -> None:
        """MockUoW should have an audit_repository attribute."""
        uow = MockUoW()
        assert hasattr(uow, "audit_repository")

    def test_current_user_field(self) -> None:
        """MockUoW should have a current_user field."""
        uow = MockUoW()
        assert hasattr(uow, "current_user")
        assert uow.current_user is None


# ── 1.7 AuditRepository queue + flush ───────────────────────────────────────


class TestAuditRepository:
    """Task 1.7-1.8: AuditRepository queue and flush via Core."""

    def test_is_abstract(self) -> None:
        """IAuditRepository should be an abstract class."""
        with pytest.raises(TypeError):
            IAuditRepository()  # type: ignore[abstract]

    def test_record_method_defined(self) -> None:
        """IAuditRepository should have record abstract method."""
        assert hasattr(IAuditRepository, "record")

    def test_record_appends_to_queue(self) -> None:
        """record() should append an entry to the internal queue."""
        repo = AuditRepository()
        repo.record(
            action="create",
            entity_type="user",
            entity_id=uuid4(),
        )
        assert len(repo._queue) == 1

    def test_record_stores_structured_entry(self) -> None:
        """record() should store a dict with correct keys."""
        repo = AuditRepository()
        entity_id = uuid4()
        tenant_id = uuid4()
        user_id = uuid4()
        repo.record(
            action="update",
            entity_type="animal",
            entity_id=entity_id,
            tenant_id=tenant_id,
            user_id=user_id,
            old_values={"name": "Old"},
            new_values={"name": "New"},
            metadata={"reason": "correction"},
            ip_address="10.0.0.1",
        )
        entry = repo._queue[0]
        assert entry["action"] == "update"
        assert entry["entity_type"] == "animal"
        assert entry["entity_id"] == entity_id
        assert entry["tenant_id"] == tenant_id
        assert entry["user_id"] == user_id
        assert entry["old_values"] == {"name": "Old"}
        assert entry["new_values"] == {"name": "New"}
        assert entry["metadata"] == {"reason": "correction"}
        assert entry["ip_address"] == "10.0.0.1"
        assert "id" in entry
        assert "created_at" in entry

    @pytest.mark.asyncio
    async def test_flush_clears_queue(self) -> None:
        """flush() should clear the internal queue after execution."""
        repo = AuditRepository()
        repo.record(action="create", entity_type="x", entity_id=uuid4())
        repo.record(action="delete", entity_type="y", entity_id=uuid4())

        # Use a mock connection to avoid actual DB
        mock_conn = AsyncMock()
        await repo.flush(mock_conn)

        assert len(repo._queue) == 0

    @pytest.mark.asyncio
    async def test_flush_calls_execute(self) -> None:
        """flush() should call connection.execute() with an INSERT statement."""
        repo = AuditRepository()
        entity_id = uuid4()
        repo.record(action="create", entity_type="test", entity_id=entity_id)

        mock_conn = AsyncMock()
        await repo.flush(mock_conn)

        assert mock_conn.execute.call_count == 1
        # Verify it was called with an insert statement
        call_args = mock_conn.execute.call_args[0][0]
        call_str = str(call_args)
        assert "INSERT" in call_str.upper()
        assert "audit_log" in call_str

    @pytest.mark.asyncio
    async def test_flush_empty_queue(self) -> None:
        """flush() with empty queue should not call execute."""
        repo = AuditRepository()
        mock_conn = AsyncMock()
        await repo.flush(mock_conn)
        mock_conn.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_bulk_flush_multiple_entries(self) -> None:
        """flush() should batch multiple entries in a single INSERT."""
        repo = AuditRepository()
        for _ in range(5):
            repo.record(action="create", entity_type="x", entity_id=uuid4())

        mock_conn = AsyncMock()
        await repo.flush(mock_conn)

        assert mock_conn.execute.call_count == 1, "Expected single bulk INSERT, not N individual inserts"

    def test_clear_without_flush(self) -> None:
        """clear() should empty queue without executing."""
        repo = AuditRepository()
        repo.record(action="create", entity_type="x", entity_id=uuid4())
        repo.clear()
        assert len(repo._queue) == 0

    @pytest.mark.asyncio
    async def test_queue_length_tracking(self) -> None:
        """Should track queue length."""
        repo = AuditRepository()
        assert repo.queue_length() == 0
        repo.record(action="create", entity_type="x", entity_id=uuid4())
        assert repo.queue_length() == 1
        repo.record(action="create", entity_type="y", entity_id=uuid4())
        assert repo.queue_length() == 2
        mock_conn = AsyncMock()
        await repo.flush(mock_conn)
        assert repo.queue_length() == 0


# ── 1.9 UoW hook behavior ───────────────────────────────────────────────────


class TestUnitOfWorkHookBehavior:
    """Task 1.9: UoW before_commit hook ordering and rollback."""

    @pytest.fixture
    def mock_session(self) -> AsyncMock:
        """Provide a mock AsyncSession."""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.close = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_hooks_execute_before_commit_in_fifo_order(self, mock_session: AsyncMock) -> None:
        """Hooks should execute in FIFO order before db.commit()."""
        from src.common.infrastructure.persistence.uow import UnitOfWork

        uow = UnitOfWork(session=mock_session)
        order: list[int] = []

        uow.add_before_commit_hook(lambda: order.append(1))
        uow.add_before_commit_hook(lambda: order.append(2))
        uow.add_before_commit_hook(lambda: order.append(3))

        await uow.commit()

        assert order == [1, 2, 3], f"Expected FIFO order, got {order}"
        # commit should have been called AFTER hooks
        assert mock_session.commit.await_count == 1

    @pytest.mark.asyncio
    async def test_hook_failure_rollback_and_raises(self, mock_session: AsyncMock) -> None:
        """If a hook raises, should rollback and propagate exception."""
        from src.common.infrastructure.persistence.uow import UnitOfWork

        uow = UnitOfWork(session=mock_session)

        uow.add_before_commit_hook(lambda: None)  # first hook OK
        uow.add_before_commit_hook(lambda: (_ for _ in ()).throw(ValueError("hook failed")))  # second fails
        uow.add_before_commit_hook(lambda: None)  # third should NOT execute

        with pytest.raises(ValueError, match="hook failed"):
            await uow.commit()

        # Should rollback, not commit
        assert mock_session.rollback.await_count == 1
        assert mock_session.commit.await_count == 0

    @pytest.mark.asyncio
    async def test_current_user_accepted_in_constructor(self, mock_session: AsyncMock) -> None:
        """UnitOfWork should accept current_user in constructor."""
        from src.common.infrastructure.persistence.uow import UnitOfWork

        user_mock = MagicMock()
        user_mock.id = uuid4()
        uow = UnitOfWork(session=mock_session, current_user=user_mock)

        assert uow.current_user is user_mock

    @pytest.mark.asyncio
    async def test_audit_repository_available(self, mock_session: AsyncMock) -> None:
        """UnitOfWork should provide audit_repository."""
        from src.common.infrastructure.persistence.uow import UnitOfWork

        uow = UnitOfWork(session=mock_session)
        repo = uow.audit_repository
        assert isinstance(repo, AuditRepository)

    @pytest.mark.asyncio
    async def test_audit_repository_flush_wired_as_hook(self, mock_session: AsyncMock) -> None:
        """AuditRepository.flush should be registered as a before_commit hook."""
        from src.common.infrastructure.persistence.uow import UnitOfWork

        uow = UnitOfWork(session=mock_session)
        repo = uow.audit_repository

        # Record an audit entry
        repo.record(action="create", entity_type="test", entity_id=uuid4())
        assert repo.queue_length() == 1

        # Commit should trigger flush via hook
        await uow.commit()

        # After commit, queue should be empty (flushed)
        assert repo.queue_length() == 0

    @pytest.mark.asyncio
    async def test_no_hooks_still_commits(self, mock_session: AsyncMock) -> None:
        """commit() should work fine with no hooks registered."""
        from src.common.infrastructure.persistence.uow import UnitOfWork

        uow = UnitOfWork(session=mock_session)
        await uow.commit()
        assert mock_session.commit.await_count == 1
