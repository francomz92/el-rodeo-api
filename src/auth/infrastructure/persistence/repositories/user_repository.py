from datetime import datetime
from uuid import UUID

from sqlalchemy import exists, func, insert, literal, select, tuple_, update

from src.auth.domain.entities import UserEntity
from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.value_objects.user_value_object import (
    UserCreationValueObject,
    UserUpdateValueObject,
)
from src.auth.infrastructure.persistence.models import User
from src.common.application.pagination.cursor import cursor_uuid, decode_cursor
from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)

from .mappers import build_user, json_safe


class UserRepository(IUserRepository, TenantAwareRepository, AuditableRepositoryMixin):
    # Required by TenantAwareRepository ABC. This repository never calls _filter_tenant:
    # the identity layer is deliberately not tenant-scoped (login/register search users
    # across tenants before any tenant context exists).
    @property
    def _model(self) -> type:
        return User

    async def exists(self, dni: str, email: str) -> bool:
        query = (
            exists(User)
            .where(
                (User.dni == dni) | (User.email == email),
            )
            .select()
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(self, id: UUID) -> UserEntity | None:
        query = select(
            *User.__table__.columns,
        ).where(User.id == id)
        result = await self.db.execute(query)
        user_db = result.mappings().one_or_none()
        return build_user(user_db) if user_db else None

    async def get_by_dni(self, dni: str) -> UserEntity | None:
        query = select(
            *User.__table__.columns,
        ).where(User.dni == dni)
        result = await self.db.execute(query)
        user_db = result.mappings().one_or_none()
        return build_user(user_db) if user_db else None

    async def create(
        self,
        data: UserCreationValueObject,
        password: str,
    ) -> UserEntity:
        query = (
            insert(User)
            .values(
                **vars(data),
                password=password,
            )
            .returning(User.id)
        )
        result = await self.db.execute(query)
        user_id = result.scalar_one()
        new_entity = await self.get_by_id(user_id)
        self._audit_create("user", user_id, vars(data))
        return new_entity  # type: ignore

    async def update_data(self, id: UUID, data: UserUpdateValueObject) -> None:
        # Capture old values before update
        old_row = await self.db.execute(select(User.__table__).where(User.id == id))
        old_row_dict = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel}
        kws["updated_at"] = func.now()
        query = update(User).where(User.id == id).values(**kws)
        await self.db.execute(query)
        # Only include changed fields in audit, excluding SQL expressions
        changed_keys = {k for k in kws if k != "updated_at"}
        old_values = {k: json_safe(v) for k, v in old_row_dict.items() if k in changed_keys} if old_row_dict else None
        new_values = {k: json_safe(v) for k, v in kws.items() if k in changed_keys}
        self._audit_update("user", id, old_values or None, new_values or None)

    async def update_password(self, id: UUID, password: str) -> None:
        # Capture old values before update
        old_row = await self.db.execute(select(User.__table__).where(User.id == id))
        old_row_dict = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        old_values = {k: json_safe(v) for k, v in old_row_dict.items() if k == "password"} if old_row_dict else None
        query = (
            update(User)
            .where(User.id == id)
            .values(
                password=password,
                updated_at=func.now(),
            )
        )
        await self.db.execute(query)
        self._audit_update("user", id, old_values or None, {"password": "***"})

    async def update_role(self, id: UUID, role: UserRole) -> None:
        # Capture old values before update
        old_row = await self.db.execute(select(User.__table__).where(User.id == id))
        old_row_dict = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        old_values = {"role": json_safe(old_row_dict.get("role"))} if old_row_dict else None
        query = (
            update(User)
            .where(User.id == id)
            .values(
                role=role.value,
                updated_at=func.now(),
            )
        )
        await self.db.execute(query)
        self._audit_update("user", id, old_values or None, {"role": role.value})

    async def count_owners_by_tenant(self, tenant_id: UUID) -> int:
        query = (
            select(func.count())
            .select_from(User)
            .where(
                User.tenant_id == tenant_id,
                User.role == UserRole.OWNER.value,
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def list(
        self,
        tenant_id: UUID,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        role: UserRole | None = None,
        cursor: str | None = None,
        ids: list[UUID] | None = None,
    ) -> tuple[list[UserEntity], int, bool]:
        conditions = [User.tenant_id == tenant_id]

        if search:
            conditions.append(
                User.name.ilike(f"%{search}%") | User.email.ilike(f"%{search}%"),
            )
        if role:
            conditions.append(User.role == role.value)
        if ids:
            conditions.append(User.id.in_(ids))

        # Total count before pagination
        count_query = select(func.count()).select_from(User).where(*conditions)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Data query
        has_next = False
        if cursor is not None:
            if not cursor:
                return [], total, False
            cursor_data = decode_cursor(cursor)
            cursor_id = cursor_uuid(cursor_data)
            # Keyset pagination by registration date: the cursor's
            # sort_value carries the previous page's last-row created_at
            # (ISO 8601). Legacy/hand-crafted cursors default sort_value
            # to the id itself → fall back to the id-only keyset.
            try:
                cursor_created_at = datetime.fromisoformat(cursor_data["sort_value"])
            except ValueError:
                query = (
                    select(*User.__table__.columns)
                    .where(*conditions, User.id > cursor_id)
                    .order_by(User.id.asc())
                    .limit(per_page + 1)  # one extra to detect next page
                )
            else:
                query = (
                    select(*User.__table__.columns)
                    .where(*conditions, tuple_(User.created_at, User.id) > tuple_(literal(cursor_created_at), literal(cursor_id)))
                    .order_by(User.created_at.asc(), User.id.asc())
                    .limit(per_page + 1)  # one extra to detect next page
                )
        else:
            query = (
                select(*User.__table__.columns)
                .where(*conditions)
                .order_by(User.created_at.asc(), User.id.asc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )

        result = await self.db.execute(query)
        rows = result.mappings().all()

        if cursor is not None:
            if len(rows) > per_page:
                has_next = True
                rows = rows[:per_page]
        else:
            has_next = False

        return [build_user(row) for row in rows], total, has_next

    async def exists_by_email_excluding_user(self, email: str, exclude_user_id: UUID) -> bool:
        query = (
            exists(User)
            .where(
                User.email == email,
                User.id != exclude_user_id,
            )
            .select()
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id_with_tenant_check(self, user_id: UUID, tenant_id: UUID) -> UserEntity | None:
        query = select(*User.__table__.columns).where(
            User.id == user_id,
            User.tenant_id == tenant_id,
        )
        result = await self.db.execute(query)
        user_db = result.mappings().one_or_none()
        return build_user(user_db) if user_db else None
