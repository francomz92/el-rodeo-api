from uuid import UUID

from sqlalchemy import delete, exists, func, insert, select, update

from src.cattle.domain.entities.animal_protocol_entity import AnimalProtocolEntity
from src.cattle.domain.repositories.protocol_animals_repository_port import IAnimalProtocolsRepository
from src.cattle.domain.value_objects.animal_protocol_value_object import (
    AnimalProtocolCreateValueObject,
    AnimalProtocolListQueryParamsValueObject,
    AnimalProtocolUpdateValueObject,
)
from src.cattle.infrastructure.persistence.models import Animal, AnimalProtocols, AnimalType
from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)

from .mappers import build_animal_protocol


class AnimalProtocolsRepository(IAnimalProtocolsRepository, TenantAwareRepository, AuditableRepositoryMixin):
    _model: type[AnimalProtocols] = AnimalProtocols

    async def exists(self, id: UUID) -> bool:
        query = self._filter_tenant(exists(AnimalProtocols).where(AnimalProtocols.id == id).select())
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
    ) -> AnimalProtocolEntity | None:
        query = self._filter_tenant(
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
            .where(AnimalProtocols.id == id)
            .outerjoin(Animal, AnimalProtocols.animal_id == Animal.id)
            .outerjoin(AnimalType, Animal.type_id == AnimalType.id)
        )
        result = await self.db.execute(query)
        protocol = result.mappings().one_or_none()
        return build_animal_protocol(protocol) if protocol else None

    async def get_by_animal_id(self, animal_id: UUID) -> AnimalProtocolEntity | None:
        query = self._filter_tenant(
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
            .where(AnimalProtocols.animal_id == animal_id)
            .outerjoin(Animal, AnimalProtocols.animal_id == Animal.id)
            .outerjoin(AnimalType, Animal.type_id == AnimalType.id)
        )
        result = await self.db.execute(query)
        protocol = result.mappings().one_or_none()
        return build_animal_protocol(protocol) if protocol else None

    async def list_for_user(
        self,
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
        query = self._filter_tenant(
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
            .where(*conditions)
            .order_by(order_by)
            .limit(limit)
            .offset(offset)
            .outerjoin(Animal, AnimalProtocols.animal_id == Animal.id)
            .outerjoin(AnimalType, Animal.type_id == AnimalType.id)
        )
        result = await self.db.execute(query)
        protocols = result.mappings().all()
        return [build_animal_protocol(protocol) for protocol in protocols]

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
                tenant_id=self._tenant_id,
            )
            .returning(AnimalProtocols.id)
        )
        result = await self.db.execute(query)
        protocol_id = result.scalar_one()
        entity = await self.get_by_id(protocol_id)
        self._audit_create(
            "animal_protocol",
            protocol_id,
            vars(data),
            tenant_id=self._tenant_id,
            user_id=user_id,
        )
        return entity  # type: ignore

    async def update_data(
        self,
        id: UUID,
        data: AnimalProtocolUpdateValueObject,
    ) -> AnimalProtocolEntity:
        old_row = await self.db.execute(self._filter_tenant(select(AnimalProtocols.__table__).where(AnimalProtocols.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET and k != "user_id"}
        kws["updated_at"] = func.now()
        query = self._filter_tenant(update(AnimalProtocols).where(AnimalProtocols.id == id).values(**kws))
        await self.db.execute(query)
        entity = await self.get_by_id(id)
        self._audit_update("animal_protocol", id, old_values, vars(data))
        return entity  # type: ignore

    async def delete(self, id: UUID) -> None:
        old_row = await self.db.execute(self._filter_tenant(select(AnimalProtocols.__table__).where(AnimalProtocols.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        query = self._filter_tenant(delete(AnimalProtocols).where(AnimalProtocols.id == id))
        await self.db.execute(query)
        self._audit_delete("animal_protocol", id, old_values)
