"""Unit tests for authentication input schemas (Phase 8 — API Hardening).

Covers:
- RegisterSchema.email validated with EmailStr
- UpdateProfileSchema constraints (max_length, EmailStr)
"""

import pytest
from pydantic import ValidationError

from src.auth.infrastructure.adapters.http.input.authentication_schemas import (
    RegisterSchema,
)
from src.auth.infrastructure.adapters.http.input.user_schemas import (
    UpdateProfileSchema,
)


class TestRegisterSchemaEmailValidation:
    """RegisterSchema.email must use EmailStr for format validation."""

    def test_valid_email_accepted(self) -> None:
        """A properly formatted email passes validation."""
        schema = RegisterSchema(
            name="Test User",
            dni="12345678",
            email="user@example.com",
        )
        assert schema.email == "user@example.com"

    def test_invalid_email_rejected(self) -> None:
        """An email without valid format raises a validation error."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterSchema(
                name="Test User",
                dni="12345678",
                email="not-an-email",
            )
        errors = exc_info.value.errors()
        assert any("email" in e["loc"] for e in errors)

    def test_empty_email_rejected(self) -> None:
        """An empty email string raises a validation error."""
        with pytest.raises(ValidationError):
            RegisterSchema(
                name="Test User",
                dni="12345678",
                email="",
            )

    def test_email_without_domain_rejected(self) -> None:
        """An email missing domain part is rejected."""
        with pytest.raises(ValidationError):
            RegisterSchema(
                name="Test User",
                dni="12345678",
                email="user@",
            )

    def test_email_without_at_sign_rejected(self) -> None:
        """An email missing @ is rejected."""
        with pytest.raises(ValidationError):
            RegisterSchema(
                name="Test User",
                dni="12345678",
                email="userexample.com",
            )

    def test_valid_email_with_plus_tag_accepted(self) -> None:
        """Email with +tag is a valid format."""
        schema = RegisterSchema(
            name="Test User",
            dni="12345678",
            email="user+tag@example.com",
        )
        assert schema.email == "user+tag@example.com"

    def test_valid_email_with_subdomain_accepted(self) -> None:
        """Email with subdomain is a valid format."""
        schema = RegisterSchema(
            name="Test User",
            dni="12345678",
            email="user@sub.example.com",
        )
        assert schema.email == "user@sub.example.com"


class TestUpdateProfileSchemaConstraints:
    """UpdateProfileSchema must enforce max_length on name and EmailStr on email."""

    def test_name_within_limit_accepted(self) -> None:
        """Name up to 100 characters passes validation."""
        schema = UpdateProfileSchema(name="a" * 100)
        assert schema.name == "a" * 100

    def test_name_exceeds_max_length_rejected(self) -> None:
        """Name longer than 100 characters raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            UpdateProfileSchema(name="a" * 101)
        errors = exc_info.value.errors()
        assert any("name" in e["loc"] for e in errors)

    def test_name_none_accepted(self) -> None:
        """Omitting name is allowed (optional field)."""
        schema = UpdateProfileSchema(email="test@example.com")
        assert schema.name is None

    def test_valid_email_accepted(self) -> None:
        """A valid email passes validation."""
        schema = UpdateProfileSchema(email="user@example.com")
        assert schema.email == "user@example.com"

    def test_invalid_email_rejected(self) -> None:
        """An invalid email raises validation error."""
        with pytest.raises(ValidationError):
            UpdateProfileSchema(email="not-an-email")

    def test_email_none_accepted(self) -> None:
        """Omitting email is allowed (optional field)."""
        schema = UpdateProfileSchema(name="Test")
        assert schema.email is None

    def test_empty_email_rejected(self) -> None:
        """An empty string for email raises validation error."""
        with pytest.raises(ValidationError):
            UpdateProfileSchema(email="")
