"""Unify enum strategy: native PG enums with value labels everywhere.

Backend-conventions-parity S6 (odd/tasks/backend-conventions-parity.md L3).
Before this revision three variants coexisted:

- native PG enums storing member NAMES as labels: ``animalstatus``
  (READY/NOT_READY/SOLD), ``purchasestatus`` (PENDING/CONFIRMED),
  ``unitofmeasurement`` (KILOGRAMS/...);
- native PG enums storing member VALUES as labels (the target convention):
  ``calendareventtype``, ``animaleventtype``;
- plain VARCHAR storing values: billing's status/plan_type columns.

After it every enum column is a native PG enum whose labels are the domain
enum VALUES. Cattle/finance labels are case-rewritten (API-invisible: the
domain and the HTTP layer already speak values); billing columns are
promoted from VARCHAR to enum with byte-identical labels (no rewrite).
"""

from typing import Sequence, Union

from alembic import op

revision: str = "6e2e88a276fe"
down_revision: Union[str, None] = "dbde2e447abe"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_ANIMAL_STATUS_MAP = {
    "READY": "disponible",
    "NOT_READY": "no_disponible",
    "SOLD": "vendido",
}
_PURCHASE_STATUS_MAP = {
    "PENDING": "pending",
    "CONFIRMED": "confirmed",
}
_UNIT_MAP = {
    "KILOGRAMS": "kg",
    "GRAMS": "gr",
    "UNIT": "unidades",
    "METERS": "mts",
    "CENTIMETERS": "cm",
    "LITERS": "lts",
    "MILILITERS": "ml",
    "CUBIC_CENTIMETERS": "cc",
}


def _case_rewrite_sql(table: str, column: str, mapping: dict[str, str]) -> str:
    whens = " ".join(f"WHEN '{k}' THEN '{v}'" for k, v in mapping.items())
    return f"UPDATE {table} SET {column} = CASE {column} {whens} END"


def upgrade() -> None:
    """Convert name-labeled enums to value labels; promote billing to native."""
    # -- cattle: animalstatus (labels = names -> values) -----------------------
    op.execute("ALTER TABLE animals ALTER COLUMN status TYPE varchar USING status::text")
    op.execute(_case_rewrite_sql("animals", "status", _ANIMAL_STATUS_MAP))
    op.execute("DROP TYPE animalstatus")
    op.execute("CREATE TYPE animalstatus AS ENUM ('disponible', 'no_disponible', 'vendido')")
    op.execute("ALTER TABLE animals ALTER COLUMN status TYPE animalstatus USING status::text::animalstatus")

    # -- finance: purchasestatus + unitofmeasurement (shared by two tables) ----
    # The column default references the type; drop it before the swap.
    op.execute("ALTER TABLE purchases ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE purchases ALTER COLUMN status TYPE varchar USING status::text")
    op.execute("ALTER TABLE purchases ALTER COLUMN unit_of_measurement TYPE varchar USING unit_of_measurement::text")
    op.execute("ALTER TABLE animal_supplies ALTER COLUMN unit_of_measurement TYPE varchar USING unit_of_measurement::text")
    op.execute(_case_rewrite_sql("purchases", "status", _PURCHASE_STATUS_MAP))
    op.execute(_case_rewrite_sql("purchases", "unit_of_measurement", _UNIT_MAP))
    op.execute(_case_rewrite_sql("animal_supplies", "unit_of_measurement", _UNIT_MAP))
    op.execute("DROP TYPE purchasestatus")
    op.execute("DROP TYPE unitofmeasurement")
    op.execute("CREATE TYPE purchasestatus AS ENUM ('pending', 'confirmed')")
    op.execute("CREATE TYPE unitofmeasurement AS ENUM ('kg', 'gr', 'unidades', 'mts', 'cm', 'lts', 'ml', 'cc')")
    op.execute("ALTER TABLE purchases ALTER COLUMN status TYPE purchasestatus USING status::text::purchasestatus")
    op.execute("ALTER TABLE purchases ALTER COLUMN status SET DEFAULT 'pending'::purchasestatus")
    op.execute(
        "ALTER TABLE purchases ALTER COLUMN unit_of_measurement TYPE unitofmeasurement USING unit_of_measurement::text::unitofmeasurement"
    )
    op.execute(
        "ALTER TABLE animal_supplies ALTER COLUMN unit_of_measurement TYPE unitofmeasurement "
        "USING unit_of_measurement::text::unitofmeasurement"
    )

    # -- billing: VARCHAR values -> native enums with identical labels ----------
    op.execute("CREATE TYPE subscriptionstatus AS ENUM ('pending', 'trial', 'active', 'canceled', 'expired', 'past_due', 'paused')")
    op.execute("CREATE TYPE paymentstatus AS ENUM ('pending', 'approved', 'rejected', 'refunded', 'canceled', 'charged_back')")
    op.execute("CREATE TYPE plan_type AS ENUM ('free', 'pro', 'enterprise')")
    op.execute("ALTER TABLE subscriptions ALTER COLUMN status TYPE subscriptionstatus USING status::text::subscriptionstatus")
    op.execute("ALTER TABLE payments ALTER COLUMN status TYPE paymentstatus USING status::text::paymentstatus")
    op.execute("ALTER TABLE plans ALTER COLUMN plan_type TYPE plan_type USING plan_type::text::plan_type")


