"""Unit tests for auth dependencies: require_role factory.

Tests verify that require_role correctly enforces role hierarchy:
- All 4 role levels grant access at their own level
- Insufficient roles are denied with NotPermissionError
- OWNER bypasses all restrictions by rank superiority
"""

import pytest
from tests.factories import make_user_entity

from src.auth.domain.entities._user_role import UserRole
from src.common.domain.exceptions import NotPermissionError


@pytest.mark.asyncio
async def test_viewer_allowed_when_require_viewer() -> None:
    """VIEWER user passes require_role(VIEWER)."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        require_role,
    )

    dep = require_role(UserRole.VIEWER)
    inner = dep.dependency
    user = make_user_entity(role=UserRole.VIEWER)
    result = await inner(current_user=user)
    assert result is None


@pytest.mark.asyncio
async def test_editor_allowed_when_require_editor() -> None:
    """EDITOR user passes require_role(EDITOR)."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        require_role,
    )

    dep = require_role(UserRole.EDITOR)
    inner = dep.dependency
    user = make_user_entity(role=UserRole.EDITOR)
    result = await inner(current_user=user)
    assert result is None


@pytest.mark.asyncio
async def test_admin_allowed_when_require_admin() -> None:
    """ADMIN user passes require_role(ADMIN)."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        require_role,
    )

    dep = require_role(UserRole.ADMIN)
    inner = dep.dependency
    user = make_user_entity(role=UserRole.ADMIN)
    result = await inner(current_user=user)
    assert result is None


@pytest.mark.asyncio
async def test_owner_allowed_when_require_owner() -> None:
    """OWNER user passes require_role(OWNER)."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        require_role,
    )

    dep = require_role(UserRole.OWNER)
    inner = dep.dependency
    user = make_user_entity(role=UserRole.OWNER)
    result = await inner(current_user=user)
    assert result is None


@pytest.mark.asyncio
async def test_viewer_denied_when_require_editor() -> None:
    """VIEWER user is denied by require_role(EDITOR)."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        require_role,
    )

    dep = require_role(UserRole.EDITOR)
    inner = dep.dependency
    user = make_user_entity(role=UserRole.VIEWER)
    with pytest.raises(NotPermissionError):
        await inner(current_user=user)


@pytest.mark.asyncio
async def test_editor_denied_when_require_admin() -> None:
    """EDITOR user is denied by require_role(ADMIN)."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        require_role,
    )

    dep = require_role(UserRole.ADMIN)
    inner = dep.dependency
    user = make_user_entity(role=UserRole.EDITOR)
    with pytest.raises(NotPermissionError):
        await inner(current_user=user)


@pytest.mark.asyncio
async def test_admin_denied_when_require_owner() -> None:
    """ADMIN user is denied by require_role(OWNER)."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        require_role,
    )

    dep = require_role(UserRole.OWNER)
    inner = dep.dependency
    user = make_user_entity(role=UserRole.ADMIN)
    with pytest.raises(NotPermissionError):
        await inner(current_user=user)


@pytest.mark.asyncio
async def test_owner_can_access_admin_level() -> None:
    """OWNER user passes require_role(ADMIN) — rank superiority."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        require_role,
    )

    dep = require_role(UserRole.ADMIN)
    inner = dep.dependency
    user = make_user_entity(role=UserRole.OWNER)
    result = await inner(current_user=user)
    assert result is None


@pytest.mark.asyncio
async def test_owner_can_access_viewer_level() -> None:
    """OWNER user passes require_role(VIEWER) — rank superiority."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        require_role,
    )

    dep = require_role(UserRole.VIEWER)
    inner = dep.dependency
    user = make_user_entity(role=UserRole.OWNER)
    result = await inner(current_user=user)
    assert result is None


@pytest.mark.asyncio
async def test_admin_can_access_editor_level() -> None:
    """ADMIN user passes require_role(EDITOR) — rank superiority."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        require_role,
    )

    dep = require_role(UserRole.EDITOR)
    inner = dep.dependency
    user = make_user_entity(role=UserRole.ADMIN)
    result = await inner(current_user=user)
    assert result is None


@pytest.mark.asyncio
async def test_editor_can_access_viewer_level() -> None:
    """EDITOR user passes require_role(VIEWER) — rank superiority."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        require_role,
    )

    dep = require_role(UserRole.VIEWER)
    inner = dep.dependency
    user = make_user_entity(role=UserRole.EDITOR)
    result = await inner(current_user=user)
    assert result is None


@pytest.mark.asyncio
async def test_require_role_error_message_includes_role_name() -> None:
    """NotPermissionError message mentions the required role."""
    from src.auth.infrastructure.presentation.dependencies.auth_dependencies import (
        require_role,
    )

    dep = require_role(UserRole.ADMIN)
    inner = dep.dependency
    user = make_user_entity(role=UserRole.VIEWER)
    with pytest.raises(NotPermissionError) as exc_info:
        await inner(current_user=user)
    assert "admin" in str(exc_info.value).lower()
