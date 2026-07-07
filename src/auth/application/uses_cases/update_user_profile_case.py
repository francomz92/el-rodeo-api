"""Use case for updating the current user's profile."""

from src.auth.domain.entities import UserEntity
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.value_objects.user_value_object import UserUpdateValueObject
from src.common.application.ports.uow import IUoW
from src.common.domain.exceptions import ConflictError


class UpdateUserProfileCase:
    """Updates the current user's name and/or email."""

    def __init__(self, uow: IUoW) -> None:
        self.uow = uow

    async def execute(
        self,
        current_user: UserEntity,
        name: str | None = None,
        email: str | None = None,
    ) -> UserEntity:
        """Update the current user's profile.

        Validates email uniqueness (excluding self) before updating.

        Args:
            current_user: The authenticated user.
            name: Optional new name.
            email: Optional new email.

        Returns:
            The updated UserEntity.

        Raises:
            ConflictError: If the email is already taken by another user.
        """
        async with self.uow as uow:
            repo: IUserRepository = uow.get_repository(IUserRepository)

            if email and email != current_user.email:
                exists = await repo.exists_by_email_excluding_user(
                    email,
                    current_user.id,
                )
                if exists:
                    raise ConflictError(
                        "El email ya está en uso por otro usuario",
                    )

            update_data = UserUpdateValueObject()
            if name is not None:
                update_data.name = name
            if email is not None:
                update_data.email = email

            await repo.update_data(current_user.id, update_data)
            await uow.commit()

            # Return updated user from repo
            updated = await repo.get_by_id(current_user.id)
            if updated is None:
                msg = f"Usuario con ID '{current_user.id}' no encontrado después de actualizar"
                raise ValueError(msg)
            return updated
