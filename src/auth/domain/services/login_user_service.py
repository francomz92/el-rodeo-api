from src.auth.domain.entities import UserEntity
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.common.domain.exceptions import UnauthorizedError
from src.common.domain.services.security import ISecurityService


class LoginUserService:
    async def validate_duplicate_and_get_user(
        self,
        dni: str,
        repository: IUserRepository,
    ) -> UserEntity:
        user = await repository.get_by_dni(dni)
        if not user:
            raise UnauthorizedError("Las credenciales proporcionadas no son válidas")
        return user

    async def validate_credentials(
        self,
        user: UserEntity,
        password: str,
        security_service: ISecurityService,
    ) -> None:
        if not user.is_active:
            raise UnauthorizedError("Las credenciales proporcionadas no son válidas")
        passwords_match = await user.passwords_match(security_service, password)
        if not passwords_match:
            raise UnauthorizedError("Las credenciales proporcionadas no son válidas")
