from uuid import UUID

from sqlalchemy import RowMapping, delete, exists, insert, select, update

from src.cattle.domain.entities.animal_entity import AnimalEntity, AnimalTypeEntity
from src.cattle.domain.entities.animal_protocol_entity import AnimalProtocolEntity
from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.cattle.domain.value_objects.animal_protocol_value_object import (
    AnimalProtocolCreateValueObject,
    AnimalProtocolListQueryParamsValueObject,
    AnimalProtocolUpdateValueObject,
)
from src.cattle.infrastructure.persistence.models import AnimalType
from src.cattle.infrastructure.persistence.models._animal_models import Animal, AnimalProtocols
from src.common.domain.types import Sentinel
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
            select(
                *AnimalProtocols.__table__.columns,
                Animal.id.label("animal_id"),
                Animal.date_of_birth.label("animal_date_of_birth"),
                Animal.initial_weight.label("animal_initial_weight"),
                Animal.status.label("animal_status"),
                Animal.breed.label("animal_breed"),
                Animal.caravana.label("animal_caravana"),
                Animal.initial_weight_date.label("animal_initial_weight_date"),
                Animal.last_weight.label("animal_last_weight"),
                Animal.tag.label("animal_tag"),
                AnimalType.id.label("animal_type_id"),
                AnimalType.name.label("animal_type_name"),
            )
            .where(
                AnimalProtocols.id == id,
                AnimalProtocols.user_id == user_id,
            )
            .outerjoin(Animal, AnimalProtocols.animal_id == Animal.id)
            .outerjoin(AnimalType, Animal.type_id == AnimalType.id)
            # .options(
            #     joinedload(AnimalProtocols.animal).joinedload(Animal.type),
            # )
        )
        result = await self.db.execute(query)
        protocol = result.mappings().one_or_none()
        return self._build_animal_protocol_entity(protocol) if protocol else None

    async def list_for_user(
        self,
        user_id: UUID,
        filters: AnimalProtocolListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalProtocolEntity]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k in ("id", "vaccinated", "sale_permission"):
                conditions.append(getattr(AnimalProtocols, k) == v)
        query = (
            select(
                *AnimalProtocols.__table__.columns,
                Animal.date_of_birth.label("animal_date_of_birth"),
                Animal.initial_weight.label("animal_initial_weight"),
                Animal.status.label("animal_status"),
                Animal.breed.label("animal_breed"),
                Animal.caravana.label("animal_caravana"),
                Animal.initial_weight_date.label("animal_initial_weight_date"),
                Animal.last_weight.label("animal_last_weight"),
                Animal.tag.label("animal_tag"),
                AnimalType.id.label("animal_type_id"),
                AnimalType.name.label("animal_type_name"),
            )
            .where(
                AnimalProtocols.user_id == user_id,
                *conditions,
            )
            .order_by(order_by)
            .limit(limit)
            .offset(offset)
            .outerjoin(Animal, AnimalProtocols.animal_id == Animal.id)
            .outerjoin(AnimalType, Animal.type_id == AnimalType.id)
            # .options(
            #     joinedload(AnimalProtocols.animal).joinedload(Animal.type),
            # )
        )
        result = await self.db.execute(query)
        protocols = result.mappings().all()
        return [self._build_animal_protocol_entity(protocol) for protocol in protocols]

    async def create(
        self,
        user_id: UUID,
        data: AnimalProtocolCreateValueObject,
    ) -> AnimalProtocolEntity:
        query = (
            insert(AnimalProtocols)
            .values(
                user_id=user_id,
                **vars(data),
            )
            .returning(AnimalProtocols.id)
        )
        result = await self.db.execute(query)
        protocol_id = result.scalar_one()
        return await self.get_by_id(protocol_id, user_id)  # type: ignore

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
        return await self.get_by_id(id, data.user_id)  # type: ignore

    async def delete(self, id: UUID) -> None:
        query = delete(AnimalProtocols).where(AnimalProtocols.id == id)
        await self.db.execute(query)

    def _build_animal_protocol_entity(self, protocol: RowMapping) -> AnimalProtocolEntity:
        animal_type = (
            AnimalTypeEntity(
                id=protocol["animal_type_id"],
                name=protocol["animal_type_name"],
            )
            if protocol["animal_type_id"]
            else None
        )
        return AnimalProtocolEntity(
            id=protocol["id"],
            animal=AnimalEntity(
                id=protocol["animal_id"],
                date_of_birth=protocol["animal_date_of_birth"],
                initial_weight=protocol["animal_initial_weight"],
                type=animal_type,
                status=protocol["animal_status"],
                breed=protocol["animal_breed"],
                caravana=protocol["animal_caravana"],
                initial_weight_date=protocol["animal_initial_weight_date"],
                last_weight=protocol["animal_last_weight"],
                tag=protocol["animal_tag"],
            ),
            vaccinated=protocol["vaccinated"],
            vaccinated_date=protocol["vaccinated_date"],
            sale_permission=protocol["sale_permission"],
            sale_permission_date=protocol["sale_permission_date"],
        )
