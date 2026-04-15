from src.auth.application.exceptions.authentication import UnauthorizedError
from src.auth.application.ports.repositories.users import IUserRepository
from src.auth.application.ports.tokens import ITokenService
from src.auth.domain.entities import UserEntity
from src.common.application.ports.uow import IUoW


class AuthService:
    def __init__(self, token_service: ITokenService) -> None:
        self.token_service = token_service

    async def get_authenticated_user(self, uow: IUoW, token: str) -> UserEntity:
        payload = self.token_service.decode(token)
        async with uow as _uow:
            repository = _uow.get_repository(IUserRepository)
            user = await repository.get_by_id(payload["user_id"])
            if not user:
                raise UnauthorizedError("No autorizado para realizar esta acción")
        return user
