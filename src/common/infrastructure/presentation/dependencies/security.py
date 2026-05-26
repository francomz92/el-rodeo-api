from typing import Annotated

from fastapi import Depends

from src.common.domain.services.security import ISecurityService
from src.common.infrastructure.adapters.security.hashers import SecurityService


def _get_security_service():
    return SecurityService()


GetSecurityService = Annotated[ISecurityService, Depends(_get_security_service)]
