# Design: API Hardening — Phase 8

## Technical Approach

Three stacked PRs to main targeting 15 security gaps found in exploration. Each PR is independently verifiable and revertable. Minimal new code — mostly modifications to existing middleware, schemas, and config. No new external dependencies.

---

## PR 1 — Security Hardening (core)

### 1. Fix 500 Error Leak

| File | Change |
|------|--------|
| `server_error.py` | Replace `message=str(exc)` with `"Error interno del servidor"` |
| same file | Swap `log.error(...)` for `log.exception(...)` to capture full traceback server-side |

**Approach**: The catch-all `server_exception_handler` leaks `str(exc)` in JSON responses. Change the `ErrorPayloadSchema.message` to a hardcoded generic string. Use loguru's `log.exception()` which automatically captures the traceback in the log record — no `str(exc)` needed in the log call either.

### 2. Request Body Size Limit Middleware — New

| File | Action |
|------|--------|
| `src/.../middlewares/body_size_limit.py` | **Create** — ASGI middleware |
| `middlewares/__init__.py` | Modify — register in chain |
| `_config.py` | Modify — add `MAX_REQUEST_BODY_SIZE: int = 10_485_760` |

**Approach**: ASGI middleware that checks `Content-Length` header in the request scope. If present and exceeding `settings.MAX_REQUEST_BODY_SIZE`, return 413 with the standard error format. If `Content-Length` is absent (chunked), we read first bytes up to the limit — but for simplicity, rely on `Content-Length` first. Registered **after TrustedHost, before CORS** to reject oversized bodies early.

```python
class BodySizeLimitMiddleware:
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):
        self.app = app
        self.max_size = max_size

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = dict(scope.get("headers", []))
        content_length = headers.get(b"content-length")
        if content_length and int(content_length) > self.max_size:
            # return 413 immediately
            ...
        await self.app(scope, receive, send)
```

### 3. Global Rate Limiting

| File | Change |
|------|--------|
| `rate_limiter.py` | Add `default_limits=["100/minute"]` to `Limiter()` init |
| `rate_limiter.py` | Create `get_client_ip()` helper respecting `X-Forwarded-For` |
| `rate_limiter.py` | Add `RATE_LIMIT_DEFAULT` as the default limit string |
| `_config.py` | Add `RATE_LIMIT_DEFAULT: str = "100/minute"` |
| `_config.py` | Add `RATE_LIMIT_KEY_FUNC: str = "ip"` (for future switching) |

**Approach**: slowapi's `Limiter(default_limits=["100/minute"])` applies to every route automatically. The `@rate_limit()` decorator overrides the default for specific endpoints (it calls `limiter.limit(...)` which overrides rather than compounds). `get_client_ip()` reads `X-Forwarded-For` first, falls back to `request.client.host` — used as `key_func` instead of slowapi's `get_remote_address`.

The `EXEMPT_PATHS` list already skips health, metrics, docs — unchanged.

### 4. CORS / TrustedHost per Environment

| File | Change |
|------|--------|
| `_config.py` | Add `model_validator(mode="after")` — log CRITICAL if `["*"]` in non-dev environment |
| `cors.py` | No code change — already logs warning for wildcards |
| `trusted_host.py` | No code change — middleware reads `TRUSTED_HOSTS` from settings |

**Approach**: Keep wildcard defaults for dev ergonomics. On `Settings` construction (via `model_validator(mode="after")`), if `ENVIRONMENT != EnvironmentType.DEVELOPMENT` and `"*" in CORS_ORIGINS` or `"*" in TRUSTED_HOSTS`, emit a `log.critical()` warning. This is non-blocking — ops can still deploy but the startup log makes misconfiguration visible.

### 5. Sanitize Query String Logging

| File | Change |
|------|--------|
| `request_logging.py` | Parse query string and redact sensitive parameter values |
| `_config.py` | Add `SANITIZE_QUERY_KEYS: list[str] = ["password", "token", "secret", "key", "api_key"]` |

**Approach**: After decoding `query_string`, parse with `urllib.parse.parse_qs`, iterate keys, replace values for any key in `SANITIZE_QUERY_KEYS` with `"***"`, re-encode. Log the sanitized version. Minimal overhead — query strings are typically small.

---

## PR 2 — Input Validation

### 6–7. Schema Constraints (Auth)

| File | Change |
|------|--------|
| `authentication_schemas.py` | `RegisterSchema.email`: change `str` to `EmailStr` (from `pydantic`) |
| `user_schemas.py` | `UpdateProfileSchema.name`: add `max_length=100`; `.email`: change to `EmailStr` |

