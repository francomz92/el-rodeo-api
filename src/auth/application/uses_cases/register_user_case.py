from src.auth.application.ports.tokens_port import ITokenService
from src.auth.application.services.notifications.wellcome_email_service import WellcomeEmailService
from src.auth.domain.entities import UserEntity
from src.auth.domain.repositories.users_repository_port import IUserRepository, UserCreationValueObject
from src.auth.domain.services.register_user_service import RegisterUserService
from src.common.application.ports.uow import IUoW
from src.common.domain.services.security import ISecurityService


class RegisterUserCase:
    def __init__(
        self,
        uow: IUoW,
        security_service: ISecurityService,
        register_service: RegisterUserService,
        notifier_service: WellcomeEmailService,
        token_service: ITokenService,
    ) -> None:
        self.uow = uow
        self.service = register_service
        self.security_service = security_service
        self.notifier_service = notifier_service
        self.token_service = token_service

    async def execute(
        self,
        data: UserCreationValueObject,
        requesting_user: UserEntity,
        redirect_url: str,
    ) -> UserEntity:
        self.service.validate_user_admin_permissions(user=requesting_user)
        async with self.uow as uow:
            repository = uow.get_repository(IUserRepository)
            await self.service.validate_duplicated(
                dni=data.dni,
                email=data.email,
                repository=repository,
            )
            user = await self.service.create_new(
                data=data,
                security_service=self.security_service,
                repository=repository,
            )
            await uow.commit()
            token = self.token_service.generate(
                data={"user_id": str(user.id)},
                exp_minutes=30,
            )
            self.notifier_service.send(
                to=[user.email],
                subject="Bienvenido a El Rodeo",
                redirect_url=f"{redirect_url}?token={token}",
            )
        return user
