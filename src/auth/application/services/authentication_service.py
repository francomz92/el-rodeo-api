from src.auth.application.ports.token_blacklist_port import ITokenBlacklistService
from src.auth.application.ports.tokens_port import ITokenService
from src.auth.domain.entities import UserEntity
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotPermissionError, UnauthorizedError


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

        async with uow as _uow:
            repository = _uow.get_repository(IUserRepository)
            user = await repository.get_by_id(payload["user_id"])
            if not user:
                raise UnauthorizedError("No autorizado para realizar esta acción")
        return user

    def validate_admin_user(self, user: UserEntity) -> None:
        if not user.is_admin:
            raise NotPermissionError("No tiene permisos para realizar esta acción")
