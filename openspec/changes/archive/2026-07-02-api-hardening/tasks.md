# Tasks: API Hardening — Phase 8

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~150–175 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | 3 stacked PRs to main |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: stacked-to-main
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | Security Hardening (core) | PR 1 → main | Error leak, body limit, rate limiting, CORS validation, sanitize logging |
| 2 | Input Validation | PR 2 → main | Schema constraints, CSP expansion |
| 3 | Cleanup | PR 3 → main | Remove unused deps, proxy IP helper |

## Phase 1: Security Hardening — PR 1

- [x] 1.1 `server_error.py`: replace `str(exc)` with hardcoded generic message, use `log.exception` for full traceback
- [x] 1.2 Create `body_size_limit.py` ASGI middleware checking `Content-Length` against `MAX_REQUEST_BODY_SIZE`
- [x] 1.3 `__init__.py`: import `BodySizeLimitMiddleware`, register after TrustedHost, before CORS in middleware chain
- [x] 1.4 `_config.py`: add `MAX_REQUEST_BODY_SIZE: int = 10_485_760`, `SANITIZE_QUERY_KEYS: list[str]`, `RATE_LIMIT_DEFAULT: str = "100/minute"`
- [x] 1.5 `rate_limiter.py`: set `default_limits=[settings.RATE_LIMIT_DEFAULT]` on `Limiter()` init
- [x] 1.6 `request_logging.py`: parse query string via `urllib.parse`, redact values for keys in `settings.SANITIZE_QUERY_KEYS`
- [x] 1.7 `correlation_id.py`: validate `X-Request-ID` — max 64 chars, alphanumeric + hyphens only, drop invalid
- [x] 1.8 `_config.py`: add `model_validator(mode="after")` — `log.critical` if wildcard `*` in `CORS_ORIGINS`/`TRUSTED_HOSTS` in non-dev environment

## Phase 2: Input Validation — PR 2

- [x] 2.1 `authentication_schemas.py`: `RegisterSchema.email` → `EmailStr`
- [x] 2.2 `user_schemas.py`: add `max_length=100` on `name`, `EmailStr` on `email`
- [x] 2.3 `animal_schemas.py`: add `gt=0` to `initial_weight`, `last_weight` in `AnimalCreationSchema`/`AnimalUpdateSchema`
- [x] 2.4 `sale_schemas.py`: add `gt=0` to `price`, `price_per_kg`, `weight` in `SaleCreateSchema`
- [x] 2.5 `animal_supplies_schemas.py`: add `max_length=100` on `name` in `AnimalSuppliesCreateSchema`
- [x] 2.6 `security_headers.py`: expand CSP with `script-src 'self'`, `style-src 'self'`, `img-src 'self' data:`, `connect-src 'self'`, `base-uri 'self'`, `form-action 'self'`
- [x] 2.7 `_config.py`: add `CSP_DIRECTIVES: dict` setting for full CSP configurability

## Phase 3: Cleanup — PR 3

- [x] 3.1 `pyproject.toml`: remove `passlib`, `pyotp`, `fastapi-csrf-protect` from dependencies
- [x] 3.2 Create `ip_utils.py` with `get_client_ip()` — reads `X-Forwarded-For` first, falls back to `request.client.host`
- [x] 3.3 `rate_limiter.py`: replace `get_remote_address` with `get_client_ip` as `Limiter(key_func=...)`
