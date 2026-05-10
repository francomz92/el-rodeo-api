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
    ) -> None:
        self.uow = uow
        self.security_service = security_service
        self.service = register_service

    async def execute(self, data: UserCreationValueObject, requesting_user: UserEntity) -> UserEntity:
        self.service.validate_user_admin_permissions(user=requesting_user)
        async with self.uow as uow:
            repository = uow.get_repository(IUserRepository)
            await self.service.validate_user_dni_uniqueness(dni=data.dni, repository=repository)
            user = await self.service.create_new(data, self.security_service, repository)
            await uow.commit()
        return user
