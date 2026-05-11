from uuid import UUID

from sqlalchemy import delete, exists, insert, select, update
from sqlalchemy.orm import joinedload

from src.cattle.domain.entities.animal_entity import AnimalEntity, AnimalTypeEntinty
from src.cattle.domain.entities.animal_protocol_entity import AnimalProtocolEntity
from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.cattle.domain.value_objects.animal_protocol_value_object import (
    AnimalProtocolCreateValueObject,
    AnimalProtocolListQueryParamsValueObject,
    AnimalProtocolUpdateValueObject,
)
from src.cattle.infrastructure.persistance.models._animal_models import AnimalProtocols
from src.common.application.types import Sentinel
from src.common.infrastructure.persistence.repositories.mixins import SessionMixin


class AnimalProtocolsRepository(IAnimalProtocolsRepository, SessionMixin):
    async def exists(self, id: UUID, user_id: UUID) -> bool:
        query = (
            exists(AnimalProtocols)
            .where(
                AnimalProtocols.id == id,
                AnimalProtocols.user_id == user_id,
            )
            .select()
        )
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
        user_id: UUID,
    ) -> AnimalProtocolEntity | None:
        query = (
            select(AnimalProtocols)
            .where(
                AnimalProtocols.id == id,
                AnimalProtocols.user_id == user_id,
            )
            .options(
                joinedload(AnimalProtocols.animal),
            )
        )
        result = await self.db.execute(query)
        protocol = result.scalar_one_or_none()
        return self._build_animal_protocol_entity(protocol) if protocol else None

    async def list_for_user(
        self,
        user_id: UUID,
        filters: AnimalProtocolListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalProtocolEntity]:
        kws = {k: v for k, v in vars(filters).items() if v is not Sentinel.UNSET}
        query = (
            select(AnimalProtocols)
            .where(AnimalProtocols.user_id == user_id)
            .filter_by(**kws)
            .order_by(order_by)
            .limit(limit)
            .offset(offset)
            .options(
                joinedload(AnimalProtocols.animal),
            )
        )
        result = await self.db.execute(query)
        protocols = result.scalars().unique().all()
        return [self._build_animal_protocol_entity(protocol) for protocol in protocols]

    async def create(
        self,
        user_id: UUID,
        data: AnimalProtocolCreateValueObject,
    ) -> AnimalProtocolEntity:
        query = (
            insert(AnimalProtocols)
            .values(
                **vars(data),
            )
            .returning(AnimalProtocols.id)
        )
        result = await self.db.execute(query)
        protocol_id = result.scalar_one()
        return self.get_by_id(protocol_id, user_id)  # type: ignore

    async def update_data(
        self,
        id: UUID,
        data: AnimalProtocolUpdateValueObject,
    ) -> AnimalProtocolEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = (
            update(AnimalProtocols)
            .where(
                AnimalProtocols.id == id,
            )
            .values(**kws)
        )
        await self.db.execute(query)
        return self.get_by_id(id, data.user_id)  # type: ignore

    async def delete(self, id: UUID) -> None:
        query = delete(AnimalProtocols).where(AnimalProtocols.id == id)
        await self.db.execute(query)

    def _build_animal_protocol_entity(
        self,
        protocol: AnimalProtocols,
    ) -> AnimalProtocolEntity:
        return AnimalProtocolEntity(
            id=protocol.id,
            animal=AnimalEntity(
                id=protocol.animal.id,
                name=protocol.animal.name,
                date_of_birth=protocol.animal.date_of_birth,
                initial_weight=protocol.animal.initial_weight,
                type=AnimalTypeEntinty(
                    id=protocol.animal.type.id,
                    name=protocol.animal.type.name,
                ),
                status=protocol.animal.status,
                breed=protocol.animal.breed,
                caravana=protocol.animal.caravana,
                initial_weight_date=protocol.animal.initial_weight_date,
                last_weight=protocol.animal.last_weight,
                tag=protocol.animal.tag,
            ),
            vaccinated=protocol.vaccinated,
            vaccinated_date=protocol.vaccinated_date,
            sale_permission=protocol.sale_permission,
            sale_permission_date=protocol.sale_permission_date,
        )
