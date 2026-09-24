"""Use case for creating a tenant with an OWNER user.

Guarded by require_role(SUPER_ADMIN) at the router level.
Trial subscription is created inline (ACID) rather than via an event handler.
"""

from __future__ import annotations

from src.auth.application.ports.tokens_port import ITokenService
from src.auth.domain.entities import UserEntity
from src.auth.domain.entities._user_role import UserRole
from src.auth.domain.events.tenant_registered import TenantRegistered
from src.auth.domain.repositories.tenant_repository_port import ITenantRepository
from src.auth.domain.repositories.users_repository_port import (
    IUserRepository,
    UserCreationValueObject,
)
from src.auth.domain.services.register_user_service import RegisterUserService
from src.billing.application.services._trial_management_service import (
    TrialManagementService,  # noqa: intentional cross-module dependency — refactor to public interface
)
from src.billing.domain.entities import PlanTypeEntity
from src.billing.domain.repositories import IPlanRepository, ISubscriptionRepository
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import DuplicatedError
from src.common.domain.ports.event_bus import IEventBus
from src.common.domain.services.security import ISecurityService


class CreateTenantCase:
    """Create a tenant with its first user as OWNER and provision trial subscription."""

    def __init__(
        self,
        uow: IUoW,
        security_service: ISecurityService,
        register_service: RegisterUserService,
        event_bus: IEventBus,
        token_service: ITokenService,
        trial_service: TrialManagementService,
    ) -> None:
        self.uow = uow
        self.service = register_service
        self.security_service = security_service
        self.event_bus = event_bus
        self.token_service = token_service
        self.trial_service = trial_service

    async def execute(
        self,
        tenant_name: str,
        slug: str,
        name: str,
        dni: str,
        email: str,
        redirect_url: str,
    ) -> UserEntity:
        async with self.uow as uow:
            user_repo = uow.get_repository(IUserRepository)
            await self.service.validate_duplicated(
                dni=dni,
                email=email,
                repository=user_repo,
            )

            # Create the tenant with the provided slug
            tenant_repo = uow.get_repository(ITenantRepository)
            existing = await tenant_repo.get_by_slug(slug)
            if existing:
                raise DuplicatedError(f"Ya existe una organización con el slug '{slug}'")
            tenant = await tenant_repo.create(name=tenant_name, slug=slug)

            # Create the first user as OWNER
            data = UserCreationValueObject(
                name=name,
                dni=dni,
                email=email,
                role=UserRole.OWNER,
                tenant_id=tenant.id,
            )
            user, password = await self.service.create_new(
                data=data,
                repository=user_repo,
            )

            # Provision trial subscription BEFORE commit, so the whole
            # operation (tenant + user + trial) is ACID — if anything
            # fails, nothing is persisted.
            plan_repository = uow.get_repository(IPlanRepository)
            subscription_repository = uow.get_repository(ISubscriptionRepository)
            await self.trial_service.start_trial(tenant.id, plan_repository, subscription_repository, PlanTypeEntity.FREE)

            # credentials for an account that wasn't persisted.
            token = self.token_service.generate(
                data={
                    "user_id": str(user.id),
                    "tenant_id": str(tenant.id),
                },
                exp_minutes=30,
            )

            tenant_registered = TenantRegistered(
                aggregate_id=tenant.id,
                metadata={
                    "title": "Bienvenido a El Rodeo",
                    "emails": [user.email],
                    "body": f"Bienvenido a El Rodeo. Haz clic en el siguiente enlace para acceder: {redirect_url}{'&' if '?' in redirect_url else '?'}token={token}",
                },
            )
            uow.add_outbox_event(tenant_registered)
            await uow.commit()
        self.event_bus.dispatch(tenant_registered)
        return user
