from src.auth.application.ports.tokens_port import ITokenService
from src.auth.application.services.notifications.wellcome_email_service import (
    WellcomeEmailService,
)
from src.auth.domain.entities import UserEntity
from src.auth.domain.repositories.tenant_repository_port import ITenantRepository
from src.auth.domain.repositories.users_repository_port import (
    IUserRepository,
    UserCreationValueObject,
)
from src.auth.domain.services.register_user_service import RegisterUserService
from src.billing.application.services._trial_management_service import (
    TrialManagementService,
)
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import DuplicatedError
from src.common.domain.services.security import ISecurityService


def _slugify(name: str) -> str:
    """Generate a URL-safe slug from an organization name.

    Lowercases, replaces spaces/special chars with hyphens,
    collapses multiple hyphens, and strips leading/trailing ones.
    """
    import re

    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug if slug else "org"


class RegisterUserCase:
    def __init__(
        self,
        uow: IUoW,
        security_service: ISecurityService,
        register_service: RegisterUserService,
        notifier_service: WellcomeEmailService,
        token_service: ITokenService,
        trial_service: TrialManagementService | None = None,
    ) -> None:
        self.uow = uow
        self.service = register_service
        self.security_service = security_service
        self.notifier_service = notifier_service
        self.token_service = token_service
        self.trial_service = trial_service

    async def execute(
        self,
        data: UserCreationValueObject,
        redirect_url: str,
    ) -> UserEntity:
        async with self.uow as uow:
            user_repo = uow.get_repository(IUserRepository)
            await self.service.validate_duplicated(
                dni=data.dni,
                email=data.email,
                repository=user_repo,
            )

            # 1. Create the tenant first
            tenant_repo = uow.get_repository(ITenantRepository)
            slug = _slugify(data.name)
            existing = await tenant_repo.get_by_slug(slug)
            if existing:
                raise DuplicatedError(f"Ya existe una organización con el nombre '{data.name}'")
            tenant = await tenant_repo.create(name=data.name, slug=slug)

            # 2. Start trial subscription (if trial service configured)
            if self.trial_service is not None:
                await self.trial_service.start_trial(tenant.id)

            # 3. Create the user with the tenant_id
            data.tenant_id = tenant.id
            user, password = await self.service.create_new(
                data=data,
                security_service=self.security_service,
                repository=user_repo,
            )

            # 4. Generate welcome token with tenant context
            token = self.token_service.generate(
                data={
                    "user_id": str(user.id),
                    "tenant_id": str(tenant.id),
                },
                exp_minutes=30,
            )
            self.notifier_service.send(
                to=[user.email],
                subject="Bienvenido a El Rodeo",
                redirect_url=f"{redirect_url}?token={token}",
                password=password,
            )
            await uow.commit()
        return user
