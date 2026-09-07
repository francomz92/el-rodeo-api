from uuid import UUID

from sqlalchemy import RowMapping, func, insert, select, update

from src.auth.domain.entities import RefreshTokenEntity
from src.auth.domain.repositories.refresh_token_repository_port import (
    IRefreshTokenRepository,
)
from src.auth.infrastructure.persistence.models import RefreshToken
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)
from src.common.utils.date_utils import get_current_datetime


class RefreshTokenRepository(IRefreshTokenRepository, TenantAwareRepository, AuditableRepositoryMixin):
    # Required by TenantAwareRepository ABC; filtering is a no-op at tenant_id=None.
    @property
    def _model(self) -> type:
        return RefreshToken

    async def save(self, token: RefreshTokenEntity) -> None:
        """Persist a new refresh token."""
        stmt = insert(RefreshToken).values(
            id=token.id,
            user_id=token.user_id,
            token_hash=token.token_hash,
            family_id=token.family_id,
            expires_at=token.expires_at,
            created_at=token.created_at,
        )
        await self.db.execute(stmt)
        self._audit_create(
            "refresh_token",
            token.id,
            {
                "user_id": str(token.user_id),
                "family_id": str(token.family_id),
            },
        )

    async def find_by_id(self, token_id: UUID) -> RefreshTokenEntity | None:
        """Look up a token by its primary key."""
        stmt = select(
            RefreshToken.id,
            RefreshToken.user_id,
            RefreshToken.token_hash,
            RefreshToken.family_id,
            RefreshToken.expires_at,
            RefreshToken.revoked_at,
            RefreshToken.created_at,
        ).where(RefreshToken.id == token_id)
        result = await self.db.execute(stmt)
        row = result.mappings().one_or_none()
        return self._build_entity(row) if row else None

    async def find_by_token_hash(self, token_hash: str) -> RefreshTokenEntity | None:
        """Look up a token by its bcrypt hash."""
        stmt = select(
            RefreshToken.id,
            RefreshToken.user_id,
            RefreshToken.token_hash,
            RefreshToken.family_id,
            RefreshToken.expires_at,
            RefreshToken.revoked_at,
            RefreshToken.created_at,
        ).where(RefreshToken.token_hash == token_hash)
        result = await self.db.execute(stmt)
        row = result.mappings().one_or_none()
        return self._build_entity(row) if row else None

    async def find_by_family(self, family_id: UUID) -> list[RefreshTokenEntity]:
        """Return all tokens in a family (active + revoked)."""
        stmt = select(
            RefreshToken.id,
            RefreshToken.user_id,
            RefreshToken.token_hash,
            RefreshToken.family_id,
            RefreshToken.expires_at,
            RefreshToken.revoked_at,
            RefreshToken.created_at,
        ).where(RefreshToken.family_id == family_id)
        result = await self.db.execute(stmt)
        rows = result.mappings().all()
        return [self._build_entity(row) for row in rows]

    async def revoke_token(self, token: RefreshTokenEntity) -> None:
        """Revoke a single token by setting its revoked_at timestamp."""

        # Capture old values before update
        old_values = vars(token)
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.id == token.id)
            .values(
                revoked_at=get_current_datetime(),
                updated_at=func.now(),
            )
        )
        await self.db.execute(stmt)
        self._audit_update("refresh_token", token.id, old_values, {"revoked_at": "now"})

    async def revoke_family(self, family_id: UUID) -> None:
        """Revoke every token in a family (reuse detection scenario)."""
        # Capture old values before update
        old_rows = await self.db.execute(
            select(RefreshToken.__table__)
            .where(
                RefreshToken.family_id == family_id,
                RefreshToken.revoked_at.is_(None),
            )
            .with_for_update()
        )
        old_tokens = old_rows.mappings().all()
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(
                revoked_at=get_current_datetime(),
                updated_at=func.now(),
            )
        )
        await self.db.execute(stmt)
        for t in old_tokens:
            self._audit_update(
                "refresh_token",
                t["id"],
                dict(t),
                {"revoked_at": "now"},
            )

    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        """Revoke every active refresh token belonging to a user."""
        # Capture old values before update
        old_rows = await self.db.execute(
            select(RefreshToken.__table__)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
            .with_for_update()
        )
        old_tokens = old_rows.mappings().all()
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .where(RefreshToken.revoked_at.is_(None))
            .values(
                revoked_at=get_current_datetime(),
                updated_at=func.now(),
            )
        )
        await self.db.execute(stmt)
        for t in old_tokens:
            self._audit_update(
                "refresh_token",
                t["id"],
                dict(t),
                {"revoked_at": "now"},
            )

    @staticmethod
    def _build_entity(row: RowMapping) -> RefreshTokenEntity:
        """Convert a DB row into a domain entity.

        The database uses revoked_at (datetime | None) while the domain
        uses is_revoked (bool). A non-NULL revoked_at means revoked.
        """
        return RefreshTokenEntity(
            id=row["id"],
            user_id=row["user_id"],
            token_hash=row["token_hash"],
            family_id=row["family_id"],
            expires_at=row["expires_at"],
            is_revoked=row["revoked_at"] is not None,
            created_at=row["created_at"],
        )
