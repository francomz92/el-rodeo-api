# Tasks: Phase 9c — Capabilities (File Storage, Animal Images, Real-Time Notifications)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~750–900 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1: S3 Storage Infra → PR 2: Animal Image Upload → PR 3: WebSocket Notifications |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | S3 port/adapter + settings + client singleton + health check + DI | PR 1 (base = main) | Tests included; boto3/python-multipart deps |
| 2 | UploadAnimalImageUseCase + entity/model/schema changes + endpoint + DI wiring | PR 2 (depends on PR 1) | Tests included; integrates S3 infra |
| 3 | ConnectionManager + WS endpoint + JWT auth + Redis Pub/Sub + EventBus handler + lifespan | PR 3 (base = main, independent) | Tests included; standalone WS capability |

## Phase 1: S3 File Storage Foundation

- [x] 1.1 Create `src/common/domain/ports/file_storage.py` — `IFileStorageService` ABC (upload/download/delete/get_url)
- [ ] 1.2 Create `src/common/domain/exceptions.py` — add `S3FileStorageError(Exception)` *(deferred — not needed until error handling is required by use cases)*
- [x] 1.3 Modify `src/common/infrastructure/core/_config.py` — add S3_BUCKET, S3_REGION, S3_ACCESS_KEY, S3_SECRET_KEY, S3_ENDPOINT
- [x] 1.4 Create `s3 client singleton` — built into `S3FileStorageService.__init__()` (avoids extra indirection)
- [x] 1.5 Create `src/common/infrastructure/adapters/s3_file_storage.py` — `S3FileStorageService` wrapping sync boto3 via `asyncio.to_thread()`
- [x] 1.6 Create `src/common/infrastructure/presentation/dependencies/storage.py` — `GetFileStorageService = Annotated[IFileStorageService, Depends(_get_s3_service)]`
- [x] 1.7 Modify `pyproject.toml` — add `boto3`, `python-multipart`
- [x] 1.8 Modify `.env.example` — add S3_* env vars with MinIO defaults

## Phase 2: S3 Health Check + Wiring

- [x] 2.1 Modify `main.py` — add S3 `head_bucket` health check in lifespan (log CRITICAL but continue on failure)
- [x] 2.2 Modify `src/common/infrastructure/presentation/routers/health.py` — add `s3: str` field to `HealthResponse`; check S3 reachability
- [x] 2.3 Test: Create `tests/unit/common/test_file_storage_port.py` — verify port contract (5 tests)
- [x] 2.4 Test: Create `tests/unit/common/test_s3_file_storage.py` — mock boto3, verify upload/download/delete/get_url/check_connection (13 tests)

## Phase 3: Animal Image Domain + Use Case

- [ ] 3.1 Modify `src/cattle/domain/entities/animal_entity.py` — add `image_url: str | None = None` field *(deferred — not needed until image_url is persisted on the entity)*
- [ ] 3.2 Modify `src/cattle/infrastructure/persistence/models/_animal_models.py` — add `image_url: Mapped[str | None]` column (nullable, String) *(deferred)*
- [ ] 3.3 Modify `src/cattle/infrastructure/adapters/http/output/animal_schemas.py` — add `image_url: str | None = None` to `AnimalSchema` *(deferred)*
- [x] 3.4 Create `src/cattle/application/uses_cases/animals_use_cases/upload_animal_image_case.py` — `UploadAnimalImageCase`: verify animal exists for tenant, generate S3 key, upload via IFileStorageService, return url + key
- [x] 3.5 Modify `src/cattle/infrastructure/presentation/dependencies/animals.py` — add `_get_upload_animal_image_case()` factory + `GetUploadAnimalImageCase` type alias; wire IFileStorageService + UoW
- [x] 3.6 Modify `src/cattle/infrastructure/presentation/routers/_animals.py` — add `POST /{animal_id}/images` endpoint (multipart, EDITOR role, 10 MB limit, image/ MIME check)
- [x] 3.7 Test: Create `tests/unit/cattle/test_upload_animal_image_case.py` — mock `IAnimalsRepository` + `IFileStorageService`, verify happy path, type validation, size validation, animal-not-found (5 tests)
- [x] 3.8 Test: Create `tests/unit/presentation/test_animal_image_upload.py` — `TestClient` upload to valid/invalid animal, non-image file, missing file, use case ValueError (4 tests)

## Phase 4: WebSocket Connection Manager

- [x] 4.1 Create `src/common/infrastructure/adapters/websocket/__init__.py` — package init
- [x] 4.2 Create `src/common/infrastructure/adapters/websocket/manager.py` — `ConnectionManager`: per-tenant `dict[UUID, set[WebSocket]]` with connect/disconnect/broadcast, stale connection cleanup
- [x] 4.3 Create `src/common/infrastructure/presentation/dependencies/websocket.py` — `GetWsManager` singleton factory (app-scoped, not request-scoped)
- [x] 4.4 Test: Create `tests/unit/common/test_websocket_manager.py` — connect/disconnect tenant isolation, broadcast skips stale connections, empty tenant cleanup (15 tests)

## Phase 5: WebSocket Endpoint + Auth

- [x] 5.1 Create `src/common/infrastructure/presentation/routers/ws.py` — `/ws/notifications` endpoint: JWT via `token` query param, extract `tenant_id`, register via `ConnectionManager`, close with 4001 on invalid/expired/missing token
- [x] 5.2 Modify `src/common/infrastructure/presentation/routers/__init__.py` — register `ws_router` at root level (no prefix)
- [x] 5.3 Test: Create `tests/unit/presentation/test_websocket_endpoint.py` — valid token connects, missing/expired token rejected 4001, disconnect cleans up manager (6 tests)

## Phase 6: Redis Pub/Sub + EventBus Integration

- [x] 6.1 Create `src/common/infrastructure/events/handlers/ws_broadcast.py` — EventBus handler that publishes events to Redis Pub/Sub channel `notifications:{tenant_id}`
- [x] 6.2 Modify `main.py` — register background Redis subscriber asyncio task in lifespan (subscribe `notifications:*` → `ConnectionManager.broadcast()` per tenant); include graceful shutdown
- [x] 6.3 Test: Create `tests/unit/common/test_ws_broadcast_handler.py` — mock Redis client, verify handler publishes to correct channel with event payload (5 tests)
- [x] 6.4 Test: Create `tests/unit/common/test_ws_subscriber.py` — mock `_handle_message` and ConnectionManager, verify message forwarding logic (9 tests)
