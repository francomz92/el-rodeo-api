from datetime import timedelta
from uuid import UUID

from src.auth.application.ports.tokens_port import ITokenService
from src.auth.domain.entities import RefreshTokenEntity
from src.auth.domain.repositories.refresh_token_repository_port import (
    IRefreshTokenRepository,
)
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.services.login_user_service import LoginUserService
from src.common.application.ports.uow import IUoW
from src.common.domain.services.security import ISecurityService
from src.common.infrastructure.core import settings
from src.common.utils.date_utils import get_current_datetime


class LoginUserCase:
    def __init__(
        self,
        uow: IUoW,
        security_service: ISecurityService,
        token_service: ITokenService,
        login_service: LoginUserService,
    ) -> None:
        self.uow = uow
        self.security_service = security_service
        self.token_service = token_service
        self.login_service = login_service

    async def execute(self, dni: str, password: str) -> tuple[str, str]:
        """Authenticate user and return (access_token, refresh_token) pair.

        Validates credentials, generates both tokens, and persists the
        refresh token in the database for rotation support.
        """
        async with self.uow as uow:
            repository = uow.get_repository(IUserRepository)
            user = await self.login_service.validate_duplicate_and_get_user(dni, repository)
            await self.login_service.validate_credentials(user, password, self.security_service)

            # Generate access token (15 min) with tenant context
            access_token = self.token_service.generate(
                {
                    "user_id": str(user.id),
                    "tenant_id": str(user.tenant_id) if user.tenant_id else None,
                },
                exp_minutes=15,
            )

            # Generate refresh token (7 days) with tenant context
            refresh_token_raw = self.token_service.generate_refresh_token(
                user_id=str(user.id),
                tenant_id=str(user.tenant_id) if user.tenant_id else None,
            )

            # Decode refresh token to get its claims for DB persistence
            refresh_payload = self.token_service.decode_refresh_token(refresh_token_raw)
            refresh_token_id_str: str = refresh_payload.get("refresh_token_id", refresh_payload["jti"])

            # Persist refresh token entity in DB
            refresh_repo = uow.get_repository(IRefreshTokenRepository)
            entity = RefreshTokenEntity(
                id=UUID(refresh_token_id_str),
                user_id=user.id,
                token_hash=refresh_token_id_str,  # use token ID as unique hash (ID-based lookup)
                family_id=UUID(refresh_payload["family_id"]),
                expires_at=get_current_datetime() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
                is_revoked=False,
            )
            await refresh_repo.save(entity)
            await uow.commit()

            return access_token, refresh_token_raw
