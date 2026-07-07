"""Use case for listing users with admin-level access."""

from src.auth.domain.entities import UserEntity
from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotPermissionError
from src.common.infrastructure.adapters.http.output.cursor_page import encode_cursor


class ListUsersCase:
    """Lists users for the current tenant. Requires ADMIN or higher role."""

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(
        self,
        current_user: UserEntity,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        role: UserRole | None = None,
        cursor: str | None = None,
    ) -> tuple[list[UserEntity], int, str | None]:
        """List users in the current user's tenant.

        Args:
            current_user: The authenticated user (must be ADMIN/OWNER).
            page: Page number (1-indexed, ignored when cursor is provided).
            per_page: Items per page.
            search: Optional search string (matches name or email).
            role: Optional role filter.
            cursor: Optional cursor token for cursor-based pagination.

        Returns:
            Tuple of (list of UserEntity, total count, next_cursor).

        Raises:
            NotPermissionError: If the current user's role is below ADMIN.
        """
        if current_user.role.rank < UserRole.ADMIN.rank:
            raise NotPermissionError(
                "No tienes permisos suficientes para listar usuarios",
            )

        async with self.uow as uow:
            repo: IUserRepository = uow.get_repository(IUserRepository)
            assert current_user.tenant_id is not None
            items, total, has_next = await repo.list(
                tenant_id=current_user.tenant_id,
                page=page,
                per_page=per_page,
                search=search,
                role=role,
                cursor=cursor,
            )

        next_cursor: str | None = None
        if cursor is not None and has_next and items:
            last = items[-1]
            next_cursor = encode_cursor(str(last.id))

        return items, total, next_cursor
