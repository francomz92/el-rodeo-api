# Design: Phase 9c — Capabilities (File Storage, Animal Images, Real-Time Notifications)

## Technical Approach

Three new capabilities layered on the existing port/adapter architecture. `IFileStorageService` port follows `ICacheService` exactly: ABC in `domain/ports/`, sync adapter in `infrastructure/adapters/` wrapped via `asyncio.to_thread()`. WebSocket notifications reuse the existing Redis connection and EventBus — a handler registered with `"*"` publishes to Redis Pub/Sub, and a background asyncio task fans out to per-tenant in-memory connections. Animal image upload is the first domain consumer, gated by `EDITOR` role, tenant-scoped S3 keys.

## Architecture Decisions

### Decision: Sync boto3 via asyncio.to_thread vs aioboto3

| Option | Tradeoff |
|--------|----------|
| **asyncio.to_thread + sync boto3** | Simpler deps, battle-tested API, acceptable for image uploads |
| aioboto3 | Native async but historically unstable API surface |

**Choice**: `asyncio.to_thread`. Image uploads are not a hot path — thread-pool overhead is negligible.

### Decision: Redis Pub/Sub vs Redis Streams for WS fan-out

| Option | Tradeoff |
|--------|----------|
| **Pub/Sub** | Fire-and-forget, no consumer groups, exactly what notifications need |
| Streams | Persistence, consumer groups, ack — overkill for ephemeral WS messages |

**Choice**: Pub/Sub. Lost messages are acceptable for real-time notifications; the source of truth is the DB.

### Decision: JWT via query param vs first-message auth

| Option | Tradeoff |
|--------|----------|
| **Query param `token`** | Standard WebSocket auth — browsers can't set headers on upgrade |
| First-message auth | Requires two-phase handshake, more complex client code |

**Choice**: Query param `token`. Mitigated by enforcing WSS in non-dev and short-lived access tokens.

### Decision: Wildcard "*" handler vs per-event-type registration

| Option | Tradeoff |
|--------|----------|
| **`"*"` wildcard** | Single handler catches all events, filters by `tenant_id` in metadata |
| Per-type registration | Explicit, but requires updating when new event types are added |

**Choice**: `"*"` initially. The WS handler already ignores events without `tenant_id` metadata. Optimize per-type if volume requires it.

## Data Flow

