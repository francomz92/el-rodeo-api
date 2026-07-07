"""Unit tests for JWT token tenant_id round-trip.

Verifies that tenant_id can be passed through the data dict to generate()
and that decode() returns it in the payload.
"""

from uuid import uuid4

import jwt as pyjwt

from src.common.infrastructure.adapters.security.tokens import TokenService

# Test secret/algorithm matching production config
TEST_SECRET = "test-secret-key-for-unit-tests"
TEST_ALGORITHM = "HS256"


class TestTokenServiceTenantId:
    """TokenService generates and decodes JWTs with tenant_id."""

    def setup_method(self) -> None:
        self.service = TokenService(secret=TEST_SECRET, algorithm=TEST_ALGORITHM)

    def test_generate_accepts_tenant_id_in_data(self) -> None:
        """tenant_id in the data dict is included in the JWT payload."""
        user_id = str(uuid4())
        tenant_id = str(uuid4())

        token = self.service.generate(
            data={"user_id": user_id, "tenant_id": tenant_id},
            exp_minutes=15,
        )

        payload = pyjwt.decode(token, TEST_SECRET, [TEST_ALGORITHM])
        assert payload["user_id"] == user_id
        assert payload["tenant_id"] == tenant_id
        assert payload["type"] == "access"

    def test_generate_without_tenant_id_still_works(self) -> None:
        """Backward compat: generate() without tenant_id is fine."""
        user_id = str(uuid4())

        token = self.service.generate(
            data={"user_id": user_id},
            exp_minutes=15,
        )

        payload = pyjwt.decode(token, TEST_SECRET, [TEST_ALGORITHM])
        assert payload["user_id"] == user_id

    def test_decode_returns_tenant_id_when_present(self) -> None:
        """decode() returns tenant_id when it was included in the payload."""
        user_id = str(uuid4())
        tenant_id = str(uuid4())

        token = self.service.generate(
            data={"user_id": user_id, "tenant_id": tenant_id},
            exp_minutes=15,
        )

        payload = self.service.decode(token)
        assert payload["tenant_id"] == tenant_id
