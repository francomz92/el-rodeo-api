from typing import Annotated

from fastapi import Depends

from src.cattle.application.uses_cases.register_animal import RegisterAnimalCase
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_register_animals_case(uow: GetUnitOfWork):
    return RegisterAnimalCase(uow=uow)

GetAnimalsCase = Annotated[RegisterAnimalCase, Depends(_get_register_animals_case)]