```text
── Animal Image Upload ─────────────────────────────────────────

Client ──POST /cattle/animals/{id}/images──→ Router
  │                                              │
  │    UploadAnimalImageUseCase.execute()         │
  │      ├─ 1. Verify animal exists (DB repo)     │
  │      ├─ 2. Validate content_type starts with  │
  │      │      "image/"                          │
  │      ├─ 3. Generate S3 key:                   │
  │      │   animals/{tenant}/{animal}/{uuid}.ext │
  │      ├─ 4. IFileStorageService.upload()       │
  │      │      └─ asyncio.to_thread → boto3      │
  │      │         put_object(Bucket, Key, Body)  │
  │      ├─ 5. Update animal.image_url in DB      │
  │      └─ 6. Return {"url": ..., "key": ...}    │
  │                                              │
  └── 201 ←──────────────────────────────────────┘

── WebSocket Notification ─────────────────────────────────────

Domain Use Case                     EventBus
     │                                 │
     │ dispatch(event) ────────────────┤
     │                                 │
     │              ┌──────────────────┤
     │              │ OutboxScheduler  │
     │              │ (*)              │
     │              └──────────────────┤
     │              ┌──────────────────┤
     │              │ WSHandler(*)     │
     │              │  └─ Redis PUB    │
     │              │    notifications │
     │              │    :{tenant_id}  │
     │              └──────────────────┤
     │                                 │
     │                                 │  Redis
     │                                 │  Pub/Sub
     │                                 │
     │              BG Task (instance) │
     │              ┌──────────────────┤
     │              │ SUB notifications│
     │              │ :{tenant_id}     │
     │              │  → ConnectionMgr │
     │              │    .broadcast()  │
     │              │     → WS send()  │
     │              └──────────────────┘
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `src/common/domain/ports/file_storage.py` | Create | `IFileStorageService` ABC with upload/download/delete/get_url |
| `src/common/domain/exceptions.py` | Modify | Add `S3FileStorageError` exception class |
| `src/common/infrastructure/adapters/s3_file_storage.py` | Create | `S3FileStorageService(IFileStorageService)` wrapping sync boto3 via `asyncio.to_thread` |
| `src/common/infrastructure/core/_config.py` | Modify | Add `S3_BUCKET`, `S3_REGION`, `S3_ACCESS_KEY`, `S3_SECRET_KEY`, `S3_ENDPOINT` |
| `src/common/infrastructure/presentation/dependencies/storage.py` | Create | `GetFileStorageService` Annotated dependency |
| `src/common/infrastructure/persistence/connections/s3.py` | Create | `_s3_client` singleton (boto3 client from settings) |
| `src/common/infrastructure/adapters/websocket/manager.py` | Create | `ConnectionManager` — per-tenant in-memory WS dict |
| `src/common/infrastructure/adapters/websocket/__init__.py` | Create | Package init |
| `src/common/infrastructure/presentation/dependencies/websocket.py` | Create | `GetWsManager` singleton dependency |
| `src/common/infrastructure/presentation/routers/notifications.py` | Create | `/ws/notifications` WebSocket endpoint with JWT auth |
| `src/common/infrastructure/events/handlers/ws_notifier.py` | Create | EventBus handler that publishes events to Redis Pub/Sub |
| `src/common/infrastructure/core/app.py` | Modify | Register background Redis subscriber task in lifespan |
| `main.py` | Modify | Add S3 `head_bucket` check in lifespan |
| `src/common/infrastructure/presentation/routers/health.py` | Modify | Add `s3` field to `HealthResponse` |
| `src/cattle/application/use_cases/upload_animal_image_case.py` | Create | `UploadAnimalImageUseCase` |
| `src/cattle/infrastructure/presentation/dependencies/animals.py` | Modify | Add `_get_upload_animal_image_case()` factory + `GetUploadAnimalImageCase` type alias |
| `src/cattle/infrastructure/presentation/routers/_animals.py` | Modify | Add `POST /{id}/images` endpoint |
| `src/cattle/domain/entities/animal_entity.py` | Modify | Add `image_url: str \| None = None` field |
| `src/cattle/infrastructure/persistence/models/_animal_models.py` | Modify | Add `image_url` column (nullable String) |
| `src/cattle/infrastructure/adapters/http/output/animal_schemas.py` | Modify | Add `image_url: str \| None` to `AnimalSchema` |
| `.env.example` | Modify | Add S3_* env vars |
| `pyproject.toml` | Modify | Add `boto3`, `python-multipart` |

## Interfaces / Contracts

```python
# src/common/domain/ports/file_storage.py
class IFileStorageService(ABC):
    @abstractmethod
    async def upload(self, file: bytes, key: str, content_type: str) -> str: ...
    @abstractmethod
    async def download(self, key: str) -> bytes: ...
    @abstractmethod
    async def delete(self, key: str) -> None: ...
    @abstractmethod
    async def get_url(self, key: str, expire_seconds: int = 3600) -> str: ...
```

```python
# src/common/domain/exceptions.py  (addition)
class S3FileStorageError(Exception):
    """Raised on S3 operation failures."""
```

```python
# ConnectionManager — per-tenant in-memory WebSocket registry
class ConnectionManager:
    _connections: dict[UUID, set[WebSocket]]
    def connect(self, ws: WebSocket, tenant_id: UUID) -> None: ...
    def disconnect(self, ws: WebSocket) -> None: ...
    async def broadcast(self, tenant_id: UUID, message: dict) -> None: ...
```

```python
# WS notification payload (sent to client)
{ "type": "notification", "event_type": "animal.created", "data": { ... } }
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | `IFileStorageService` contract | Port contract test verifying adapter behavior (mocked boto3) |
| Unit | `UploadAnimalImageUseCase` | Mock both `IAnimalsRepository` and `IFileStorageService` |
| Unit | `ConnectionManager` | Direct unit tests for connect/disconnect/broadcast edge cases |
| Unit | WS background subscriber | Mock Redis pubsub loop and `ConnectionManager` |
| Unit | EventBus WS handler | Verify handler publishes to correct Redis channel |
| Integration | S3 adapter (MinIO) | Use testcontainers or MinIO in docker-compose for real S3 ops |
| Integration | Full WS flow | `TestClient` WebSocket connect + publish domain event + verify message |

## Migration / Rollout

No data migration required. The `image_url` column on the `animals` table is nullable — existing rows are unaffected. The WebSocket and S3 capabilities are opt-in from day one (no existing behavior changes).

## Open Questions

- [ ] Should the WS subscriber task be registered in the FastAPI lifespan or as a Celery worker? (FastAPI lifespan — it's an asyncio task tied to the HTTP process, not background job processing)
- [ ] Confirm whether the existing `DomainEvent.metadata` is populated with `tenant_id` by use cases, or needs to be added to the dispatch call sites
