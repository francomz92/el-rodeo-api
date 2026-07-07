# Proposal: User Management — Phase 5

## Intent

Complete user profile management (self-service) and admin user CRUD. Users currently have no way to view or update their own profile, and admins have no way to browse or deactivate users. The `UserSchema` only exposes `id, created_at, name, dni` — missing `email`, `role`, `is_active`, `tenant_id`.

## Scope

### In Scope
- Profile: `GET /users/me` — read own profile
- Profile: `PUT /users/me` — update name, email
- Admin: `GET /users` — paginated, tenant-scoped, searchable by name/email
- Admin: `GET /users/{id}` — user detail within tenant
- Admin: `DELETE /users/{id}` — soft-delete (set `is_active=false`)
- Enrich `UserSchema` with `email`, `role`, `is_active`, `tenant_id`
- Login guard: reject auth for `is_active=false` users
- `list_users()` on `IUserRepository` (paginated, filterable)

### Out of Scope
- Avatar upload/storage
- User preferences/settings
- Tenant management (CRUD, config)
- Hard-delete (GDPR is separate at `DELETE /users/me/data`)
- Password change (exists at `POST /password-change`)

## Capabilities

### New Capabilities
- `user-profile`: Self-service profile read/update for authenticated users
- `user-admin`: Admin user listing, detail, and soft-deletion (requires ADMIN/OWNER)

### Modified Capabilities
- `auth`: Enrich `UserSchema` with `email`, `role`, `is_active`, `tenant_id`; add `is_active` check in login flow
- `rbac`: New admin routes require `UserRole.ADMIN` or `UserRole.OWNER`

## Approach

- Add `list_users()` to `IUserRepository` (paginated, tenant-scoped, optional name/email search)
- Create use cases: `GetUserProfileCase`, `UpdateUserProfileCase`, `ListUsersCase`, `SoftDeleteUserCase`
- Create router `_user_routers.py` for profile + admin endpoints
- Enrich `UserSchema` with new fields
- Update `LoginUserService.validate_credentials` to check `user.is_active`
- Soft-delete is a single field toggle (`is_active=false`) via repository

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/auth/domain/repositories/users_repository_port.py` | Modified | Add `list_users()` abstract method |
| `src/auth/application/uses_cases/` | New | 4 new use case files |
| `src/auth/domain/services/login_user_service.py` | Modified | Add `is_active` check |
| `src/auth/infrastructure/persistence/repositories/user_repository.py` | Modified | Implement `list_users()` |
| `src/auth/infrastructure/adapters/http/output/user_schemas.py` | Modified | Enrich fields |
| `src/auth/infrastructure/presentation/routers/_user_routers.py` | New | Profile + admin endpoints |
| `src/auth/infrastructure/presentation/dependencies/user_dependencies.py` | New | DI wiring for new use cases |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Existing login breaks for inactive users | Low | Intentional — soft-deleted users must not authenticate |
| List query performance on large tenants | Low | Pagination with sensible defaults (20/page, max 100) |

## Rollback Plan

Revert routes, use cases, and `UserSchema` changes. Remove `list_users` from `IUserRepository`. Remove `is_active` login check. Restore old `UserSchema`.

## Dependencies

None — all within auth bounded context.

## Success Criteria

- [ ] `GET /users/me` returns full profile with `email`, `role`, `is_active`, `tenant_id`
- [ ] `PUT /users/me` updates name and email
- [ ] `GET /users` returns paginated, tenant-scoped user list
- [ ] `GET /users/{id}` returns a single user
- [ ] `DELETE /users/{id}` sets `is_active=false`
- [ ] Soft-deleted user cannot log in
- [ ] Non-admin users get 403 on admin routes