def downgrade() -> None:
    """Restore the previous storage: name-labeled enums and billing VARCHAR."""
    # -- billing: back to VARCHAR values ---------------------------------------
    op.execute("ALTER TABLE subscriptions ALTER COLUMN status TYPE varchar USING status::text")
    op.execute("ALTER TABLE payments ALTER COLUMN status TYPE varchar USING status::text")
    op.execute("ALTER TABLE plans ALTER COLUMN plan_type TYPE varchar USING plan_type::text")
    op.execute("DROP TYPE subscriptionstatus")
    op.execute("DROP TYPE paymentstatus")
    op.execute("DROP TYPE plan_type")

    # -- finance: back to name labels -------------------------------------------
    op.execute("ALTER TABLE purchases ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TABLE purchases ALTER COLUMN status TYPE varchar USING status::text")
    op.execute("ALTER TABLE purchases ALTER COLUMN unit_of_measurement TYPE varchar USING unit_of_measurement::text")
    op.execute("ALTER TABLE animal_supplies ALTER COLUMN unit_of_measurement TYPE varchar USING unit_of_measurement::text")
    op.execute("DROP TYPE purchasestatus")
    op.execute("DROP TYPE unitofmeasurement")
    op.execute("CREATE TYPE purchasestatus AS ENUM ('PENDING', 'CONFIRMED')")
    op.execute(
        "CREATE TYPE unitofmeasurement AS ENUM "
        "('KILOGRAMS', 'GRAMS', 'UNIT', 'METERS', 'CENTIMETERS', 'LITERS', 'MILILITERS', 'CUBIC_CENTIMETERS')"
    )
    _reverse_map = {v: k for k, v in _PURCHASE_STATUS_MAP.items()}
    op.execute(_case_rewrite_sql("purchases", "status", _reverse_map))
    op.execute(_case_rewrite_sql("purchases", "unit_of_measurement", {v: k for k, v in _UNIT_MAP.items()}))
    op.execute(_case_rewrite_sql("animal_supplies", "unit_of_measurement", {v: k for k, v in _UNIT_MAP.items()}))
    op.execute("ALTER TABLE purchases ALTER COLUMN status TYPE purchasestatus USING status::text::purchasestatus")
    op.execute("ALTER TABLE purchases ALTER COLUMN status SET DEFAULT 'PENDING'::purchasestatus")
    op.execute(
        "ALTER TABLE purchases ALTER COLUMN unit_of_measurement TYPE unitofmeasurement USING unit_of_measurement::text::unitofmeasurement"
    )
    op.execute(
        "ALTER TABLE animal_supplies ALTER COLUMN unit_of_measurement TYPE unitofmeasurement "
        "USING unit_of_measurement::text::unitofmeasurement"
    )

    # -- cattle: back to name labels --------------------------------------------
    op.execute("ALTER TABLE animals ALTER COLUMN status TYPE varchar USING status::text")
    op.execute("DROP TYPE animalstatus")
    op.execute("CREATE TYPE animalstatus AS ENUM ('READY', 'NOT_READY', 'SOLD')")
    op.execute(_case_rewrite_sql("animals", "status", {v: k for k, v in _ANIMAL_STATUS_MAP.items()}))
    op.execute("ALTER TABLE animals ALTER COLUMN status TYPE animalstatus USING status::text::animalstatus")
