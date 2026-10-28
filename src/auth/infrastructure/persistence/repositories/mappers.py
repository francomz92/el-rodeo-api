"""Mapper functions for UserRepository.

Extracted from user_repository.py to reduce file size (task 3.4 of
modularizacion-estructura).
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import RowMapping

from src.auth.domain.entities import UserEntity
from src.auth.domain.entities._user_role import UserRole


def build_user(user_db: RowMapping) -> UserEntity:
    """Build a UserEntity from a SQLAlchemy RowMapping."""
    return UserEntity(
        id=user_db["id"],
        name=user_db["name"],
        dni=user_db["dni"],
        email=user_db["email"],
        created_at=user_db["created_at"],
        role=UserRole(user_db["role"]) if user_db["role"] else UserRole.VIEWER,
        _hashed_password=user_db["password"],
        tenant_id=user_db.get("tenant_id"),
        is_active=user_db.get("is_active", True),
    )


def json_safe(value: object) -> object:
    """Convert non-JSON-serializable values to strings."""
    if isinstance(value, (UUID, datetime)):
        return str(value)
    return value