**Approach**: Pydantic's `EmailStr` enables format validation (RFC-like) natively — no regex needed. `max_length` on `name` prevents arbitrarily long strings. Both cause 422 on violation, consistent with existing validation error handling.

### 8. Domain Schema Constraints

| File | Change |
|------|--------|
| `animal_schemas.py` | `AnimalCreationSchema.initial_weight`: add `gt=0` |
| `animal_schemas.py` | `AnimalCreationSchema.caravana`: already `max_length=50` — OK |
| `animal_schemas.py` | `AnimalUpdateSchema.*`: add `gt=0` to weight fields |
| `sale_schemas.py` | `SaleCreateSchema.price`, `price_per_kg`, `weight`: add `gt=0` |

**Approach**: Pydantic `Field(gt=0)` on numeric fields that must be positive. Prevents zero/negative values at the API boundary before they reach domain logic.

### 9. CSP Directives

| File | Change |
|------|--------|
| `security_headers.py` | Expand CSP from `default-src 'self'` to full policy |
| `_config.py` | Add `CSP_DIRECTIVES: dict[str, str]` for full configurability |

**Approach**: Current CSP only sets `default-src 'self'`. Expand to:
```python
CSP = (
    f"default-src 'self'; "
    f"script-src 'self'; "
    f"style-src 'self'; "
    f"img-src 'self' data:; "
    f"connect-src 'self'; "
    f"base-uri 'self'; "
    f"form-action 'self'"
)
```
Still set from settings so staging/prod can override.

---

## PR 3 — Cleanup

### 10. Remove Unused Dependencies

| File | Change |
|------|--------|
| `pyproject.toml` | Remove `passlib>=1.7.4`, `pyotp>=2.9.0`, `fastapi-csrf-protect>=0.3.1` |

**Approach**: These packages are imported nowhere in the codebase (verified in exploration). Removing them reduces the attack surface and dependency count.

### 11. Proxy IP Detection Helper

| File | Action |
|------|--------|
| `src/.../middlewares/ip_utils.py` | **Create** — `get_client_ip` helper |
| `rate_limiter.py` | Use `get_client_ip` as `key_func` instead of slowapi's `get_remote_address` |

**Approach**:
```python
def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = request.client
    return client[0] if client else "127.0.0.1"
```

This replaces `slowapi.util.get_remote_address` in the `Limiter(key_func=...)`. Behind a reverse proxy, slowapi's default key always returns the proxy IP, making rate limiting ineffective for per-IP enforcement.

---

## Middleware Registration Order (Updated)

```
TrustedHost → BodySizeLimit → CORS → RateLimiter → SecurityHeaders → CorrelationId → RequestLogging → GZip
```

TrustedHost is outermost to validate the `Host` header before any body processing. `BodySizeLimitMiddleware` comes second to reject oversized payloads before body reading. CORS handles OPTIONS preflight after body size validation. Observability middleware (CorrelationId, RequestLogging) sits towards the inner side so it captures the full pipeline. `ip_utils.py` is a utility module — not middleware.

## Testing Strategy

| Layer | What | Approach |
|-------|------|----------|
| Unit | 500 error leak | Add assertion: `body["error"]["message"]` is generic; update existing test that checks for `str(exc)` in message |
| Unit | Body size limit | Mock middleware with small limit, verify 413 vs 200 |
| Unit | Rate limiter key func | Test `get_client_ip()` with/without `X-Forwarded-For` |
| Unit | Schema constraints | Pydantic validation tests — `EmailStr`, `gt=0`, `max_length` |
| Unit | Query sanitization | Parse URL with sensitive params, verify redacted output |
| Unit | CSP header composition | Verify header string contains all expected directives |
| Integration | Global rate limit | Full app with low default limit, verify 429 on non-auth endpoint |
| Integration | CORS/TrustedHost warning | Patch `DEBUG=False`, verify `log.critical` called with wildcard |
| Integration | End-to-end body limit | POST >10MB, verify 413 |

## Open Questions

- [ ] **Log level for `log.exception()`**: Loguru's `logger.exception()` is equivalent to `logger.error()` + traceback. The current handler uses `log.error()` — should we keep ERROR level? Yes — unhandled exceptions are errors.
- [ ] **`X-Request-ID` log injection**: The exploration flagged this but it's not in specs. Add truncated validation (max 64 chars, alphanumeric only) to `CorrelationIdMiddleware` as a quick win?
