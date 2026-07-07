from enum import StrEnum


class UserRole(StrEnum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    OWNER = "owner"
    SUPER_ADMIN = "super_admin"

    @property
    def rank(self) -> int:
        return {"viewer": 1, "editor": 2, "admin": 3, "owner": 4, "super_admin": 5}[self.value]
