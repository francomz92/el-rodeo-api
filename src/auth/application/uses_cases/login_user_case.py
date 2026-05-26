from src.auth.application.ports.tokens_port import ITokenService
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.services.login_user_service import LoginUserService
from src.common.application.ports.uow import IUoW
from src.common.domain.services.security import ISecurityService


class LoginUserCase:
    def __init__(
        self,
        uow: IUoW,
        security_service: ISecurityService,
        token_service: ITokenService,
        login_service: LoginUserService,
    ) -> None:
        self.uow = uow
        self.security_service = security_service
        self.token_service = token_service
        self.login_service = login_service

    async def execute(self, dni: str, password: str) -> str:
        async with self.uow as uow:
            repository = uow.get_repository(IUserRepository)
            user = await self.login_service.validate_duplicate_and_get_user(dni, repository)
            await self.login_service.validate_credentials(user, password, self.security_service)
            expire_time = 60 * 24  # ? 24 hs
            return self.token_service.generate({"user_id": str(user.id)}, expire_time)
