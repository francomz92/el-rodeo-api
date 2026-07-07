"""Tests for billing domain exceptions."""

from src.billing.domain.exceptions import QuotaExceededException


class TestQuotaExceededException:
    """Task 1.10: QuotaExceededException."""

    def test_construct_with_message_and_params(self) -> None:
        exc = QuotaExceededException(
            resource_name="animals",
            limit=50,
            current_usage=60,
        )
        assert exc.resource_name == "animals"
        assert exc.limit == 50
        assert exc.current_usage == 60
        assert str(exc) == "Quota 'animals' exceeded: 60 used, limit is 50"

    def test_is_exception(self) -> None:
        exc = QuotaExceededException(
            resource_name="animals",
            limit=50,
            current_usage=60,
        )
        assert isinstance(exc, Exception)

    def test_default_message_format(self) -> None:
        exc = QuotaExceededException(
            resource_name="users",
            limit=5,
            current_usage=10,
        )
        assert str(exc) == "Quota 'users' exceeded: 10 used, limit is 5"
