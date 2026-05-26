from src.auth.domain.entities import UserEntity
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.common.domain.exceptions import DuplicatedError
from src.common.domain.services.security import ISecurityService


class RegisterUserService:
    async def validate_duplicated(
        self,
        dni: str,
        email: str,
        repository: IUserRepository,
    ) -> None:
        user = await repository.exists(dni=dni, email=email)
        if user:
            raise DuplicatedError("Este usuario ya se encuentra registrado")

    async def create_new(
        self,
        data,
        security_service: ISecurityService,
        repository: IUserRepository,
    ) -> tuple[UserEntity, str]:
        random_password = security_service.generate_random_str(10)
        random_hashed_password = security_service.hash_password(random_password)
        user = await repository.create(
            data=data,
            password=random_hashed_password,
        )
        return user, random_password
