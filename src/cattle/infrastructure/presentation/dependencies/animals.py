from typing import Annotated

from fastapi import Depends

from src.cattle.application.uses_cases.delete_animal_case import DeleteAnimalCase
from src.cattle.application.uses_cases.get_animal_case import ObtainAnimalCase
from src.cattle.application.uses_cases.list_animals_case import ListAnimalsCase
from src.cattle.application.uses_cases.register_animal_case import RegisterAnimalCase
from src.cattle.application.uses_cases.update_animal_case import UpdateAnimalCase
from src.common.infrastructure.presentation.dependencies.uow import GetUnitOfWork


def _get_register_animals_case(uow: GetUnitOfWork):
    return RegisterAnimalCase(uow=uow)


def _get_update_animal_case(uow: GetUnitOfWork):
    return UpdateAnimalCase(uow=uow)


def _get_delete_animal_case(uow: GetUnitOfWork):
    return DeleteAnimalCase(uow=uow)


def _get_list_animal_case(uow: GetUnitOfWork):
    return ListAnimalsCase(uow=uow)


def _get_obtain_animal_case(uow: GetUnitOfWork):
    return ObtainAnimalCase(uow=uow)


GetAnimalRegisterCase = Annotated[RegisterAnimalCase, Depends(_get_register_animals_case)]
GetAnimalUpdateCase = Annotated[UpdateAnimalCase, Depends(_get_update_animal_case)]
GetAnimalDeleteCase = Annotated[DeleteAnimalCase, Depends(_get_delete_animal_case)]
GetAnimalListCase = Annotated[ListAnimalsCase, Depends(_get_list_animal_case)]
GetObtainAnimalCase = Annotated[ObtainAnimalCase, Depends(_get_obtain_animal_case)]
