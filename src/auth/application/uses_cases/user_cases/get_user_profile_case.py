"""Use case for retrieving the current user's profile."""

from src.auth.domain.entities import UserEntity


class GetUserProfileCase:
    """Returns the current authenticated user as-is."""

    async def execute(self, current_user: UserEntity) -> UserEntity:
        """Return the current user unchanged."""
        return current_user
