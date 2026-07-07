## Exploration: Phase 8 — API Hardening

### Current State

The API hardening posture is a **mixed bag** — solid foundations in some areas, glaring gaps in others. The auth domain has received intentional security attention (token rotation, rate limiting on sensitive endpoints, blacklisting), but the rest of the API surface is largely unprotected.

### Findings Summary

| Area | Grade | Key Gaps |
|------|-------|----------|
| Rate Limiting | ⚠️ Partial | Only 4 auth endpoints protected; all domain CRUD endpoints open |
| Security Headers | ✅ Good | CSP, HSTS, XFO, nosniff present; minor enhancements possible |
| CORS | ⚠️ Weak | Defaults to `["*"]` for origins AND headers in `.env.example` |
| Input Validation | ⚠️ Inconsistent | Some schemas lack max_length; email has no format validation; UpdateProfileSchema has zero constraints |
| Error Handling | 🔴 Leaky | `server_error.py` exposes `str(exc)` in 500 response body |
| Body Size Limits | 🔴 Missing | No limit configured — potential DoS vector |
| Token Security | ✅ Good | 15-min access, 7-day refresh with rotation & family reuse detection, Redis blacklist |
| CSRF / MFA | 🔴 Not implemented | `fastapi-csrf-protect` and `pyotp` in dependencies but never wired |
| Logging | ⚠️ OK | Query string logged (sensitive data concern); request body NOT logged (good) |
| Trusted Host | ⚠️ Weak | Defaults to `["*"]` — middleware is effectively a no-op |
| Dead Dependencies | ⚠️ 3 | `passlib`, `pyotp`, `fastapi-csrf-protect` — listed but never imported |

---

### Detail Per Area

#### 1. Rate Limiting

- **What exists**: `slowapi` with Redis auto-detection (falls back to in-memory). Module-level `limiter` with `@rate_limit()` decorator gated by `settings.ENABLE_RATE_LIMIT`.
- **Protected**: `POST /login` (5/min), `POST /register` (3/min), `POST /password-change` (3/min), `POST /auth/refresh` (10/min)
- **Unprotected**: Every cattle, market, finance, and billing endpoint — no rate limiting at all.
- **Key function**: `get_remote_address` — no `X-Forwarded-For` trust configuration; behind a reverse proxy all traffic appears to come from the proxy IP.
- **Redis fallback**: Graceful degradation to in-memory if Redis is unreachable (logged).

#### 2. Security Headers

- `SecurityHeadersMiddleware` (custom ASGI): X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, CSP, HSTS
- CSP: `default-src 'self'` — configurable via settings but only sets `default-src`
- HSTS: `max-age=31536000; includeSubDomains` — correctly skipped in dev
- Tests exist in `tests/integration/common/test_security_headers_api.py` and `tests/unit/common/test_security_headers.py`
- **Missing**: `Cross-Origin-Resource-Policy`, `Cross-Origin-Opener-Policy`

#### 3. CORS

```python
ALLOWED_ORIGINS: list[str] = ["*"]
ALLOWED_HEADERS: list[str] = ["*"]  # accepts anything
```

Wildcard detection disables credentials (correct), but the `.env.example` ships with open CORS. Production deployment needs explicit origins.

#### 4. Input Validation

**Good examples** (auth):
- `LoginSchema`: `dni` (max_length=10), `password` (min_length=8, max_length=50)
- `ChangePasswordSchema`: All three fields have min/max length
- `RegisterSchema`: All fields have max_length

**Gaps**:
- `RegisterSchema.email` — **No email validation** (`max_length=100` only, no `EmailStr`, no regex)
- `UpdateProfileSchema` — **Zero constraints** on `name` or `email` (both `str | None = None`)
- `AnimalSuppliesCreateSchema.name` — **No max_length** (unlike its `UpdateSchema` counterpart which has it)
- `SaleCreateSchema.price`, `price_per_kg` — **No gt/ge bounds**
- `AnimalCreationSchema.initial_weight` — **No gt/ge bounds**
- `LoginSchema.dni` — No regex pattern for DNI format

#### 5. Error Handling

**Critical finding**: `server_error.py` (the catch-all handler):
```python
error=ErrorPayloadSchema(
    code="Internal server error",
    message=str(exc),  # 🔴 EXCEPTION MESSAGE LEAKED TO CLIENT
)
```

This means any unhandled `Exception` — including `ValueError`, `KeyError`, SQL errors, or 3rd-party SDK exceptions — gets its `str()` rendered in the API response. This is an **information disclosure** vulnerability.

All other exception handlers (domain, application, validation) are well-structured and don't leak internals.

#### 6. Request Body Size Limits

**None whatsoever**. No `max_body_size` configuration on the FastAPI app, no middleware checking `Content-Length`. A client could send a multi-gigabyte payload and it would be read into memory.

#### 7. Token / Auth Security

This is the **strongest area**:
- Access tokens: 15-min expiry, JTI (unique token ID), includes `iat` and `exp`
- Refresh tokens: 7-day expiry, family-based rotation with **reuse detection** (if a rotated token is reused, the entire family is revoked)
- Token blacklist: Redis-based with TTL matching remaining token validity
- Cookies: HttpOnly, Secure (configurable), SameSite=Strict, path-scoped
- Password hashing: `bcrypt` via `asyncio.to_thread` (non-blocking)
- JWT algorithm: HS256 (symmetric) — fine for single-service, but limits key distribution

**Not implemented** (but deps exist):
- `pyotp` installed — no MFA/2FA
- `fastapi-csrf-protect` installed — no CSRF protection

#### 8. Logging

- `RequestLoggingMiddleware` logs: method, path, query_string, client_ip, user_agent, correlation_id, status, duration
- Logs `query_string` — **could contain sensitive data** (e.g., tokens in query params)
- Does NOT log request body — good
- Does NOT log auth headers — good
- `X-Request-ID` from headers is reflected in logs AND in the `X-Request-ID` response header — potential **log injection** vector if not sanitized

#### 9. Dependencies

**Present but unused** (dead weight / security surface):
| Dependency | Version | Purpose | Status |
|-----------|---------|---------|--------|
| `passlib` | >=1.7.4 | Password hashing | 🔴 Unused — bcrypt used directly |
| `pyotp` | >=2.9.0 | TOTP/MFA | 🔴 Unused — no 2FA implemented |
| `fastapi-csrf-protect` | >=0.3.1 | CSRF tokens | 🔴 Unused — not imported anywhere |

**Security advisories**: `slowapi>=0.1.9` should be checked for latest version; no known critical CVEs found during scan.

---

### Immediate Risks (Priority Order)

1. **🔴 CRITICAL** — `str(exc)` leaked in 500 error responses → information disclosure
2. **🔴 HIGH** — No request body size limit → DoS via large payloads
3. **🔴 HIGH** — 0 rate limiting on ~80% of API → brute-force on non-auth endpoints
4. **🟡 MEDIUM** — `UpdateProfileSchema` has zero field validation → arbitrary-length strings accepted
5. **🟡 MEDIUM** — `RegisterSchema.email` has no format validation → invalid emails stored
6. **🟡 MEDIUM** — `get_remote_address` behind proxy → all traffic from same IP, rate limiting ineffective
7. **🟡 MEDIUM** — Logged `query_string` may contain sensitive data
8. **🟢 LOW** — 3 unused dependencies increase attack surface
9. **🟢 LOW** — Some finance/sale schemas missing numeric bounds

### Ready for Proposal
Yes — full coverage with concrete gaps identified. Recommend starting with **critical & high** items (error leakage, body size limits, rate limiting coverage) before moving to medium improvements.
