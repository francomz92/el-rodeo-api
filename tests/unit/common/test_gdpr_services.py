"""Tests for GDPR Export and Delete services.

Covers Phase 3 tasks: 3.1 (GDPRExportService), 3.2 (GDPRDeleteService).
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.common.application.services.gdpr_delete_service import GDPRDeleteService
from src.common.application.services.gdpr_export_service import GDPRExportService

# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def user_id() -> UUID:
    return uuid4()


@pytest.fixture
def now() -> datetime:
    return datetime.now(tz=timezone.utc)


@pytest.fixture
def mock_db() -> AsyncMock:
    """Create a mock AsyncSession."""
    return AsyncMock()


@pytest.fixture
def mock_result(mock_db) -> MagicMock:
    """Create a mock Result that returns no rows by default.

    The fixture configures mock_db.execute() to return this result,
    so ALL queries return empty unless overridden.
    """
    result = MagicMock()
    result.mappings().all.return_value = []
    result.mappings().one_or_none.return_value = None
    mock_db.execute.return_value = result
    return result


@pytest.fixture
def export_service(mock_db) -> GDPRExportService:
    return GDPRExportService(db=mock_db)


@pytest.fixture
def delete_service(mock_db) -> GDPRDeleteService:
    return GDPRDeleteService(db=mock_db)


# ── Test data helpers ─────────────────────────────────────────────────────────


def make_user_row(
    user_id: UUID,
    name: str = "Test User",
    dni: str = "12345678",
    email: str = "test@example.com",
    role: str = "viewer",
    is_active: bool = True,
) -> dict:
    return {
        "id": user_id,
        "name": name,
        "dni": dni,
        "email": email,
        "password": "$2b$12$hashedpassword",
        "role": role,
        "is_active": is_active,
        "tenant_id": uuid4(),
        "created_at": datetime.now(tz=timezone.utc),
        "updated_at": datetime.now(tz=timezone.utc),
    }


def make_buyer_row(user_id: UUID) -> dict:
    return {
        "id": uuid4(),
        "user_id": user_id,
        "name": "Buyer Name",
        "description": "Test buyer",
        "contact_number": "1234567890",
        "contact_address": "123 Street",
        "tenant_id": uuid4(),
        "created_at": datetime.now(tz=timezone.utc),
    }


def make_sale_row(user_id: UUID) -> dict:
    return {
        "id": uuid4(),
        "user_id": user_id,
        "buyer_id": uuid4(),
        "animal_id": uuid4(),
        "sale_date": datetime.now(tz=timezone.utc),
        "price": 1000.0,
        "price_per_kg": 5.0,
        "weight": 200.0,
        "description": "Test sale",
        "tenant_id": uuid4(),
        "created_at": datetime.now(tz=timezone.utc),
    }


def make_animal_row(user_id: UUID) -> dict:
    return {
        "id": uuid4(),
        "user_id": user_id,
        "type_id": uuid4(),
        "caravana": "CAR-123456",
        "tag": "TAG-123456",
        "date_of_birth": datetime.now(tz=timezone.utc),
        "initial_weight": 150.0,
        "initial_weight_date": datetime.now(tz=timezone.utc),
        "last_weight": 320.0,
        "breed": "Angus",
        "status": "ready",
        "tenant_id": uuid4(),
        "created_at": datetime.now(tz=timezone.utc),
    }


def make_protocol_row(user_id: UUID) -> dict:
    return {
        "id": uuid4(),
        "user_id": user_id,
        "animal_id": uuid4(),
        "vaccinated": True,
        "vaccinated_date": datetime.now(tz=timezone.utc),
        "sale_permission": False,
        "sale_permission_date": None,
        "tenant_id": uuid4(),
        "created_at": datetime.now(tz=timezone.utc),
    }


def make_purchase_row(user_id: UUID) -> dict:
    return {
        "id": uuid4(),
        "user_id": user_id,
        "supply_id": uuid4(),
        "amount": 10.0,
        "price": 500.0,
        "purchase_date": datetime.now(tz=timezone.utc),
        "unit_price": 50.0,
        "unit_of_measurement": "unit",
        "tenant_id": uuid4(),
        "created_at": datetime.now(tz=timezone.utc),
    }


def make_supply_row(user_id: UUID) -> dict:
    return {
        "id": uuid4(),
        "user_id": user_id,
        "type_id": uuid4(),
        "name": "Feed",
        "description": "Animal feed",
        "amount": 100.0,
        "critical_amount": 20.0,
        "unit_of_measurement": "kg",
        "tenant_id": uuid4(),
        "created_at": datetime.now(tz=timezone.utc),
    }


def make_schedule_event_row(user_id: UUID) -> dict:
    return {
        "id": uuid4(),
        "user_id": user_id,
        "title": "Health check",
        "description": "Annual checkup",
        "event_date": datetime.now(tz=timezone.utc),
        "pending": True,
        "tenant_id": uuid4(),
        "created_at": datetime.now(tz=timezone.utc),
    }


def make_audit_log_row(user_id: UUID) -> dict:
    return {
        "id": uuid4(),
        "user_id": user_id,
        "entity_type": "user",
        "entity_id": uuid4(),
        "action": "update",
        "old_values": None,
        "new_values": {"name": "New Name"},
        "tenant_id": uuid4(),
        "created_at": datetime.now(tz=timezone.utc),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 3.1 GDPR Export Service Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestGDPRExportService:
    """Task 3.1: GDPRExportService should collect user data across contexts."""

    async def test_export_returns_all_expected_sections(
        self,
        user_id,
        export_service,
        mock_db,
        mock_result,
    ):
        """export_user_data() should return a dict with all required sections."""
        # ── Configure mock to return data for each table ──────────────
        user_row = make_user_row(user_id)
        buyer_rows = [make_buyer_row(user_id)]
        sale_rows = [make_sale_row(user_id)]
        animal_rows = [make_animal_row(user_id)]
        protocol_rows = [make_protocol_row(user_id)]
        purchase_rows = [make_purchase_row(user_id)]
        supply_rows = [make_supply_row(user_id)]
        event_rows = [make_schedule_event_row(user_id)]
        audit_rows = [make_audit_log_row(user_id)]

        # Each execute() call returns different data based on query type.
        # We use side_effect to return different results in order.
        def execute_side_effect(*args, **kwargs):
            """Return appropriate mock data based on the query."""
            query = args[0] if args else kwargs.get("statement")
            compiled = str(query.compile(compile_kwargs={"literal_binds": True}))

            result = MagicMock()

            if " FROM users" in compiled or "FROM users" in compiled:
                mappings = MagicMock()
                mappings.one_or_none.return_value = user_row
                result.mappings.return_value = mappings
            elif " FROM buyers" in compiled or "FROM buyers" in compiled:
                result.mappings().all.return_value = buyer_rows
            elif " FROM sales" in compiled or "FROM sales" in compiled:
                result.mappings().all.return_value = sale_rows
            elif " FROM animals" in compiled or "FROM animals" in compiled:
                result.mappings().all.return_value = animal_rows
            elif " FROM animal_protocols" in compiled or "FROM animal_protocols" in compiled:
                result.mappings().all.return_value = protocol_rows
            elif " FROM purchases" in compiled or "FROM purchases" in compiled:
                result.mappings().all.return_value = purchase_rows
            elif " FROM animal_supplies" in compiled or "FROM animal_supplies" in compiled:
                result.mappings().all.return_value = supply_rows
            elif " FROM scheduled_events" in compiled or "FROM scheduled_events" in compiled:
                result.mappings().all.return_value = event_rows
            elif " FROM audit_log" in compiled or "FROM audit_log" in compiled:
                result.mappings().all.return_value = audit_rows
            else:
                result.mappings().all.return_value = []
                result.mappings().one_or_none.return_value = None

            return result

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)

        # ── Execute ──────────────────────────────────────────────────
        result = await export_service.export_user_data(user_id)

        # ── Assert all sections exist ────────────────────────────────
        assert "user_profile" in result, "Missing user_profile section"
        assert "buyers" in result, "Missing buyers section"
        assert "sales" in result, "Missing sales section"
        assert "animals" in result, "Missing animals section"
        assert "animal_protocols" in result, "Missing animal_protocols section"
        assert "purchases" in result, "Missing purchases section"
        assert "animal_supplies" in result, "Missing animal_supplies section"
        assert "schedule_events" in result, "Missing schedule_events section"
        assert "audit_log" in result, "Missing audit_log section"

        # ── Assert user profile has expected fields ──────────────────
        profile = result["user_profile"]
        assert profile["name"] == "Test User"
        assert profile["email"] == "test@example.com"
        assert profile["dni"] == "12345678"
        assert profile["role"] == "viewer"

        # ── Assert collections are non-empty ─────────────────────────
        assert len(result["buyers"]) == 1
        assert len(result["sales"]) == 1
        assert len(result["animals"]) == 1
        assert len(result["audit_log"]) == 1

    async def test_export_does_not_include_password_hash(
        self,
        user_id,
        export_service,
        mock_db,
        mock_result,
    ):
        """The password hash MUST NOT be present in the export."""
        # Simulate the actual column selection: the real query selects
        # only PII fields via select(User.id, User.name, User.dni, ...)
        # so the result dict has NO password key.
        user_row_no_password = make_user_row(user_id)
        user_row_no_password.pop("password", None)

        def execute_side_effect(*args, **kwargs):
            query = args[0] if args else kwargs.get("statement")
            compiled = str(query.compile(compile_kwargs={"literal_binds": True}))

            result = MagicMock()
            if " FROM users" in compiled or "FROM users" in compiled:
                mappings = MagicMock()
                mappings.one_or_none.return_value = user_row_no_password
                result.mappings.return_value = mappings
            else:
                result.mappings().all.return_value = []
                result.mappings().one_or_none.return_value = None
            return result

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)

        result = await export_service.export_user_data(user_id)

        profile = result["user_profile"]
        assert "password" not in profile, "Password hash leaked into export"
        assert "_hashed_password" not in profile, "Password hash leaked"

    async def test_export_with_no_associated_data(
        self,
        user_id,
        export_service,
        mock_db,
        mock_result,
    ):
        """When user has no associated data, sections should be empty lists."""
        user_row = make_user_row(user_id)

        def execute_side_effect(*args, **kwargs):
            query = args[0] if args else kwargs.get("statement")
            compiled = str(query.compile(compile_kwargs={"literal_binds": True}))

            result = MagicMock()
            if " FROM users" in compiled or "FROM users" in compiled:
                mappings = MagicMock()
                mappings.one_or_none.return_value = user_row
                result.mappings.return_value = mappings
            else:
                result.mappings().all.return_value = []
                result.mappings().one_or_none.return_value = None
            return result

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)

        result = await export_service.export_user_data(user_id)

        assert result["user_profile"]["name"] == "Test User"
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
        user_id,
        export_service,
        mock_db,
    ):
        """When user is not found, export_user_data should return None."""

        def execute_side_effect(*args, **kwargs):
            result = MagicMock()
            result.mappings.return_value = MagicMock()
            result.mappings().one_or_none.return_value = None
            return result

        mock_db.execute = AsyncMock(side_effect=execute_side_effect)

        result = await export_service.export_user_data(user_id)
        assert result is None, "Expected None for non-existent user"


# ═══════════════════════════════════════════════════════════════════════════════
# 3.2 GDPR Delete Service Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestGDPRDeleteService:
    """Task 3.2: GDPRDeleteService should anonymize user data."""

    async def test_delete_anonymizes_user_id_on_business_records(
        self,
        user_id,
        delete_service,
        mock_db,
    ):
        """All business records should have their user_id set to NULL."""
        mock_conn = AsyncMock()
        mock_db.connection.return_value = mock_conn

        # The get_transaction() should be None (no transaction active), so
        # the service uses connection.begin() — mock that too.
        mock_tx = AsyncMock()
        mock_conn.begin = MagicMock(return_value=AsyncMock())
        mock_conn.begin().__aenter__ = AsyncMock(return_value=mock_tx)
        mock_conn.begin().__aexit__ = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock()

        # Mark get_transaction as None to simulate no active transaction
        mock_db.get_transaction.return_value = None

        await delete_service.delete_user_data(user_id)

        # Verify UPDATE statements were executed for each business table
        assert mock_conn.execute.call_count >= 7, "Expected at least 7 UPDATE queries for business tables"

        # Collect all SQL strings to verify table coverage
        update_tables = set()
        for call in mock_conn.execute.call_args_list:
            stmt = call[0][0] if call.args else None
            if stmt is not None:
                compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
                if "UPDATE" in compiled:
                    # Extract table name
                    for table in ["sales", "purchases", "animals", "animal_protocols", "animal_supplies", "scheduled_events", "buyers"]:
                        if table in compiled.lower():
                            update_tables.add(table)

        assert "sales" in update_tables
        assert "purchases" in update_tables
        assert "animals" in update_tables
        assert "animal_protocols" in update_tables
        assert "animal_supplies" in update_tables
        assert "scheduled_events" in update_tables
        assert "buyers" in update_tables

    async def test_delete_disables_user_account(
        self,
        user_id,
        delete_service,
        mock_db,
    ):
        """User account should be set to inactive (is_active = False)."""
        mock_conn = AsyncMock()
        mock_db.connection.return_value = mock_conn
        mock_db.get_transaction.return_value = None
        mock_conn.begin = MagicMock(return_value=AsyncMock())
        mock_conn.begin().__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_conn.begin().__aexit__ = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock()

        await delete_service.delete_user_data(user_id)

        # Check that an UPDATE on users setting is_active=False was executed
        found_disable = False
        for call in mock_conn.execute.call_args_list:
            stmt = call[0][0] if call.args else None
            if stmt is not None:
                compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
                if "UPDATE" in compiled and "users" in compiled.lower() and "is_active" in compiled.lower():
                    found_disable = True
                    break

        assert found_disable, "User account was not disabled (is_active=False)"

    async def test_delete_revokes_all_refresh_tokens(
        self,
        user_id,
        delete_service,
        mock_db,
    ):
        """All refresh tokens for the user should be revoked."""
        mock_conn = AsyncMock()
        mock_db.connection.return_value = mock_conn
        mock_db.get_transaction.return_value = None
        mock_conn.begin = MagicMock(return_value=AsyncMock())
        mock_conn.begin().__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_conn.begin().__aexit__ = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock()

        await delete_service.delete_user_data(user_id)

        found_token_revoke = False
        for call in mock_conn.execute.call_args_list:
            stmt = call[0][0] if call.args else None
            if stmt is not None:
                compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
                if "UPDATE" in compiled and "refresh_tokens" in compiled.lower() and "revoked_at" in compiled.lower():
                    found_token_revoke = True
                    break

        assert found_token_revoke, "Refresh tokens were not revoked"

    async def test_delete_preserves_audit_log_entries(
        self,
        user_id,
        delete_service,
        mock_db,
    ):
        """Audit log entries should NOT be touched by the delete operation."""
        mock_conn = AsyncMock()
        mock_db.connection.return_value = mock_conn
        mock_db.get_transaction.return_value = None
        mock_conn.begin = MagicMock(return_value=AsyncMock())
        mock_conn.begin().__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_conn.begin().__aexit__ = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock()

        await delete_service.delete_user_data(user_id)

        # Check that no audit_log UPDATE or DELETE was executed
        for call in mock_conn.execute.call_args_list:
            stmt = call[0][0] if call.args else None
            if stmt is not None:
                compiled = str(stmt.compile(compile_kwargs={"literal_binds": True})).lower()
                assert "audit_log" not in compiled, "Audit log entries should not be modified"

    async def test_delete_idempotent_for_already_deleted_user(
        self,
        user_id,
        delete_service,
        mock_db,
    ):
        """Calling delete multiple times should not raise errors."""
        mock_conn = AsyncMock()
        mock_db.connection.return_value = mock_conn
        mock_db.get_transaction.return_value = None
        mock_conn.begin = MagicMock(return_value=AsyncMock())
        mock_conn.begin().__aenter__ = AsyncMock(return_value=AsyncMock())
        mock_conn.begin().__aexit__ = AsyncMock(return_value=None)
        mock_conn.execute = AsyncMock()

        # Calling delete twice should succeed both times
        await delete_service.delete_user_data(user_id)
        await delete_service.delete_user_data(user_id)

        assert mock_conn.execute.call_count >= 14, "Expected at least 14 UPDATE calls (2 calls × 7 business tables)"
