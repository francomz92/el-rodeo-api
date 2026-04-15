from typing import Annotated

from fastapi import Depends

from src.cattle.application.uses_cases.register_animal import RegisterAnimalCase
from src.cattle.application.uses_cases.update_animal_data import UpdateAnimalCase
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_register_animals_case(uow: GetUnitOfWork):
    return RegisterAnimalCase(uow=uow)


def _get_update_animal_case(uow: GetUnitOfWork):
    return UpdateAnimalCase(uow=uow)


GetAnimalRegisterCase = Annotated[RegisterAnimalCase, Depends(_get_register_animals_case)]
GetAnimalUpdateCase = Annotated[UpdateAnimalCase, Depends(_get_update_animal_case)]
