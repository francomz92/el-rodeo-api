"""Mapper functions for AnimalRepository.

Extracted from animal_repository.py to reduce file size (task 3.5 of
modularizacion-estructura).
"""

from sqlalchemy import RowMapping

from src.cattle.domain.entities.animal_entity import AnimalEntity, AnimalTypeEntity


def build_animal_with_type(animal_data: RowMapping) -> AnimalEntity:
    """Build an AnimalEntity with its AnimalType from a SQLAlchemy RowMapping.

    The mapping is expected to contain columns from Animal and AnimalType
    tables via outer join.
    """
    return AnimalEntity(
        id=animal_data["id"],
        tenant_id=animal_data["tenant_id"],
        user_id=animal_data["user_id"],
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
