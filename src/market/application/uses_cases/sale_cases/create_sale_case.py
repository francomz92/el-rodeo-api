from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.repositories.animals_repository_port import IAnimalsRepository
from src.cattle.domain.repositories.protocol_animals_repository_port import (
    IAnimalProtocolsRepository,
)
from src.common.application.ports.uow import IUoW
from src.market.domain.entities.sales import SaleEntity
from src.market.domain.repositories.sales import ISalesRepository
from src.market.domain.services.sale_services.create_sale_service import CreateSaleService
from src.market.domain.value_objects.sale_value_objects import SaleCreateValueObject


class CreateSaleCase:
    def __init__(self, uow: IUoW, service: CreateSaleService):
        self.uow = uow
        self.service = service

    async def execute(self, data: SaleCreateValueObject) -> SaleEntity:
        async with self.uow as uow:
            animal_repo = uow.get_repository(IAnimalsRepository)
            protocol_repo = uow.get_repository(IAnimalProtocolsRepository)
            repository = uow.get_repository(ISalesRepository)

            entity = await self.service.create_new(data, repository, animal_repo, protocol_repo)

            await animal_repo.update_status(data.animal_id, AnimalStatus.SOLD)

            await uow.commit()
            return entity
