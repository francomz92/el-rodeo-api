# Design: User Management — Phase 5

## Technical Approach

Add four use cases following the existing `UpdateUserRoleCase` pattern (UoW-scoped, single responsibility). Extend `IUserRepository` with `list()` and `exists_by_email_excluding_user()`. Add a 3-line `is_active` guard in `LoginUserService.validate_credentials`. Profile routes attach to `auth_router` (no auth overhead), admin routes to `role_router` (already prefix=/users, already has `require_role` DEPs). Schemas reuse `from_attributes` ConfigDict. No new services, no new entities — just use cases + repo extension + schemas.

## Architecture Decisions

### Decision: Profile vs admin route separation

| Option | Tradeoff | Decision |
|--------|----------|----------|
| All in `_authentication_routers` | Mixed concerns, auth_router grows | Rejected |
| All in `_role_routers` | Profile routes need no admin guard | Rejected |
| Profile on `auth_router`, admin on `role_router` | Clean separation, reuses existing guards | ✅ Chosen |

Rationale: Profile endpoints (`/users/me`) are self-service and need only auth — they naturally live on `auth_router`. Admin endpoints need `require_role(ADMIN)` which `_role_routers.py` already applies. No new router module needed — add endpoints to existing files.

### Decision: Use case isolation

| Option | Tradeoff | Decision |
|--------|----------|----------|
| Single `UserManagementCase` | Cohesion loss, harder to test | Rejected |
| One file per use case | 4 files, explicit deps, easy to unit-test | ✅ Chosen |

Rationale: Follows existing pattern (`update_user_role_case.py`, `login_user_case.py`). Each use case gets its own `execute` method with unambiguous dependencies.

### Decision: Repository method naming

| Option | Tradeoff | Decision |
|--------|----------|----------|
| `list_users` | Matches proposal/spec | Rejected |
| `list` | Shorter, consistent with `get_by_id` / `create` | ✅ Chosen |

Rationale: The repo is already scoped to users (`IUserRepository`). `repo.list(...)` reads naturally. Follow billing's `list_by_tenant` pattern but name it `list` since tenant_id is always a parameter.

### Decision: Value object for profile update

| Option | Tradeoff | Decision |
|--------|----------|----------|
| New `UserProfileUpdateValueObject` | Another file, but clean | Rejected |
| Extend `UserUpdateValueObject` with `email` | Existing `update_data` handles Sentinels | ✅ Chosen |

Rationale: `update_data` already strips `Sentinel.UNSET` fields and passes remaining keys to SQL UPDATE. Adding `email` with `Sentinel` default means the same method works for profile updates without a new VO.

## Data Flow

```
── Profile (GET/PUT /users/me) ──
  Router → GetCurrentUser + UseCase → UoW → Repo → DB
  (No tenant/role guard — user is the resource owner)

── Admin list (GET /users) ──
  Router → require_role(ADMIN) → ListUsersCase → UoW → Repo.list(tenant_id, ...) → DB
  │                                                                              │
  └── PaginatedUsersSchema ← items + total + page + per_page ───────────────────┘

── Admin delete (DELETE /users/{id}) ──
  Router → require_role(ADMIN) → SoftDeleteUserCase
    → guard: not self, not last OWNER, same tenant
    → repo.update_data(id, UserUpdateValueObject(is_active=False))
    → commit
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/auth/domain/repositories/users_repository_port.py` | Modify | Add `list()` and `exists_by_email_excluding_user()` |
| `src/auth/infrastructure/persistence/repositories/user_repository.py` | Modify | Implement both new methods |
| `src/auth/domain/value_objects/user_value_object.py` | Modify | Add `email` to `UserUpdateValueObject` |
| `src/auth/domain/services/login_user_service.py` | Modify | Add `is_active` check in `validate_credentials` |
| `src/auth/application/uses_cases/get_user_profile_case.py` | Create | Returns current_user directly |
| `src/auth/application/uses_cases/update_user_profile_case.py` | Create | Email uniqueness check, repo.update_data |
| `src/auth/application/uses_cases/list_users_case.py` | Create | Admin guard, repo.list call |
| `src/auth/application/uses_cases/soft_delete_user_case.py` | Create | Guards + repo.update_data(is_active=False) |
| `src/auth/infrastructure/adapters/http/output/user_schemas.py` | Modify | Enrich with email, role, is_active, tenant_id |
| `src/auth/infrastructure/adapters/http/input/user_schemas.py` | Create | UpdateProfileSchema (name?, email?) |
| `src/auth/infrastructure/presentation/routers/_authentication_routers.py` | Modify | Add GET + PUT /users/me |
| `src/auth/infrastructure/presentation/routers/_role_routers.py` | Modify | Add GET /users, GET /users/{id}, DELETE /users/{id} |
| `src/auth/infrastructure/presentation/dependencies/user_dependencies.py` | Create | DI wiring for 4 new use cases |

## Interfaces / Contracts

```python
# ── Repository port extensions ──
class IUserRepository(IRepository):
    async def list(
        self,
        tenant_id: UUID,
        page: int = 1,
        per_page: int = 20,
        search: str | None = None,
        role: UserRole | None = None,
    ) -> tuple[list[UserEntity], int]: ...

    async def exists_by_email_excluding_user(
        self, email: str, exclude_user_id: UUID
    ) -> bool: ...

# ── Schemas ──
class UserProfileSchema(BaseModel):
    id: UUID; created_at: datetime; name: str; dni: str
    email: str; role: str; is_active: bool; tenant_id: UUID | None
    model_config = ConfigDict(from_attributes=True)

class UpdateProfileSchema(BaseModel):
    name: str | None = None
    email: str | None = None

class PaginatedUsersSchema(BaseModel):
    items: list[UserProfileSchema]
    total: int; page: int; per_page: int
```

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | GetUserProfileCase | MockUoW, assert returns current_user unchanged |
| Unit | UpdateUserProfileCase | MockUoW, test 409 on duplicate email, assert commit |
| Unit | ListUsersCase | MockUoW, test role guard (403), test pagination passthrough |
| Unit | SoftDeleteUserCase | MockUoW, test self-block, last-OWNER block, cross-tenant block |
| Unit | LoginService | Mock repo, test inactive user raises 401 |
| Integration | GET/PUT /users/me | Full stack, assert 200 + enriched schema |
| Integration | GET /users | Assert pagination, search filter, 403 for VIEWER |
| Integration | DELETE /users/{id} | Assert soft-delete, 400 on self-delete |

## Migration / Rollout

No data migration required. `is_active` already defaults to `True` in the model. New repository and use cases are additive — old auth flow unchanged until the login guard is added.

## Open Questions

- [ ] Should `UserSchema` be renamed to `UserProfileSchema` for clarity, or should we enrich in place? (Spec says enrich — keep same name for backward compat)
- [ ] Pagination max per_page? Proposal says 100, spec omits — use 100 as ceiling.
