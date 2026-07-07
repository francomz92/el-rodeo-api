# Design: RBAC Phase 4 — Role-Based Access Control

## Technical Approach

Add a 4-tier `UserRole` enum (VIEWER < EDITOR < ADMIN < OWNER) with `.rank` comparison, inject a `require_role()` dependency factory, and protect all ~40 routes across 4 bounded contexts. Fix the production `bypass_filter` gap in `AuthService.get_authenticated_user()`. Keep `is_admin` as a cross-tenant flag alongside `role` for tenant-scoped auth.

## Architecture Decisions

| Decision | Options | Tradeoffs | Choice |
|----------|---------|-----------|--------|
| UserRole location | In `_user_entity.py` vs separate `_user_role.py` | Co-location is simpler, separate avoids import coupling | **Separate `_user_role.py`** in `auth/domain/entities/` |
| `require_role` placement | `auth_dependencies.py` vs new file | Existing file bundles all auth deps; new file SRP | **`auth_dependencies.py`** (follows existing pattern) |
| Guard injection | Router-level vs per-route | Router-level DRYer; per-route explicit for varying roles | **Router-level VIEWER** + **per-route overrides** for EDITOR/ADMIN |
| Role assignment | New endpoint vs reuse update_user | New keeps SRP; reuse adds role to generic update | **New endpoint** `PUT /users/{id}/role` |
| `bypass_filter` fix | In `AuthService` vs `_get_current_user` dependency | Service has direct UoW access; dependency adds another injection | **In `AuthService.get_authenticated_user()`** after user loads |
| Chained PR split | 2 vs 3 PRs | Fewer merges vs smaller chunks | **3 PRs** per spec recommendation |

## Data Flow

```
JWT Request
  │
  ├─► _get_current_user (FastAPI Depends)
  │     ├─ decode JWT → extract tenant_id, user_id
  │     ├─ uow.tenant_id = payload.tenant_id
  │     ├─ auth_service.get_authenticated_user(uow, token)
  │     │    ├─ check blacklist
  │     │    ├─ repo.get_by_id(user_id) → UserEntity(role, is_admin)
  │     │    └─ uow.bypass_filter = user.is_admin   ★ FIX
  │     └─ return UserEntity (with role + is_admin)
  │
  ├─► require_role(EDITOR)  ← router-level or per-route
  │     ├─ current_user.role.rank >= EDITOR.rank? → ok
  │     └─ else → raise NotPermissionError(403)
  │
  └─► Use Case
        └─ TenantAwareRepository uses uow.bypass_filter
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/auth/domain/entities/_user_role.py` | Create | `UserRole` StrEnum with `.rank` |
| `src/auth/domain/entities/__init__.py` | Modify | Export `UserRole` |
| `src/auth/domain/entities/_user_entity.py` | Modify | Add `role: UserRole = UserRole.VIEWER` field |
| `src/auth/domain/value_objects/user_value_object.py` | Modify | Add `role: UserRole = UserRole.VIEWER` to creation VO |
| `src/auth/infrastructure/persistence/models/_user_models.py` | Modify | Add `role: Mapped[str] = mapped_column(String(20), ...)` |
| `src/auth/infrastructure/persistence/repositories/user_repository.py` | Modify | Map `role=UserRole(user_db["role"])` in `_build_user` |
| `src/auth/domain/repositories/users_repository_port.py` | Modify | Add `update_role(id, role)` / `count_owners_by_tenant(tid)` |
| `src/auth/application/services/authentication_service.py` | Modify | Set `uow.bypass_filter = user.is_admin` after user load |
| `src/auth/infrastructure/presentation/dependencies/auth_dependencies.py` | Modify | Add `require_role()` factory; keep `is_admin_user` as alias |
| `src/auth/domain/services/update_user_role_service.py` | Create | Validate last-OWNER, self-escalation rules |
| `src/auth/application/uses_cases/update_user_role_case.py` | Create | Orchestrate role update with UoW |
| `src/auth/infrastructure/presentation/dependencies/role_dependencies.py` | Create | Wire `UpdateUserRoleCase` for DI |
| `src/auth/infrastructure/presentation/routers/_role_routers.py` | Create | `PUT /users/{id}/role` endpoint |
| `src/cattle/.../_animals.py` | Modify | Add guards to 5 routes |
| `src/cattle/.../_animal_protocols.py` | Modify | Add guards to 4 routes |
| `src/cattle/.../_animal_types.py` | Modify | Replace `is_admin_user` → `require_role(ADMIN)` |
| `src/cattle/.../_schedule_events.py` | Modify | Add guards to 4 routes |
| `src/finance/.../_purchases.py` | Modify | Add guards to 4 routes |
| `src/finance/.../_animal_supply_types.py` | Modify | Replace `is_admin_user` → `require_role(ADMIN)` |
| `src/finance/.../_animal_supplies.py` | Modify | Add guards to 5 routes |
| `src/market/.../_sales.py` | Modify | Add guards to 4 routes |
| `src/market/.../_buyers.py` | Modify | Add guards to 5 routes |
| `src/auth/.../_authentication_routers.py` | Modify | Replace `is_admin_user` → `require_role(ADMIN)` on `/register` |
| `alembic/versions/xxxx_add_role_column.py` | Create | Add `role VARCHAR(20)`, backfill, CHECK constraint |

