from src.auth.domain.entities import UserEntity
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.common.domain.exceptions import DuplicatedError, NotPermissionError
from src.common.domain.services.security import ISecurityService


class RegisterUserService:
    def validate_user_admin_permissions(self, user: UserEntity) -> None:
        if not user.is_admin:
            raise NotPermissionError("No tiene permisos para realizar esta acción")

    async def validate_user_dni_uniqueness(
        self,
        dni: str,
        repository: IUserRepository,
    ) -> None:
        user = await repository.exists(dni=dni)
        if user:
            raise DuplicatedError("Este usuario ya se encuentra registrado")

    async def create_new(
        self,
        data,
        security_service: ISecurityService,
        repository: IUserRepository,
    ) -> UserEntity:
        random_password = security_service.generate_random_str(10)
        random_hashed_password = security_service.hash_password(random_password)
        return await repository.create(
            data=data,
            password=random_hashed_password,
        )
