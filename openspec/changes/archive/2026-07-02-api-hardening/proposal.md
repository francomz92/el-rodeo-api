# Proposal: API Hardening

## Intent

Fix 15 security gaps found in Phase 8 exploration: exception leaks, no request body limit, CORS/TrustedHost wildcards, no global rate limiting, weak input validation, CSP gaps, and log injection surface. Prevent information disclosure, abuse, and misconfiguration in production.

## Scope

### In Scope
- Fix `server_error.py` exc leak in 500 responses
- Add request body size limit middleware (e.g., 1MB default)
- Add global rate limiting with low default + endpoint overrides
- Set safe CORS origins/headers and TrustedHosts per environment
- Sanitize query string from request logging
- Add CSP directives (script-src, style-src, etc.)
- Harden Pydantic constraints on auth and domain schemas
- Remove 3 unused deps: `passlib`, `pyotp`, `fastapi-csrf-protect`
- Fix proxy-aware rate limiter key function

### Out of Scope
- Reverse proxy config (WAF, nginx body limit, TLS termination)
- Multi-factor auth or SSO
- Static code analysis or dependency vulnerability scanning

## Capabilities

### New Capabilities
- `error-handling`: Safe 500 responses — no exception details leaked
- `request-body-limit`: Enforce max body size on all endpoints
- `rate-limiting`: Global default rate + endpoint overrides (not just auth)
- `cors-trusted-hosts`: Environment-aware CORS origins and TrustedHost
- `logging-sanitization`: Redact sensitive data from query strings/headers
- `content-security-policy`: Expanded CSP with script-src, style-src, etc.
- `input-validation`: Pydantic constraint hardening for all schemas

### Modified Capabilities
- `auth`: RegisterSchema.email must use EmailStr or regex validator
- `user-profile`: UpdateProfileSchema.name/email must have max_length

## Approach

- **PR 1 — Security Hardening (core)**: Fix exc leak, add body limit middleware, global rate limiting, env-safe CORS/TrustedHost, sanitize logging.
- **PR 2 — Input Validation**: Add Pydantic constraints to all schemas, expand CSP directives.
- **PR 3 — Cleanup**: Remove unused deps, fix proxy IP detection for rate limiter.
- Each PR is independently verifiable and reverts cleanly.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `server_error.py` | Modified | Remove `str(exc)` from response body |
| `rate_limiter.py` | Modified | Add global defaults, fix key_func for proxy |
| `_config.py` | Modified | Per-env CORS/TrustedHost defaults |
| `cors.py` | Modified | Validate origins per env |
| `request_logging.py` | Modified | Strip query string from log output |
| `security_headers.py` | Modified | Expand CSP directives |
| `correlation_id.py` | Modified | Validate/truncate X-Request-ID |
| All Pydantic schemas | Modified | Add constraints (EmailStr, gt, max_length) |
| `pyproject.toml` | Modified | Remove 3 unused deps |
| New middleware file | New | Request body size limit |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Global rate limiting breaks legit traffic | Low | Start with generous defaults, log-only mode first |
| CORS restriction breaks frontend | Low | Staging env with exact origin, test before prod deploy |
| Body limit rejects valid large requests | Low | Set 1MB default; add `settings.MAX_REQUEST_SIZE` |

## Rollback Plan

- **Per-PR revert**: Each PR reverts independently via `git revert <sha>`.
- **CORS/TrustedHost**: Restore `["*"]` defaults and redeploy.
- **Body limit**: Remove middleware from registration and redeploy.
- **Rate limiting**: Set `ENABLE_RATE_LIMIT=False` via env var.

## Dependencies

- `slowapi` for rate limiting (already present)
- No new external packages

## Success Criteria

- [ ] 500 responses return generic message, never `str(exc)`
- [ ] POST body >1MB rejected with 413
- [ ] Every non-auth endpoint has a rate limit (even if high)
- [ ] CORS and TrustedHost reject unauthorized origins/hosts in staging/prod
- [ ] Query strings absent from log output
- [ ] All Pydantic schemas have `EmailStr`, `max_length`, `gt`/`ge` as appropriate
- [ ] `passlib`, `pyotp`, `fastapi-csrf-protect` removed from dependencies
