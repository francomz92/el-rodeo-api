from src.auth.application.ports.dtos.user_dtos import UserCreationDTO
from src.auth.domain.entities import UserEntity
from src.common.application.exceptions import AlreadyExistsError, NotPermissionError
from src.auth.application.ports.repositories.users_repository_port import IUserRepository
from src.common.application.ports.uow import IUoW
from src.common.domain.services.security import ISecurityService


class RegisterUserCase:
    def __init__(self, uow: IUoW, security_service: ISecurityService) -> None:
        self.uow = uow
        self.security_service = security_service

    async def execute(self, data: UserCreationDTO, requesting_user: UserEntity) -> UserEntity:
        if not requesting_user.is_admin:
            raise NotPermissionError("No tiene permisos para realizar esta acción")
        async with self.uow as uow:
            repository = uow.get_repository(IUserRepository)
            user = await repository.get_by_dni(data.dni)
            if user:
                raise AlreadyExistsError("Este usuario ya se encuentra registrado")
            random_password = self.security_service.generate_random_str(10)
            random_hashed_password = self.security_service.hash_password(random_password)
            user = await repository.create(data=data, password=random_hashed_password)
            await uow.commit()
        return user
