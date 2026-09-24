"""Use case for inviting a user to an existing tenant.

Guarded by require_role(ADMIN) at the router level.
No tenant creation, no event dispatch.
"""

from src.auth.application.ports.tokens_port import ITokenService
from src.auth.domain.entities import UserEntity
from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.events.user_registered import UserRegistered
from src.auth.domain.repositories.tenant_repository_port import ITenantRepository
from src.auth.domain.repositories.users_repository_port import (
    IUserRepository,
    UserCreationValueObject,
)
from src.auth.domain.services.register_user_service import RegisterUserService
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import NotPermissionError
from src.common.domain.ports.event_bus import IEventBus
from src.common.domain.services.security import ISecurityService


class InviteUserCase:
    """Invite a user to an existing tenant with role ≤ inviter's rank."""

    def __init__(
        self,
        uow: IUoW,
        security_service: ISecurityService,
        register_service: RegisterUserService,
        token_service: ITokenService,
        event_bus: IEventBus,
    ) -> None:
        self.uow = uow
        self.service = register_service
        self.security_service = security_service
        self.token_service = token_service
        self.event_bus = event_bus

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
            tenant_repo = uow.get_repository(ITenantRepository)
            user = await user_repo.get_by_dni(dni)
            if not user:
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
                user, _ = await self.service.create_new(data=data, repository=user_repo)

            # Generate an invite token (no password in URL).
            token = self.token_service.generate(
                data={
                    "user_id": str(user.id),
                    "tenant_id": str(inviter.tenant_id),
                },
                exp_minutes=30,
            )
            tenant = await tenant_repo.get_by_id(inviter.tenant_id)
            tenant_name = tenant.name if tenant else "El Rodeo"

            user_invited = UserRegistered(
                aggregate_id=user.id,
                metadata={
                    "title": f"Has sido invitado a {tenant_name}",
                    "emails": [user.email],
                    "body": f"Ha sido invitado a {tenant_name}. Haz clic en el siguiente enlace para acceder: {redirect_url}{'&' if '?' in redirect_url else '?'}token={token}",
                },
            )
            uow.add_outbox_event(user_invited)
            await uow.commit()
        await self.event_bus.dispatch(user_invited)
        return user
