from src.auth.domain.entities import UserEntity
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.common.domain.exceptions import UnauthorizedError
from src.common.domain.services.security import ISecurityService


class ChangePasswordService:
    async def validate_passwords(
        self,
        user: UserEntity,
        password: str,
        security_service: ISecurityService,
    ):
        password_matches = await user.passwords_match(security_service, password)
        if not password_matches:
            raise UnauthorizedError("Las credenciales proporcionadas no son válidas")

    async def change_password(
        self,
        user: UserEntity,
        password: str,
        new_password: str,
        confirmed_password: str,
        security_service: ISecurityService,
        repository: IUserRepository,
    ):
        await user.update_password(
            security_service,
            password,
            new_password,
            confirmed_password,
        )
        await repository.update_password(user.id, user.hashed_password)
