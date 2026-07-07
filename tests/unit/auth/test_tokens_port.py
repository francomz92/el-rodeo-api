"""Unit tests for ITokenService interface contract.

Verifies that the token service port defines the required methods
for access and refresh token operations.
"""

from abc import ABC

import pytest

from src.auth.application.ports.tokens_port import ITokenService


def test_interface_is_abstract() -> None:
    """ITokenService must be an abstract class."""
    assert issubclass(ITokenService, ABC)


def test_interface_defines_existing_methods() -> None:
    """Existing methods (generate, decode) are still present."""
    assert hasattr(ITokenService, "generate")
    assert hasattr(ITokenService, "decode")


def test_interface_defines_generate_refresh_token() -> None:
    """ITokenService must declare generate_refresh_token method."""
    assert hasattr(ITokenService, "generate_refresh_token")


def test_interface_defines_decode_refresh_token() -> None:
    """ITokenService must declare decode_refresh_token method."""
    assert hasattr(ITokenService, "decode_refresh_token")


def test_interface_defines_rotate_refresh_token() -> None:
    """ITokenService must declare rotate_refresh_token method."""
    assert hasattr(ITokenService, "rotate_refresh_token")


def test_interface_defines_revoke_refresh_token() -> None:
    """ITokenService must declare revoke_refresh_token method."""
    assert hasattr(ITokenService, "revoke_refresh_token")


def test_interface_defines_revoke_user_refresh_tokens() -> None:
    """ITokenService must declare revoke_user_refresh_tokens method."""
    assert hasattr(ITokenService, "revoke_user_refresh_tokens")


def test_new_methods_raise_not_implemented() -> None:
    """Calling new methods on the base class raises NotImplementedError."""
    with pytest.raises(NotImplementedError):
        ITokenService.generate_refresh_token(None, "user-id")  # type: ignore[call-arg]

    with pytest.raises(NotImplementedError):
        ITokenService.decode_refresh_token(None, "token")  # type: ignore[call-arg]

    # Async methods need a coroutine runner — just verify the method exists
    assert hasattr(ITokenService, "rotate_refresh_token")
    assert hasattr(ITokenService, "revoke_refresh_token")
    assert hasattr(ITokenService, "revoke_user_refresh_tokens")
