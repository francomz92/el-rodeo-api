from uuid import UUID

from src.auth.application.ports.token_blacklist_port import ITokenBlacklistService
from src.auth.application.ports.tokens_port import ITokenService
from src.auth.domain.entities import UserEntity
from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import UnauthorizedError


class AuthService:
    def __init__(
        self,
        token_service: ITokenService,
        blacklist_service: ITokenBlacklistService,
    ) -> None:
        self.token_service = token_service
        self.blacklist_service = blacklist_service

    async def get_authenticated_user(self, uow: IUoW, token: str) -> UserEntity:
        payload = self.token_service.decode(token)

        jti = payload.get("jti")
        if jti is not None and await self.blacklist_service.is_blacklisted(jti):
            raise UnauthorizedError("No autorizado para realizar esta acción")

        # Set tenant context from JWT payload for downstream use cases
        tid = payload.get("tenant_id")
        uow.tenant_id = UUID(tid) if tid else None

        async with uow as _uow:
            repository = _uow.get_repository(IUserRepository)
            user = await repository.get_by_id(payload["user_id"])
            if not user:
                raise UnauthorizedError("No autorizado para realizar esta acción")
            # Activate cross-tenant super-admin access for SUPER_ADMIN users only
            _uow.bypass_filter = user.role == UserRole.SUPER_ADMIN
        return user
