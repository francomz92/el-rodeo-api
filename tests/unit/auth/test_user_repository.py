"""Unit tests for UserRepository role mapping (now in _mappers.py).

The build_user() function in _mappers.py must correctly convert the
string 'role' column from the database into a UserRole enum value.
This test was previously testing UserRepository._build_user() directly;
it now tests the extracted standalone function.
"""

from unittest.mock import MagicMock

from src.auth.domain.entities._user_role import UserRole
from src.auth.infrastructure.persistence.repositories._mappers import build_user


class TestBuildUser:
    """build_user maps role string column to UserRole enum."""

    def test_viewer_string_mapped_to_viewer_enum(self) -> None:
        """role='viewer' in DB → UserRole.VIEWER."""
        user = build_user(_make_row(role="viewer"))
        assert user.role == UserRole.VIEWER

    def test_editor_string_mapped_to_editor_enum(self) -> None:
        """role='editor' in DB → UserRole.EDITOR."""
        user = build_user(_make_row(role="editor"))
        assert user.role == UserRole.EDITOR

    def test_admin_string_mapped_to_admin_enum(self) -> None:
        """role='admin' in DB → UserRole.ADMIN."""
        user = build_user(_make_row(role="admin"))
        assert user.role == UserRole.ADMIN

    def test_owner_string_mapped_to_owner_enum(self) -> None:
        """role='owner' in DB → UserRole.OWNER."""
        user = build_user(_make_row(role="owner"))
        assert user.role == UserRole.OWNER

    def test_empty_role_falls_back_to_viewer(self) -> None:
        """role=None or empty string → UserRole.VIEWER (safe fallback)."""
        user = build_user(_make_row(role=None))
        assert user.role == UserRole.VIEWER

    def test_all_user_fields_are_mapped_correctly(self) -> None:
        """All fields including role are correctly mapped from the DB row."""
        import uuid
        from datetime import datetime, timezone

        user_id = uuid.uuid4()
        tenant_id = uuid.uuid4()
        now = datetime.now(tz=timezone.utc)
        row = _make_row(
            id=user_id,
            name="John Doe",
            dni="12345678",
            email="john@example.com",
            role="admin",
            password="hashed_pwd_123",
            tenant_id=tenant_id,
            created_at=now,
        )
        user = build_user(row)

        assert user.id == user_id
        assert user.name == "John Doe"
        assert user.dni == "12345678"
        assert user.email == "john@example.com"
        assert user.role == UserRole.ADMIN
        assert user._hashed_password == "hashed_pwd_123"
        assert user.tenant_id == tenant_id
        assert user.created_at == now

    def test_super_admin_string_mapped_to_super_admin_enum(self) -> None:
        """role='super_admin' in DB → UserRole.SUPER_ADMIN."""
        user = build_user(_make_row(role="super_admin"))
        assert user.role == UserRole.SUPER_ADMIN


def _make_row(**overrides: object) -> MagicMock:
    """Build a mock RowMapping with realistic user DB columns."""
    import uuid
    from datetime import datetime, timezone

    defaults: dict[str, object] = {
        "id": uuid.uuid4(),
        "name": "Test User",
        "dni": "87654321",
        "email": "test@example.com",
        "role": "viewer",
        "password": "hashed_value",
        "tenant_id": None,
        "created_at": datetime.now(tz=timezone.utc),
    }
    defaults.update(overrides)
    row = MagicMock()
    row.__getitem__.side_effect = lambda k: defaults[k]  # type: ignore[arg-type]
    row.get.side_effect = lambda k, default=None: defaults.get(k, default)  # type: ignore[arg-type]
    return row
