from abc import abstractmethod
from uuid import UUID

from src.auth.domain.entities import UserEntity
from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.value_objects.user_value_object import (
    UserCreationValueObject,
    UserUpdateValueObject,
)
from src.common.domain.repository import IRepository


class IUserRepository(IRepository):
    @abstractmethod
    async def exists(self, dni: str, email: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, id: UUID) -> UserEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_dni(self, dni: str) -> UserEntity | None:
        raise NotImplementedError

    @abstractmethod
    async def create(self, data: UserCreationValueObject, password: str) -> UserEntity:
        raise NotImplementedError

    @abstractmethod
    async def update_data(self, id: UUID, data: UserUpdateValueObject) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_password(self, id: UUID, password: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_role(self, id: UUID, role: UserRole) -> None:
        """Update the role for a given user."""
        raise NotImplementedError

    @abstractmethod
    async def count_owners_by_tenant(self, tenant_id: UUID) -> int:
        """Count users with role OWNER for a given tenant."""
        raise NotImplementedError

    @abstractmethod
    async def list(
        self,
        tenant_id: UUID,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        role: UserRole | None = None,
        cursor: str | None = None,
    ) -> tuple[list[UserEntity], int, bool]:
        """List users for a tenant with pagination, optional search and role filter.

        When *cursor* is provided, cursor-based pagination is used
        (``WHERE id > :cursor_id ORDER BY id ASC``) and *page*/*per_page*
        are ignored in favour of *per_page* (limit).
        When *cursor* is ``None``, the legacy page/per_page pagination is used.

        Returns ``(items, total_count, has_next)``.
        """
        raise NotImplementedError

    @abstractmethod
    async def exists_by_email_excluding_user(self, email: str, exclude_user_id: UUID) -> bool:
        """Check if email exists for a user other than the one being updated."""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id_with_tenant_check(self, user_id: UUID, tenant_id: UUID) -> UserEntity | None:
        """Get a user by ID, returning None if the user is not in the given tenant."""
        raise NotImplementedError
