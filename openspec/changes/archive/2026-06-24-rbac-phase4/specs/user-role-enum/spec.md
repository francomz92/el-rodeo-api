# user-role-enum — Specification

## Purpose
Define the `UserRole` StrEnum with a 4-tier hierarchy and wire it through the entity, model, VOs, and repository mapping.

## Requirements

### Requirement: UserRole Enum

The system MUST define `UserRole` as a `StrEnum` with OWNER("owner", rank=4), ADMIN("admin", rank=3), EDITOR("editor", rank=2), VIEWER("viewer", rank=1). Each MUST expose a `rank` property for comparison.

#### Scenario: Rank hierarchy
- GIVEN the UserRole enum
- WHEN comparing ranks
- THEN OWNER.rank > ADMIN.rank > EDITOR.rank > VIEWER.rank

#### Scenario: String values are lowercase roles
- GIVEN each UserRole member
- WHEN accessed as string
- THEN str(OWNER) == "owner", str(ADMIN) == "admin", str(EDITOR) == "editor", str(VIEWER) == "viewer"

### Requirement: Entity, Model, VO, Repository wiring

The system MUST add `role: UserRole` (default VIEWER) to UserEntity, `role: Mapped[str]` NOT NULL default "viewer" to the User SQLAlchemy model, `role: UserRole = UserRole.VIEWER` to creation/update VOs, and string-to-enum mapping in `_build_user`.

#### Scenario: Default role on registration
- GIVEN a UserCreationValueObject without role
- WHEN creating a user
- THEN role defaults to UserRole.VIEWER

#### Scenario: Role persists and maps back
- GIVEN a user saved with role "admin" in the DB
- WHEN UserRepository._build_user maps the row
- THEN returned UserEntity.role == UserRole.ADMIN
