from src.auth.application.exceptions.authentication import InvalidCredentialError
from src.auth.application.ports.repositories.users import IUserRepository
from src.auth.application.services.authentication import AuthService
from src.auth.domain.entities import UserEntity
from src.common.application.ports.uow import IUoW
from src.common.domain.services.security import ISecurityService


class ChangePasswordCase:
    def __init__(
        self,
        uow: IUoW,
        security_service: ISecurityService,
        auth_service: AuthService,
    ) -> None:
        self.uow = uow
        self.security_service = security_service
        self.auth_service = auth_service

    async def execute(
        self,
        token: str,
        password: str,
        new_password: str,
        confirmed_password: str,
    ):
        user = await self.auth_service.get_authenticated_user(self.uow, token)
        if not user.passwords_match(self.security_service, password):
            raise InvalidCredentialError("Inválid credentials")
        user.validate_changed_password(password, new_password, confirmed_password)
        async with self.uow as uow:
            repository = uow.get_repository(IUserRepository)
            await repository.update_password(password)
            await uow.commit()
