from src.auth.domain.entities import UserEntity
from src.auth.domain.repositories.refresh_token_repository_port import (
    IRefreshTokenRepository,
)
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.services.change_password_service import ChangePasswordService
from src.common.application.ports.uow import IUoW
from src.common.domain.services.security import ISecurityService


class ChangePasswordCase:
    def __init__(
        self,
        uow: IUoW,
        security_service: ISecurityService,
        change_password_service: ChangePasswordService,
    ) -> None:
        self.uow = uow
        self.security_service = security_service
        self.change_password_service = change_password_service

    async def execute(
        self,
        user: UserEntity,
        password: str,
        new_password: str,
        confirmed_password: str,
    ) -> None:
        """Change a user's password and revoke all their refresh tokens.

        The authenticated user is resolved by the auth dependency and
        passed in directly — no token parameter required.

        Args:
            user: The authenticated user entity.
            password: The user's current password.
            new_password: The new password to set.
            confirmed_password: New password confirmation.

        Raises:
            UnauthorizedError: If the current password is invalid.
        """
        await self.change_password_service.validate_passwords(user, password, self.security_service)
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

            # Revoke all refresh tokens for security (forces re-login)
            refresh_repo = uow.get_repository(IRefreshTokenRepository)
            await refresh_repo.revoke_all_user_tokens(user.id)
