"""Use case for inviting a user to an existing tenant.

Guarded by require_role(ADMIN) at the router level.
No tenant creation, no event dispatch.
"""

from src.auth.application.ports.tokens_port import ITokenService
from src.auth.application.services.notifications.wellcome_email_service import (
    WellcomeEmailService,
)
from src.auth.domain.entities import UserEntity
from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.repositories.users_repository_port import (
    IUserRepository,
    UserCreationValueObject,
)
from src.auth.domain.services.register_user_service import RegisterUserService
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotPermissionError
from src.common.domain.services.security import ISecurityService


class InviteUserCase:
    """Invite a user to an existing tenant with role ≤ inviter's rank."""

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
        inviter: UserEntity,
        name: str,
        dni: str,
        email: str,
        role: UserRole,
        redirect_url: str,
    ) -> UserEntity:
        # Cross-tenant assertion: inviter must belong to a tenant
        if inviter.tenant_id is None:
            raise NotPermissionError("El usuario invitador no pertenece a un tenant")

        # Role-rank check: invitee's role rank must ≤ inviter's role rank
        if role.rank > inviter.role.rank:
            raise NotPermissionError(f"No tienes permisos para invitar con rol '{role.value}'")

        async with self.uow as uow:
            user_repo = uow.get_repository(IUserRepository)
            await self.service.validate_duplicated(
                dni=dni,
                email=email,
                repository=user_repo,
            )

            data = UserCreationValueObject(
                name=name,
                dni=dni,
                email=email,
                role=role,
                tenant_id=inviter.tenant_id,
            )
            user, _ = await self.service.create_new(
                data=data,
                security_service=self.security_service,
                repository=user_repo,
            )

            # Generate an invite token (no password in URL).
            token = self.token_service.generate(
                data={
                    "user_id": str(user.id),
                    "tenant_id": str(inviter.tenant_id),
                },
                exp_minutes=30,
            )
            await uow.commit()

            # Send email only AFTER successful commit.
            await self.notifier_service.send(
                to=[user.email],
                subject="Has sido invitado a El Rodeo",
                redirect_url=f"{redirect_url}{'&' if '?' in redirect_url else '?'}token={token}",
            )

        return user
