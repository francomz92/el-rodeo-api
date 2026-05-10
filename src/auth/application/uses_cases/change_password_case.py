from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.application.services.authentication_service import AuthService
from src.auth.domain.services.change_password_service import ChangePasswordService
from src.common.application.ports.uow import IUoW
from src.common.domain.services.security import ISecurityService


class ChangePasswordCase:
    def __init__(
        self,
        uow: IUoW,
        security_service: ISecurityService,
        auth_service: AuthService,
        change_password_service: ChangePasswordService,
    ) -> None:
        self.uow = uow
        self.security_service = security_service
        self.auth_service = auth_service
        self.change_password_service = change_password_service

    async def execute(
        self,
        token: str,
        password: str,
        new_password: str,
        confirmed_password: str,
    ):
        user = await self.auth_service.get_authenticated_user(self.uow, token)
        self.change_password_service.validate_passwords(user, password, self.security_service)
        async with self.uow as uow:
            repository = uow.get_repository(IUserRepository)
            await self.change_password_service.change_password(
                user=user,
                password=password,
                new_password=new_password,
                confirmed_password=confirmed_password,
                security_service=self.security_service,
                repository=repository,
            )
            await uow.commit()
