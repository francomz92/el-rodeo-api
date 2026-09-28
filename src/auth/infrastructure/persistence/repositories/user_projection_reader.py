from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.infrastructure.persistence.models import User
from src.finance.domain.repositories.user_reader_port import IUserNameReader


class UserProjectionReader(IUserNameReader):
    def __init__(self, session: AsyncSession) -> None:
        self.db = session

    async def get_names_by_ids(self, user_ids: set[UUID]) -> dict[UUID, str]:
        if not user_ids:
            return {}

        stmt = select(User.id, User.name).where(User.id.in_(user_ids))
        result = await self.db.execute(stmt)
        rows = result.mappings().all()
        return {row["id"]: row["name"] for row in rows}
