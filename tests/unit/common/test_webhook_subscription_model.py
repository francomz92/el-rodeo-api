"""Unit tests for WebhookSubscription SQLAlchemy model."""

from uuid import UUID

from src.common.infrastructure.persistence.models.webhook_subscription import (
    WebhookSubscription,
)


class TestWebhookSubscriptionModel:
    """WebhookSubscription model fields and defaults."""

    def test_has_table_name(self) -> None:
        """Model uses the correct table name."""
        assert WebhookSubscription.__tablename__ == "webhook_subscriptions"

    def test_has_id_column(self) -> None:
        """Model has a UUID primary key id."""
        col = WebhookSubscription.__table__.columns["id"]
        assert col.primary_key
        assert col.type.python_type is UUID

    def test_has_tenant_id_column(self) -> None:
        """Model has a tenant_id UUID column with index."""
        col = WebhookSubscription.__table__.columns["tenant_id"]
        assert col.type.python_type is UUID
        assert not col.nullable

    def test_has_tenant_id_index(self) -> None:
        """tenant_id has an index for tenant-scoped queries."""
        indexes = WebhookSubscription.__table__.indexes
        index_cols = {idx.name: [c.name for c in idx.columns] for idx in indexes}
        assert any("tenant_id" in cols for cols in index_cols.values())

    def test_has_url_column(self) -> None:
        """Model has a url string column (max 500)."""
        col = WebhookSubscription.__table__.columns["url"]
        assert col.type.python_type is str

    def test_has_secret_column(self) -> None:
        """Model has a secret string column (max 100)."""
        col = WebhookSubscription.__table__.columns["secret"]
        assert col.type.python_type is str

    def test_has_subscribed_events_column(self) -> None:
        """Model has a subscribed_events ARRAY column."""
        col = WebhookSubscription.__table__.columns["subscribed_events"]
        assert "ARRAY" in str(col.type).upper()

    def test_has_is_active_column(self) -> None:
        """Model has an is_active boolean column defaulting to True."""
        col = WebhookSubscription.__table__.columns["is_active"]
        assert col.type.python_type is bool
        assert col.default is not None

    def test_has_failure_count_column(self) -> None:
        """Model has a failure_count integer column defaulting to 0."""
        col = WebhookSubscription.__table__.columns["failure_count"]
        assert col.type.python_type is int
        assert col.default is not None

    def test_has_created_at_column(self) -> None:
        """Model has a created_at datetime column."""
        col = WebhookSubscription.__table__.columns["created_at"]
        assert hasattr(col.type, "python_type")

    def test_has_updated_at_column(self) -> None:
        """Model has an updated_at datetime column."""
        col = WebhookSubscription.__table__.columns["updated_at"]
        assert hasattr(col.type, "python_type")
