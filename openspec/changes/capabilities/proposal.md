# Proposal: capabilities

## Intent

Add file storage and real-time notification capabilities. Currently the API has no way to upload/retrieve images (e.g., animal photos) and no real-time channel for server→client notifications (email-only). This phase adds both foundational capabilities and the first domain use case for each.

## Scope

### In Scope
- **S3 File Storage**: `IFileStorageService` port (upload/download/delete/get_url) + `S3FileStorageService` adapter via boto3, S3 settings, health check, DI wiring
- **Animal Image Upload**: `UploadAnimalImageUseCase` in cattle module, `POST /cattle/animals/{id}/images` endpoint
- **WebSocket Real-time**: Connection manager with Redis Pub/Sub (per tenant), `/ws/notifications` endpoint with JWT auth, EventBus subscriber → WS broadcast
- **Dependencies**: `boto3` and `python-multipart` added to `pyproject.toml`

### Out of Scope
- Direct file download endpoints (use S3 pre-signed URLs via `get_url`)
- File deletion endpoints (use S3 lifecycle policies)
- Chat/bidirectional messaging (server→client only)
- Multiple file types per domain (start with animal images only)

## Capabilities

### New Capabilities
- `file-storage`: S3 port/adapter for upload, download, delete, and pre-signed URL generation
- `animal-image-upload`: First domain use case — upload and associate images with animals in the cattle module
- `real-time-notifications`: WebSocket endpoint + Redis Pub/Sub per tenant for server→client event broadcasts

### Modified Capabilities
None — no existing spec behavior changes. The EventBus subscriber is a new handler, not a spec change to domain-events.

## Approach

Port/adapter pattern (same as `ICacheService` → `RedisCacheService`):
- `IFileStorageService` in `src/common/domain/ports/`, `S3FileStorageService` in adapters using `asyncio.to_thread()` for sync boto3 calls
- `UploadAnimalImageUseCase` in `src/cattle/application/use_cases/`
- WebSocket connection manager with Redis Pub/Sub per tenant channel (`notifications:{tenant_id}`), auth via JWT query param, EventBus handler publishes to Redis
- S3 health check added to existing `/health` endpoint; env vars in `Settings`
- All DI via `Annotated[Type, Depends(factory)]` type aliases

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `src/common/domain/ports/` | +New | `IFileStorageService` port |
| `src/common/infrastructure/adapters/` | +New | `S3FileStorageService` adapter |
| `src/common/infrastructure/core/_config.py` | Modified | Add S3 env vars |
| `src/cattle/application/` | +New | `UploadAnimalImageUseCase` |
| `src/cattle/infrastructure/presentation/routers/` | +New | Image upload endpoint |
| `src/common/infrastructure/presentation/routers/` | +New | `/ws/notifications` WebSocket endpoint |
| `src/common/infrastructure/events/` | +New | WebSocket EventBus handler |
| `main.py` | Modified | S3 health check in lifespan |
| `pyproject.toml` | Modified | Add `boto3`, `python-multipart` |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| S3 credentials misconfigured on deploy | Med | Startup health check with clear error message |
| WS auth token exposed in URL query param | Med | Enforce WSS in non-dev, short-lived tokens, log redaction |
| Redis Pub/Sub memory leak with many tenants | Low | Tenant TTL, connection limits, periodic cleanup |
| `asyncio.to_thread` overhead for S3 ops | Low | Acceptable for image uploads; move to `aioboto3` later if needed |

## Rollback Plan

- Remove S3 env vars from `Settings` and `.env.example`
- Remove `IFileStorageService` / `S3FileStorageService` and all references
- Remove WebSocket endpoint + connection manager + EventBus handler
- Revert `pyproject.toml` dependency additions
- Revert `main.py` lifespan changes

## Dependencies

- `boto3` — AWS S3 SDK (sync, called via `asyncio.to_thread`)
- `python-multipart` — FastAPI `UploadFile` parsing
- Existing Redis instance — Pub/Sub channels for WebSocket broadcasting
- S3-compatible storage (AWS S3 or MinIO for dev/test)

## Success Criteria

- [ ] Unit tests for `IFileStorageService` port contract + `S3FileStorageService` adapter (mocked boto3)
- [ ] Unit tests for `UploadAnimalImageUseCase` (mocked file storage)
- [ ] Unit tests for WebSocket connection manager + EventBus broadcast
- [ ] Health check reports S3 status (`"ok"` / `"unreachable"`)
- [ ] `POST /cattle/animals/{id}/images` returns 201 with image URL
- [ ] WebSocket client receives notification after a domain event is published
- [ ] Integration: `.env.example` documents S3_* vars
