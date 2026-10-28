"""Row-to-entity builders for the cattle repositories."""

from sqlalchemy import RowMapping

from src.cattle.domain.entities.animal_entity import AnimalEntity, AnimalTypeEntity
from src.cattle.domain.entities.animal_protocol_entity import AnimalProtocolEntity


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


def build_animal_type(type_data: RowMapping) -> AnimalTypeEntity:
    """Build an AnimalTypeEntity from a SQLAlchemy RowMapping."""
    return AnimalTypeEntity(
        id=type_data["id"],
        name=type_data["name"],
    )


def build_animal_protocol(protocol: RowMapping) -> AnimalProtocolEntity:
    """Build an AnimalProtocolEntity from an animal-protocol row mapping.

    The mapping is expected to contain columns from AnimalProtocols plus the
    outer-joined Animal and AnimalType columns.
    """
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
        tenant_id=protocol["tenant_id"],
        animal=AnimalEntity(
            id=protocol["animal_id"],
            tenant_id=protocol["tenant_id"],
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
