from src.auth.domain.repositories.refresh_token_repository_port import (
    IRefreshTokenRepository,
)
from src.auth.domain.repositories.tenant_repository_port import ITenantRepository
from src.auth.domain.repositories.users_repository_port import (
    IUserRepository,
)
from src.auth.infrastructure.persistence.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from src.auth.infrastructure.persistence.repositories.tenant_repository import (
    TenantRepository,
)
from src.auth.infrastructure.persistence.repositories.user_repository import (
    UserRepository,
)
from src.common.domain.repository import IRepository

repositories_list: dict[type[IRepository], type[IRepository]] = {
    IRefreshTokenRepository: RefreshTokenRepository,
    ITenantRepository: TenantRepository,
    IUserRepository: UserRepository,
}
