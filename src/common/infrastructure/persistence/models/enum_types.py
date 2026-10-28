"""Shared native-PG-enum column configuration.

Repo-wide enum convention (backend-conventions-parity S6, L3): every enum
column is a native PostgreSQL enum whose LABELS are the domain enum VALUES
(lowercase, human-readable). This matches the pre-existing
``calendareventtype``/``animaleventtype`` types and the API boundary, where
pydantic already serializes enums by value.
"""

from enum import Enum

from sqlalchemy import Enum as SQLEnum


def values_enum(enum_cls: type[Enum], *, name: str | None = None) -> SQLEnum:
    """Return a native PG enum type storing the enum's lowercase values.

    ``name`` defaults to the enum class name in lowercase (e.g.
    ``AnimalStatus`` -> ``animalstatus``): SQLAlchemy does NOT auto-name
    enums that use ``values_callable``, and the derived name matches the
    type names the existing migrations already created.
    """
    return SQLEnum(
        enum_cls,
        values_callable=lambda cls: [member.value for member in cls],
        native_enum=True,
        name=name or enum_cls.__name__.lower(),
    )