## Route Protection Matrix

| Router | GET (list) | GET (by id) | POST | PUT | DELETE |
|--------|-----------|-------------|------|-----|--------|
| `/animals` | VIEWER | VIEWER | **EDITOR** | **EDITOR** | **ADMIN** |
| `/animal-protocols` | VIEWER | VIEWER | — | **EDITOR** | **ADMIN** |
| `/animal-types` | **ADMIN** | — | **ADMIN** | **ADMIN** | — |
| `/schedule-events` | VIEWER | — | **EDITOR** | **EDITOR** | **ADMIN** |
| `/purchases` | VIEWER | VIEWER | **EDITOR** | — | **ADMIN** |
| `/supply-types` | **ADMIN** | — | **ADMIN** | **ADMIN** | **ADMIN** |
| `/animal-supplies` | VIEWER | VIEWER | **EDITOR** | **EDITOR** | **ADMIN** |
| `/buyers` | VIEWER | VIEWER | **EDITOR** | **EDITOR** | **ADMIN** |
| `/sales` | VIEWER | VIEWER | **EDITOR** | — | **ADMIN** |
| `/register` | — | — | **ADMIN** | — | — |

Bold = explicit guard override; others use the router-level VIEWER guard.

## Interfaces / Contracts

```python
# UserRole enum
class UserRole(str, Enum):
    VIEWER = "viewer"
    EDITOR = "editor"
    ADMIN = "admin"
    OWNER = "owner"

    @property
    def rank(self) -> int:
        return {"viewer": 1, "editor": 2, "admin": 3, "owner": 4}[self.value]

# require_role factory — in auth_dependencies.py
def require_role(min_role: UserRole):
    async def _role_checker(current_user: GetCurrentUser) -> None:
        if current_user.role.rank < min_role.rank:
            raise NotPermissionError(
                f"Se requiere rol {min_role.value} o superior"
            )
    return Depends(_role_checker)

# UpdateUserRoleCase — new use case
class UpdateUserRoleCase:
    async def execute(actor: UserEntity, target_id: UUID, new_role: UserRole):
        # 1. actor must be ADMIN or OWNER
        # 2. cannot self-escalate (actor.id != target_id when self-demoting)
        # 3. last-OWNER check: if demoting an OWNER, verify ≥1 other OWNER same tenant
        # 4. repo.update_role(target_id, new_role)
```

## Testing Strategy

| Layer | What | How |
|-------|------|-----|
| Unit | UserRole rank comparison | Parametrized tests, pure Python |
| Unit | require_role raises/accepts | Mock GetCurrentUser, verify NotPermissionError |
| Unit | UpdateUserRoleCase + Service | Mock repository, test all guard rules |
| Unit | bypass_filter set in AuthService | Mock UoW, verify assignment after get_user |
| Integration | Role hierarchy on all routes | New fixtures `viewer_client`, `editor_client`, `admin_client` in conftest; each fixture sets `role` on the injected `UserEntity` |
| Integration | Last-OWNER protection | Seed 2 OWNERs, demote 1, verify 1 remains |
| Integration | Self-escalation blocked | VIEWER tries `PUT /users/{self}/role → 403` |
| Migration | `role` column + backfill | Alembic test (--autogenerate check, SQL replay) |

## Migration / Rollout

1. Alembic revision: `ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'viewer'`
2. Backfill: `UPDATE users SET role = 'admin' WHERE is_admin = TRUE`
3. Add CHECK: `ALTER TABLE users ADD CONSTRAINT ck_users_role CHECK (role IN ('viewer','editor','admin','owner'))`
4. `is_admin` column kept for dual-read until next cleanup phase
5. Deploy: 3 chained PRs per spec recommendation

## Open Questions

None identified. All technical decisions are resolved against the existing codebase patterns.
