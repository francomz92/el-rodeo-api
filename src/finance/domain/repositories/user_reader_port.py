from abc import abstractmethod
from uuid import UUID

from src.common.domain.repository import IRepository


class IUserNameReader(IRepository):
    @abstractmethod
    async def get_names_by_ids(self, user_ids: set[UUID]) -> dict[UUID, str]:
        """Retrieve names for the requested users in one batch."""
        raise NotImplementedError
