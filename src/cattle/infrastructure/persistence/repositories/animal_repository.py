from uuid import UUID

from sqlalchemy import RowMapping, delete, exists, func, insert, select, update

from src.cattle.domain.constants.animal import AnimalStatus
from src.cattle.domain.entities.animal_entity import AnimalEntity, AnimalTypeEntity
from src.cattle.domain.repositories.animals_repository_port import (
    AnimalCreateValueObject,
    AnimalsListQueryParamsValueObject,
    AnimalUpdateValueObject,
    IAnimalsRepository,
)
from src.cattle.infrastructure.persistence.models import Animal, AnimalType
from src.common.domain.types import Sentinel
from src.common.infrastructure.adapters.http.output.cursor_page import decode_cursor
from src.common.infrastructure.persistence.repositories._auditable_mixin import (
    AuditableRepositoryMixin,
)
from src.common.infrastructure.persistence.repositories.tenant_aware_repository import (
    TenantAwareRepository,
)


class AnimalRepository(IAnimalsRepository, TenantAwareRepository, AuditableRepositoryMixin):
    _model: type[Animal] = Animal

    async def exists(
        self,
        id: UUID | None = None,
        type_id: UUID | None = None,
        caravana: str | None = None,
    ) -> bool:
        if not id and not all([type_id, caravana]):
            raise ValueError("Debe proporcionar un id o un conjunto de type_id y caravana para verificar la existencia")
        if not id:
            query = self._filter_tenant(
                exists(Animal).where(
                    Animal.caravana == caravana,
                    Animal.type_id == type_id,
                )
            )
        else:
            query = self._filter_tenant(exists(Animal).where(Animal.id == id))
        result = await self.db.execute(query.select())
        return result.scalar_one()

    async def get_by_id(
        self,
        id: UUID,
    ) -> AnimalEntity | None:
        query = self._filter_tenant(
            select(
                *Animal.__table__.columns,
                AnimalType.name.label("type_name"),
            )
            .where(Animal.id == id)
            .outerjoin(AnimalType, Animal.type_id == AnimalType.id)
        )
        result = await self.db.execute(query)
        animal_db = result.mappings().one_or_none()
        return self._build_animal_with_type(animal_db) if animal_db else None

    async def get_by_caravana(self, caravana: str) -> AnimalEntity | None:
        query = self._filter_tenant(
            select(
                *Animal.__table__.columns,
                AnimalType.name.label("type_name"),
            )
            .where(Animal.caravana == caravana)
            .outerjoin(AnimalType, Animal.type_id == AnimalType.id)
        )
        result = await self.db.execute(query)
        animal_db = result.mappings().one_or_none()
        return self._build_animal_with_type(animal_db) if animal_db else None

    async def list_for_user(
        self,
        filters: AnimalsListQueryParamsValueObject,
        limit: int,
        offset: int,
        order_by: str,
        cursor: str | None = None,
    ) -> tuple[list[AnimalEntity], int, bool]:
        conditions = []
        for k, v in vars(filters).items():
            if v is Sentinel.UNSET:
                continue
            elif k == "type_id":
                conditions.append(Animal.type_id == v)
            elif k in ("caravana", "breed"):
                conditions.append(getattr(Animal, k).icontains(v))

        base_columns = [
            *Animal.__table__.columns,
            AnimalType.name.label("type_name"),
        ]
        base_join = Animal.type_id == AnimalType.id

        # ── Count total (filter-wide, not cursor-sliced) ────────────
        count_query = self._filter_tenant(select(func.count()).select_from(Animal).outerjoin(AnimalType, base_join).where(*conditions))
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # ── Data query ───────────────────────────────────────────────
        has_next = False
        if cursor is not None:
            cursor_data = decode_cursor(cursor)
            cursor_id = UUID(cursor_data["id"])
            query = self._filter_tenant(
                select(*base_columns)
                .where(*conditions, Animal.id > cursor_id)
                .order_by(Animal.id.asc())
                .limit(limit + 1)  # fetch one extra to detect next page
                .outerjoin(AnimalType, base_join)
            )
        else:
            query = self._filter_tenant(
                select(*base_columns).where(*conditions).limit(limit).offset(offset).order_by(order_by).outerjoin(AnimalType, base_join)
            )

        result = await self.db.execute(query)
        animal_list_db = result.mappings().all()

        if cursor is not None:
            if len(animal_list_db) > limit:
                has_next = True
                animal_list_db = animal_list_db[:limit]
        else:
            # offset mode: only compute has_next if caller requested it
            has_next = False

        items = [self._build_animal_with_type(animal_data) for animal_data in animal_list_db]
        return items, total, has_next

    async def create(self, data: AnimalCreateValueObject) -> AnimalEntity:
        query = (
            insert(Animal)
            .values(
                **vars(data),
                tenant_id=self._tenant_id,
            )
            .returning(Animal.id)
        )
        result = await self.db.execute(query)
        animal_id = result.scalar_one()
        new_entity = await self.get_by_id(id=animal_id)
        self._audit_create(
            "animal",
            animal_id,
            vars(data),
            tenant_id=self._tenant_id,
        )
        return new_entity  # type: ignore[return-value]

    async def update_data(self, id: UUID, data: AnimalUpdateValueObject) -> AnimalEntity:
        # Capture old values before update
        old_row = await self.db.execute(self._filter_tenant(select(Animal.__table__).where(Animal.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        kws = {k: v for k, v in vars(data).items() if v is not Sentinel.UNSET}
        kws["updated_at"] = func.now()
        query = self._filter_tenant(update(Animal).where(Animal.id == id).values(**kws))
        await self.db.execute(query)
        new_entity = await self.get_by_id(id=id)
        self._audit_update("animal", id, old_values, vars(data))
        return new_entity  # type: ignore[return-value]

    async def update_status(self, id: UUID, status: AnimalStatus):
        old_row = await self.db.execute(self._filter_tenant(select(Animal.__table__).where(Animal.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        query = self._filter_tenant(
            update(Animal)
            .where(Animal.id == id)
            .values(
                status=status,
                updated_at=func.now(),
            )
        )
        await self.db.execute(query)
        self._audit_update("animal", id, old_values, {"status": status})

    async def delete(self, id: UUID) -> None:
        old_row = await self.db.execute(self._filter_tenant(select(Animal.__table__).where(Animal.id == id)))
        old_values = dict(old_row.mappings().one_or_none() or {}) if old_row else None
        query = self._filter_tenant(delete(Animal).where(Animal.id == id))
        await self.db.execute(query)
        self._audit_delete("animal", id, old_values)

    def _build_animal_with_type(self, animal_data: RowMapping) -> AnimalEntity:
        return AnimalEntity(
            id=animal_data["id"],
            tenant_id=animal_data["tenant_id"],
            caravana=animal_data["caravana"],
            tag=animal_data["tag"],
            date_of_birth=animal_data["date_of_birth"],
            initial_weight=animal_data["initial_weight"],
            initial_weight_date=animal_data["initial_weight_date"],
            last_weight=animal_data["last_weight"],
            breed=animal_data["breed"],
            status=animal_data["status"],
            type=AnimalTypeEntity(
                id=animal_data["type_id"],
                name=animal_data["type_name"],
            )
            if animal_data["type_id"]
            else None,
        )
