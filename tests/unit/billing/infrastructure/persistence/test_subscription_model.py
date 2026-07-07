"""Tests for Subscription SQLAlchemy model."""

from sqlalchemy import (
    DateTime,
    String,
    Uuid as SA_Uuid,
)
from sqlalchemy.dialects.postgresql import JSONB

from src.common.infrastructure.persistence.models import Model


class TestSubscriptionModel:
    """Subscription model must define subscriptions table with expected columns."""

    def test_import_succeeds(self) -> None:
        """Subscription model can be imported."""

    def test_tablename(self) -> None:
        """Subscription model uses 'subscriptions' tablename."""
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription,
        )

        assert Subscription.__tablename__ == "subscriptions"

    def test_inherits_model(self) -> None:
        """Subscription model inherits from common Model base."""
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription,
        )

        assert issubclass(Subscription, Model)

    def test_has_id_column(self) -> None:
        """Subscription has UUID primary key id column."""
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription,
        )

        col = Subscription.__table__.columns["id"]
        assert isinstance(col.type, SA_Uuid)
        assert col.primary_key

    def test_has_tenant_id_fk(self) -> None:
        """Subscription has tenant_id FK referencing tenants(id)."""
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription,
        )

        col = Subscription.__table__.columns["tenant_id"]
        assert isinstance(col.type, SA_Uuid)
        assert col.nullable is False
        # Check FK target (resolved or as string)
        fks = list(col.foreign_keys)
        assert len(fks) == 1
        fk = fks[0]
        assert fk._get_colspec() == "tenants.id"
        assert fk.ondelete == "CASCADE"

    def test_has_plan_id_fk(self) -> None:
        """Subscription has plan_id FK referencing plans(id) with RESTRICT."""
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription,
        )

        col = Subscription.__table__.columns["plan_id"]
        assert isinstance(col.type, SA_Uuid)
        assert col.nullable is False
        fks = list(col.foreign_keys)
        assert len(fks) == 1
        fk = fks[0]
        assert fk.column.table.name == "plans"
        assert fk.column.name == "id"
        assert fk.ondelete == "RESTRICT"

    def test_has_status_column(self) -> None:
        """Subscription has VARCHAR status column."""
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription,
        )

        col = Subscription.__table__.columns["status"]
        assert isinstance(col.type, String)
        assert col.type.length == 20
        assert col.nullable is False

    def test_has_current_period_start(self) -> None:
        """Subscription has TIMESTAMPTZ current_period_start."""
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription,
        )

        col = Subscription.__table__.columns["current_period_start"]
        assert isinstance(col.type, DateTime)
        assert col.nullable is False

    def test_has_current_period_end(self) -> None:
        """Subscription has nullable TIMESTAMPTZ current_period_end."""
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription,
        )

        col = Subscription.__table__.columns["current_period_end"]
        assert isinstance(col.type, DateTime)
        assert col.nullable is True

    def test_has_trial_end(self) -> None:
        """Subscription has nullable TIMESTAMPTZ trial_end."""
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription,
        )

        col = Subscription.__table__.columns["trial_end"]
        assert isinstance(col.type, DateTime)
        assert col.nullable is True

    def test_has_canceled_at(self) -> None:
        """Subscription has nullable TIMESTAMPTZ canceled_at."""
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription,
        )

        col = Subscription.__table__.columns["canceled_at"]
        assert isinstance(col.type, DateTime)
        assert col.nullable is True

    def test_has_metadata_jsonb(self) -> None:
        """Subscription stores metadata as JSONB with default."""
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription,
        )

        col = Subscription.__table__.columns["metadata"]
        assert isinstance(col.type, JSONB)
        # Python attribute name avoids SQLAlchemy reserved word
        assert hasattr(Subscription, "subscription_metadata")

    def test_has_timestamps(self) -> None:
        """Subscription has created_at and updated_at columns."""
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription,
        )

        assert "created_at" in Subscription.__table__.columns
        assert "updated_at" in Subscription.__table__.columns

    def test_tenant_id_index(self) -> None:
        """Subscription has index on tenant_id for fast lookup."""
        from src.billing.infrastructure.persistence.models._subscription_model import (
            Subscription,
        )

        # Check that an index exists for tenant_id
        indexes = [idx for idx in Subscription.__table__.indexes if len(idx.columns) == 1 and "tenant_id" in idx.columns]
        assert len(indexes) >= 1
