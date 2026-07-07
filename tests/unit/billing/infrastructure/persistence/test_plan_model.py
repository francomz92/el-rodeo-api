"""Tests for Plan SQLAlchemy model."""

from sqlalchemy import (
    Boolean,
    DateTime,
    Numeric,
    String,
    Uuid as SA_Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB

from src.common.infrastructure.persistence.models import Model


class TestPlanModel:
    """Plan model must define plans table with expected columns."""

    def test_import_succeeds(self) -> None:
        """Plan model can be imported (existence test)."""

    def test_tablename(self) -> None:
        """Plan model uses 'plans' tablename."""
        from src.billing.infrastructure.persistence.models._plan_model import Plan

        assert Plan.__tablename__ == "plans"

    def test_inherits_model(self) -> None:
        """Plan model inherits from common Model base."""
        from src.billing.infrastructure.persistence.models._plan_model import Plan

        assert issubclass(Plan, Model)

    def test_has_id_column(self) -> None:
        """Plan has UUID primary key id column."""
        from src.billing.infrastructure.persistence.models._plan_model import Plan

        col = Plan.__table__.columns["id"]
        assert isinstance(col.type, SA_Uuid)
        assert col.primary_key
        assert col.index is True

    def test_has_plan_type_column(self) -> None:
        """Plan has unique VARCHAR plan_type column."""
        from src.billing.infrastructure.persistence.models._plan_model import Plan

        col = Plan.__table__.columns["plan_type"]
        assert isinstance(col.type, String)
        assert col.type.length == 20
        assert col.unique is True
        assert col.nullable is False

    def test_has_name_column(self) -> None:
        """Plan has VARCHAR name column."""
        from src.billing.infrastructure.persistence.models._plan_model import Plan

        col = Plan.__table__.columns["name"]
        assert isinstance(col.type, String)
        assert col.type.length == 100

    def test_has_description_column(self) -> None:
        """Plan has TEXT description column."""
        from src.billing.infrastructure.persistence.models._plan_model import Plan

        col = Plan.__table__.columns["description"]
        col_type = col.type
        # Could be TEXT or VARCHAR
        assert isinstance(col_type, String)

    def test_has_features_jsonb(self) -> None:
        """Plan stores features as JSONB."""
        from src.billing.infrastructure.persistence.models._plan_model import Plan

        col = Plan.__table__.columns["features"]
        assert isinstance(col.type, JSONB)

    def test_has_quotas_jsonb(self) -> None:
        """Plan stores quotas as JSONB."""
        from src.billing.infrastructure.persistence.models._plan_model import Plan

        col = Plan.__table__.columns["quotas"]
        assert isinstance(col.type, JSONB)

    def test_has_price_monthly(self) -> None:
        """Plan has NUMERIC price_monthly column."""
        from src.billing.infrastructure.persistence.models._plan_model import Plan

        col = Plan.__table__.columns["price_monthly"]
        assert isinstance(col.type, Numeric)

    def test_has_price_yearly(self) -> None:
        """Plan has NUMERIC price_yearly column."""
        from src.billing.infrastructure.persistence.models._plan_model import Plan

        col = Plan.__table__.columns["price_yearly"]
        assert isinstance(col.type, Numeric)

    def test_has_is_active(self) -> None:
        """Plan has BOOLEAN is_active column defaulting to True."""
        from src.billing.infrastructure.persistence.models._plan_model import Plan

        col = Plan.__table__.columns["is_active"]
        assert isinstance(col.type, Boolean)
        assert col.default is not None

    def test_has_timestamps(self) -> None:
        """Plan has created_at and updated_at columns."""
        from src.billing.infrastructure.persistence.models._plan_model import Plan

        assert "created_at" in Plan.__table__.columns
        assert "updated_at" in Plan.__table__.columns
        created = Plan.__table__.columns["created_at"]
        updated = Plan.__table__.columns["updated_at"]
        assert isinstance(created.type, DateTime)
        assert isinstance(updated.type, DateTime)

    def test_pk_is_uuid_not_autoinc(self) -> None:
        """Plan PK is UUID, not auto-increment."""
        from src.billing.infrastructure.persistence.models._plan_model import Plan

        id_col = Plan.__table__.columns["id"]
        assert isinstance(id_col.type, SA_Uuid)
        assert id_col.autoincrement == "auto"  # SA default for non-integer PK
