# Tasks: User Management — Phase 5

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~450-550 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (core/domain) → PR 2 (routes/DI/tests) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Repository + VO + Login guard + Enriched schema + 4 use cases | PR 1 | Base = main. Domain, app layer, schemas. No routes/DI/tests. |
| 2 | Routes + DI wiring + Unit & integration tests | PR 2 | Base = PR 1 branch or main (if stacked). Presentation + test layer. |

## Phase 1: Repository & Value Objects

- [x] 1.1 Add `list()` and `exists_by_email_excluding_user()` to `IUserRepository` port
- [x] 1.2 Implement `list()` in `UserRepository` — paginated, tenant-scoped, ILIKE search, role filter
- [x] 1.3 Implement `exists_by_email_excluding_user()` in `UserRepository`
- [x] 1.4 Add `email` and `is_active` fields to `UserUpdateValueObject` (Sentinel default)

## Phase 2: Domain Service Guard

- [x] 2.1 Add `is_active` check in `LoginUserService.validate_credentials` — inactive user raises 401

## Phase 3: Schemas

- [x] 3.1 Enrich `UserSchema` with `email`, `role`, `is_active`, `tenant_id` fields
- [x] 3.2 Create `UpdateProfileSchema` input schema (`name?`, `email?`)

## Phase 4: Use Cases

- [x] 4.1 Create `GetUserProfileCase` — returns `current_user` as-is
- [x] 4.2 Create `UpdateUserProfileCase` — email uniqueness check via `exists_by_email_excluding_user`, then `repo.update_data`
- [x] 4.3 Create `ListUsersCase` — calls `repo.list()` with pagination, search, role params
- [x] 4.4 Create `SoftDeleteUserCase` — guards: not self, not last OWNER, same tenant → `repo.update_data(is_active=False)`

## Phase 5: Routes & DI

- [x] 5.1 Add `GET /users/me` to `auth_router` — returns `UserSchema`
- [x] 5.2 Add `PUT /users/me` to `auth_router` — accepts `UpdateProfileSchema`
- [x] 5.3 Add `GET /users` to `role_router` — paginated list, `require_role(ADMIN)`
- [x] 5.4 Add `GET /users/{id}` to `role_router` — detail, `require_role(ADMIN)`
- [x] 5.5 Add `DELETE /users/{id}` to `role_router` — soft-delete, `require_role(ADMIN)`
- [x] 5.6 Create `user_dependencies.py` — DI wiring for 4 use cases (Annotated+Depends)

## Phase 6: Tests

- [x] 6.1 Unit test: `GetUserProfileCase` — assert returns current_user unchanged
- [x] 6.2 Unit test: `UpdateUserProfileCase` — test 409 on duplicate email, assert commit
- [x] 6.3 Unit test: `ListUsersCase` — test pagination passthrough, role filter
- [x] 6.4 Unit test: `SoftDeleteUserCase` — test self-block, last-OWNER block, cross-tenant block
- [x] 6.5 Unit test: `LoginUserService` — test inactive user raises 401
- [x] 6.6 Integration: `GET/PUT /users/me` — assert 200 + enriched schema
- [x] 6.7 Integration: `GET /users` — assert pagination, search filter, 403 for VIEWER
- [x] 6.8 Integration: `DELETE /users/{id}` — assert soft-delete, 400 on self-delete
