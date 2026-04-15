from src.auth.application.exceptions.authentication import InvalidCredentialError
from src.auth.application.ports.repositories.users import IUserRepository
from src.auth.application.ports.tokens import ITokenService
from src.common.application.exceptions import ResourceNotFoundError
from src.common.application.ports.uow import IUoW
from src.common.domain.services.security import ISecurityService


class LoginUserCase:
    def __init__(self, uow: IUoW, security_service: ISecurityService, token_service: ITokenService) -> None:
        self.uow = uow
        self.security_service = security_service
        self.token_service = token_service

    async def execute(self, dni: str, password: str) -> str:
        async with self.uow as uow:
            repository = uow.get_repository(IUserRepository)
            user = await repository.get_by_dni(dni)
            if not user:
                raise ResourceNotFoundError(f'El usuario con DNI "{dni}" no se encuentra registrado')
            passwords_match = user.passwords_match(self.security_service, password)
            if not passwords_match:
                raise InvalidCredentialError("Las credenciales proporcionadas no son válidas")
            expire_time = 60 * 24  # 24 hs
            return self.token_service.generate({"user_id": user.id}, expire_time)
