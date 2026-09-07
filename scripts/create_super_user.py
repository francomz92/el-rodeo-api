import asyncio
import sys
from pathlib import Path

from src.auth.domain.entities import UserRole
from src.auth.domain.repositories.users_repository_port import IUserRepository
from src.auth.domain.value_objects.user_value_object import UserCreationValueObject
from src.common.infrastructure.adapters.security.hashers import SecurityService
from src.common.infrastructure.persistence.connections.db import AsyncSessionMaker
from src.common.infrastructure.persistence.uow import UnitOfWork

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))


async def main() -> None:
    if len(sys.argv) != 5:
        print("Usage: python create_super_user.py <name> <dni> <email> <password>")
        sys.exit(1)

    name = sys.argv[1]
    dni = sys.argv[2]
    email = sys.argv[3]
    password = sys.argv[4]

    async with UnitOfWork(AsyncSessionMaker()) as uow:
        security_service = SecurityService()
        repository = uow.get_repository(IUserRepository)

        data = UserCreationValueObject(
            name=name,
            dni=dni,
            email=email,
            role=UserRole.SUPER_ADMIN,
            tenant_id=None,
        )
        hashed_password = await security_service.hash_password(password)
        await repository.create(data=data, password=hashed_password)
        await uow.commit()


if __name__ == "__main__":
    asyncio.run(main())
