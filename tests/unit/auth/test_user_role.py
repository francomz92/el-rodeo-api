"""Unit tests for UserRole enum — rank hierarchy and string values."""

from src.auth.domain.entities._user_role import UserRole


class TestUserRoleValues:
    """UserRole is a StrEnum with 5 tiers."""

    def test_viewer_value(self) -> None:
        assert UserRole.VIEWER.value == "viewer"

    def test_editor_value(self) -> None:
        assert UserRole.EDITOR.value == "editor"

    def test_admin_value(self) -> None:
        assert UserRole.ADMIN.value == "admin"

    def test_owner_value(self) -> None:
        assert UserRole.OWNER.value == "owner"

    def test_super_admin_value(self) -> None:
        assert UserRole.SUPER_ADMIN.value == "super_admin"


class TestUserRoleRank:
    """UserRole.rank returns an int hierarchy for comparison."""

    def test_viewer_rank_is_one(self) -> None:
        assert UserRole.VIEWER.rank == 1

    def test_editor_rank_is_two(self) -> None:
        assert UserRole.EDITOR.rank == 2

    def test_admin_rank_is_three(self) -> None:
        assert UserRole.ADMIN.rank == 3

    def test_owner_rank_is_four(self) -> None:
        assert UserRole.OWNER.rank == 4

    def test_super_admin_rank_is_five(self) -> None:
        assert UserRole.SUPER_ADMIN.rank == 5


class TestUserRoleHierarchy:
    """Rank hierarchy: VIEWER < EDITOR < ADMIN < OWNER < SUPER_ADMIN."""

    def test_viewer_can_be_promoted_to_editor(self) -> None:
        assert UserRole.VIEWER.rank < UserRole.EDITOR.rank

    def test_editor_can_be_promoted_to_admin(self) -> None:
        assert UserRole.EDITOR.rank < UserRole.ADMIN.rank

    def test_admin_can_be_promoted_to_owner(self) -> None:
        assert UserRole.ADMIN.rank < UserRole.OWNER.rank

    def test_owner_can_be_promoted_to_super_admin(self) -> None:
        assert UserRole.OWNER.rank < UserRole.SUPER_ADMIN.rank

    def test_super_admin_is_highest_rank(self) -> None:
        assert UserRole.SUPER_ADMIN.rank > UserRole.OWNER.rank
        assert UserRole.SUPER_ADMIN.rank > UserRole.ADMIN.rank
        assert UserRole.SUPER_ADMIN.rank > UserRole.EDITOR.rank
        assert UserRole.SUPER_ADMIN.rank > UserRole.VIEWER.rank

    def test_viewer_is_lowest_rank(self) -> None:
        assert UserRole.VIEWER.rank < UserRole.EDITOR.rank
        assert UserRole.VIEWER.rank < UserRole.ADMIN.rank
        assert UserRole.VIEWER.rank < UserRole.OWNER.rank
        assert UserRole.VIEWER.rank < UserRole.SUPER_ADMIN.rank

    def test_admin_outranks_editor(self) -> None:
        assert UserRole.ADMIN.rank > UserRole.EDITOR.rank


class TestUserRoleRoundTrip:
    """UserRole can be constructed from its string value."""

    def test_from_viewer_string(self) -> None:
        assert UserRole("viewer") == UserRole.VIEWER

    def test_from_editor_string(self) -> None:
        assert UserRole("editor") == UserRole.EDITOR

    def test_from_admin_string(self) -> None:
        assert UserRole("admin") == UserRole.ADMIN

    def test_from_owner_string(self) -> None:
        assert UserRole("owner") == UserRole.OWNER

    def test_from_super_admin_string(self) -> None:
        assert UserRole("super_admin") == UserRole.SUPER_ADMIN
