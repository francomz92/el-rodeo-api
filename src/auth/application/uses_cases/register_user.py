from src.common.application.exceptions import AlreadyExistsError
from src.auth.application.ports.repositories.users import IUserRepository
from src.common.application.ports.uow import IUoW
from src.common.domain.services.security import ISecurityService


class RegisterUserCase:
    def __init__(self, uow: IUoW, security_service: ISecurityService) -> None:
        self.uow = uow
        self.security_service = security_service

    async def execute(self, dni: str) -> None:
        async with self.uow as uow:
            repository = uow.get_repository(IUserRepository)
            user = await repository.get_by_dni(dni)
            if user:
                raise AlreadyExistsError("Este usuario ya se encuentra registrado")
            random_password = self.security_service.generate_random_str(10)
            random_hashed_password = self.security_service.hash_password(random_password)
            await repository.create(dni=dni, hashed_password=random_hashed_password)
            await uow.commit()
