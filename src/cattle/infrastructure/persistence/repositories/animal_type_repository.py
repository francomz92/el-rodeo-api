from uuid import UUID

from sqlalchemy import RowMapping, exists, func, insert, select, update

from src.cattle.domain.entities.animal_entity import AnimalTypeEntity
from src.cattle.domain.repositories.animal_type_repository_port import IAnimalTypesRepository
from src.cattle.domain.value_objects.animal_type_value_object import (
    AnimalTypeCreateValueObject,
    AnimalTypeListQueryParamsValueObject,
    AnimalTypeUpdateValueObject,
)
from src.cattle.infrastructure.persistence.models import AnimalType
from src.common.domain.types import Sentinel
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)


class AnimalTypeRepository(IAnimalTypesRepository, TenantAwareRepository, AuditableRepositoryMixin):
    @property
    def _model(self) -> type:
        return AnimalType

    async def exists(self, id: UUID) -> bool:
        query = exists(AnimalType).where(AnimalType.id == id).select()
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_by_id(self, id: UUID) -> AnimalTypeEntity | None:
        query = select(
            AnimalType.id,
            AnimalType.name,
        ).where(AnimalType.id == id)
        result = await self.db.execute(query)
        animal_type_db = result.mappings().one_or_none()
        return self._build_animal_type(animal_type_db) if animal_type_db else None

    async def list(
        self,
        filters: AnimalTypeListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
    ) -> list[AnimalTypeEntity]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k == "id":
                conditions.append(AnimalType.id == v)
            elif k == "name":
                conditions.append(AnimalType.name.icontains(v))
        query = (
            select(
                AnimalType.id,
                AnimalType.name,
            )
            .where(
                *conditions,
            )
            .limit(limit)
            .offset(offset)
            .order_by(order_by)
        )
        result = await self.db.execute(query)
        animal_types_list = result.mappings().all()
        return [self._build_animal_type(type_data) for type_data in animal_types_list]

    async def create(
        self,
        data: AnimalTypeCreateValueObject,
    ) -> AnimalTypeEntity:
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        query = insert(AnimalType).values(**kws).returning(AnimalType.id)
        result = await self.db.execute(query)
        animal_type_id = result.scalar_one()
        entity = await self.get_by_id(animal_type_id)
        self._audit_create("animal_type", animal_type_id, kws)
        return entity  # type: ignore

    async def update(
        self,
        id: UUID,
        data: AnimalTypeUpdateValueObject,
    ) -> AnimalTypeEntity:
        old_row = await self.db.execute(select(AnimalType.__table__).where(AnimalType.id == id))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        kws["updated_at"] = func.now()
        query = (
            update(AnimalType)
            .where(
                AnimalType.id == id,
            )
            .values(**kws)
            .returning(AnimalType.id)
        )
        result = await self.db.execute(query)
        animal_type_id = result.scalar_one_or_none()
        entity = await self.get_by_id(animal_type_id)  # type: ignore
        self._audit_update("animal_type", id, old_values, kws)
        return entity  # type: ignore

    def _build_animal_type(self, type_data: RowMapping) -> AnimalTypeEntity:
        return AnimalTypeEntity(
            id=type_data["id"],
            name=type_data["name"],
        )
