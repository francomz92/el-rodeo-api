from src.auth.infrastructure.persistence.repositories._registry import (
    repositories_list as auth_repos,
)
from src.billing.infrastructure.persistence.repositories._registry import (
    repositories_list as billing_repos,
)
from src.calendar.infrastructure.persistence.repositories._registry import (
    repositories_list as calendar_repos,
)
from src.cattle.infrastructure.persistence.repositories._registry import (
    repositories_list as cattle_repos,
)
from src.common.application.ports.audit_log_query_port import IAuditLogQueryRepository
from src.common.application.ports.gdpr_delete_port import IGDPRDeleteRepository
from src.common.domain.repositories.webhook_subscription_repository_port import (
    IWebhookSubscriptionRepository,
)
from src.common.domain.repository import IRepository
from src.common.infrastructure.persistence.repositories.audit_log_query_repository import (
    AuditLogQueryRepository,
)
from src.common.infrastructure.persistence.repositories.gdpr_delete_repository import (
    GDPRDeleteRepository,
)
from src.common.infrastructure.persistence.repositories.webhook_subscription_repository import (
    WebhookSubscriptionRepository,
)
from src.finance.infrastructure.persistence.repositories._registry import (
    repositories_list as finance_repos,
)
from src.market.infrastructure.persistence.repositories._registry import (
    repositories_list as market_repos,
)


def _merge_registries(
    *registries: dict[type[IRepository], type[IRepository]],
) -> dict[type[IRepository], type[IRepository]]:
    """Merge multiple repository registries, failing early on duplicate keys."""
    result: dict[type[IRepository], type[IRepository]] = {}
    for registry in registries:
        duplicates = set(result.keys()) & set(registry.keys())
        if duplicates:
            raise ValueError(f"Duplicate repository interface keys across contexts: {duplicates}")
        result.update(registry)
    return result


repositories_list: dict[type[IRepository], type[IRepository]] = {
    IAuditLogQueryRepository: AuditLogQueryRepository,
    IGDPRDeleteRepository: GDPRDeleteRepository,
    IWebhookSubscriptionRepository: WebhookSubscriptionRepository,
}
repositories_list.update(
    _merge_registries(
        auth_repos,
        cattle_repos,
        market_repos,
        finance_repos,
        billing_repos,
        calendar_repos,
    )
)
