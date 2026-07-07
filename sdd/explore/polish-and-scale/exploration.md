## Exploration: Polish & Scale — Phase 9 Readiness

### Current State

The codebase is a well-structured Clean/Hexagonal FastAPI application (`el-rodeo-api`) for cattle and finance management for small producers. Currently at version `0.1.0`, it has **736 passing unit tests**, **147 passing integration tests** (41 integration tests failing), and 12 skipped. The app serves **5 domains** (auth, cattle, finance, market, billing) with proper separation of concerns.

Below is the detailed state of each area.

---

### 1. File Upload (S3/Supabase)

**Current State: NOTHING EXISTS**

- **No endpoints**: Zero file upload routes exist in any domain router
- **No SDKs**: `pyproject.toml` dependencies include no S3/Supabase/storage SDKs (`boto3`, `s3fs`, `supabase-py`, `python-multipart` are all absent)
- **No models**: No `File`, `Media`, `Attachment`, `Photo`, `Receipt`, `Invoice`, or `Document` entities or models exist
- **No services**: No upload, transform, or CDN service exists
- **Config**: `MAX_REQUEST_BODY_SIZE` is set (10MB) but no multipart config

**What files would be for**: Based on the domain structure:
- **Cattle**: Animal photos
- **Finance**: Purchase receipts, supply invoices
- **Billing**: Payment receipts, invoices
- **Auth**: User profile photos (avatar)

**Effort: High** — Full new feature from scratch
- Dependencies to add: `python-multipart` (FastAPI), `boto3` or `supabase-py`, `Pillow` or similar for image processing
- New domain/workflow: File domain or cross-cutting `MediaModule`
- Storage abstraction + CDN integration
- Would require a new `sdd-init` + full SDD cycle

---

### 2. WebSocket / Real-time (Redis pub/sub)

**Current State: NOTHING EXISTS**

- **No WebSocket support**: Zero occurrences of `websocket`, `socketio`, `WebSocket` in any Python file
- **FastAPI WebSocket**: Not used anywhere
- **Redis usage**: Redis is used for 3 things:
  1. **Celery broker + result backend** (`BROKER_URL`, `RESULT_BACKEND_URL`)
  2. **Token blacklist** (`RedisTokenBlacklistService` — synchronous TTL-based JWT revocation)
  3. **Rate limiter backend** (slowapi, switches to Redis in production)
- **No Redis pub/sub**: Only client-server Redis, no pub/sub channels used beyond Celery's internal protocol
- **No real-time notifications**: All notifications are email-based (Celery tasks → SMTP)

**Notifications architecture currently**: Celery Beat runs a daily `notify_upcoming_events` task that iterates all tenants and sends email reminders for scheduled events. No push/real-time delivery.

**Effort: Medium**
- Redis pub/sub already available (same Redis instance)
- FastAPI native WebSocket support (no extra deps)
- Would need: WebSocket router, connection manager, auth middleware for WS, frontend integration
- Pub/sub channels for: event reminders, billing notifications, data sync
- Low-hanging fruit: use an existing Redis connection + new WS routes

---

### 3. Webhook System (Domain Events)

**Current State: NOTHING EXISTS**

- **Only MP webhook**: A `/billing/webhooks/mercadopago` endpoint exists (MercadoPago IPN handler in `PaymentWebhookService`)
- **No generic event system**: Zero occurrences of `EventBus`, `DomainEvent`, `dispatch`, `publish`, `event_dispatcher` patterns
- **No domain events**: The codebase uses no DDD eventing pattern at all
- **Architecture style**: Synchronous request-response with UoW + repositories; no event-driven pathways
- **No outbox pattern**: No transactional outbox for reliable event delivery

**What would need to be built**:
- `DomainEvent` base class
- `EventBus` / `EventDispatcher` interface
- In-memory + Redis-backed implementations
- Webhook dispatch service (HTTP POST to configured URLs)
- Tenant webhook configuration (URL, secret, events subscribed)
- Outbox pattern for reliable delivery
- Retry + idempotency for webhook delivery

**Effort: High** — New architectural subsystem
- Foundational architectural change (from sync-only to event-driven)
- Would touch every domain (each would emit domain events)
- Database migration for webhook config + outbox tables
- Needs careful design to maintain current codebase quality

---

### 4. Performance Optimization

**N+1 Queries: LOW RISK (currently mitigated)**

- All repositories use **SQLAlchemy Core-style queries** with explicit `outerjoin` + column projection — no ORM lazy loading during reads
- `animal_repository.py`, `sales.py`, `purchases.py`, `animal_protocol_repository.py` all manually join their related tables in the SELECT
- `relationship()` declarations exist on models (e.g., `Animal.user`, `Sale.animal`) but are only used for FK declarations and ORM relationship metadata — entity construction is manual via `_build_*` methods
- **Risk only**: If any code accesses ORM relationship properties directly on model instances outside the repository pattern (e.g., from a Celery task that has a live ORM session), it would trigger N+1. Currently no such patterns exist.
- **No `selectinload`/`joinedload` used anywhere** — not needed given the Core-style approach

**Caching: NOTHING EXISTS**

- **No application-level caching**: Zero cache layers (Redis is only used for token blacklist + Celery)
- **No query result caching**: Every request hits PostgreSQL
- **No response caching**: No `Cache-Control`, `ETag`, or `Last-Modified` headers
- **No Redis caching**: The existing `Redis` connection is a prime candidate for caching but isn't used for it
- **Config**: `lru_cache` is used on `_get_settings()` and `configure_logger()` (trivial)

**Connection Pooling: ADEQUATE FOR NOW**

```python
pool_size=10,
max_overflow=20,
pool_pre_ping=True,
pool_recycle=3600,
```

- These are reasonable defaults for a small-to-medium app
- `pool_size=10` may be tight under concurrent load depending on Uvicorn workers
- Redis connection is **single client** (module-level `Redis.from_url()`) — no pooling configured

**Pagination: EXISTS BUT INCONSISTENT**

- All listing endpoints use `limit`/`offset` pagination
- No cursor-based pagination (keyset pagination) for large datasets
- No total-count endpoint or `X-Total-Count` header pattern
- Pagination is embedded in each domain's value objects (`AnimalsListQueryParamsValueObject`, etc.)
- No standardized pagination schema shared across domains

**Effort: Medium** across sub-items
- **N+1**: Low effort (already mitigated; just needs audit + tests)
- **Caching**: Medium effort (Redis-backed caching service + decorators)
- **Pool tuning**: Low effort (config changes + Redis pool config)
- **Pagination standardization**: Low effort (shared schema for cursor-pagination)

---

### 5. Current Codebase Health

**Tests**
| Suite | Count | Status |
|-------|-------|--------|
| Unit | 736 | ✅ All passing |
| Integration | 147 passing / 41 failing | ❌ 41 failures |
| Skipped | 12 | — |

The 41 integration failures span cattle, finance, and market domains. Likely fixture/database state issues rather than logic bugs — worth investigating before adding new features.

**Architecture**
- ✅ Clean Hexagonal architecture with domain/application/infrastructure layers
- ✅ Proper dependency injection via FastAPI `Depends`
- ✅ Repository pattern + UoW
- ✅ Tenant isolation via `TenantAwareRepository`
- ✅ Audit logging (partitioned monthly, retention purge exists)
- ✅ GDPR export/delete capabilities
- ✅ Prometheus metrics
- ✅ Structured logging (Loguru, JSON/text formats)
- ✅ Rate limiting (slowapi with Redis backend)
- ✅ Security headers, CORS, correlation IDs, body size limits

**Missing / Issues**
- ❌ Integration test failures need attention
- ❌ No cursor-based pagination for large datasets
- ❌ No caching layer
- ❌ No file/media support
- ❌ No real-time capabilities
- ❌ No domain events / event bus
- ❌ No webhook dispatch system
- ❌ Redis pool not configured (single client)
- ❌ Single module-level `_redis_client` — no reconnect logic

---

### Effort Summary

| Item | Effort | Dependencies | Current State |
|------|--------|-------------|---------------|
| File Upload + CDN | **High** | New deps, new domain, SDD cycle | Nothing |
| WebSocket / Real-time | **Medium** | Uses existing Redis | Nothing |
| Webhook System | **High** | New architectural subsystem | Only MP webhook |
| Performance (N+1) | **Low** | None (already mitigated) | Low risk |
| Performance (Caching) | **Medium** | Uses existing Redis | Nothing |
| Performance (Pool) | **Low** | Config changes | Adequate |
| Pagination | **Low** | Shared schema + cursor impl | Inconsistent |

### Dependencies Between Items

```
File Upload ──► Animal Photos, Receipts, Invoices
     │
     └── Could use Webhooks/Events for "file processed" notifications

WebSocket ──► Event-driven notifications (pairs with Webhook System)
     │
     └── Would consume domain events from Webhook System

Webhook System ──► Foundation for event-driven architecture
     │
     └── Other domains emit events → WebSocket or Webhook dispatch
     │
     └── Outbox table needed for reliability

Performance ──► Cross-cutting, no dependencies on other items
```

### Recommendation

**Do NOT attempt all of Phase 9 in one shot.** Each item is substantial and would benefit from its own SDD cycle. Here's what I recommend:

**Phase 9a (Foundation - Medium effort, highest immediate value):**
1. **Performance sprint** (N+1 audit + caching layer + pool tuning + pagination standard) — cross-cutting, no new domain needed, uses existing Redis
2. **Fix 41 integration test failures** — prerequisite for confidence in further work

**Phase 9b (Capability - High effort, separate SDD cycle):**
3. **Webhook/Domain Event system** — foundational architecture change, enables everything else
4. **File Upload** — only after Webhook system exists (for post-processing events)

**Phase 9c (Real-time - Medium effort, after event system):**
5. **WebSocket/Real-time** — consumes domain events, natural extension after event system is in place

**For the current exploration purposes:** The recommendation is to **start with Performance + Test fixes** (Phase 9a). The Webhook system should be the next architectural investment as it enables both clean file processing pipelines and real-time notifications.

### Ready for Proposal

**Yes** — this analysis is ready for the `propose` phase. The clear recommendation is a phased approach starting with performance optimization and test stability, then building the event infrastructure before adding new capabilities.

### Risks

- 41 integration test failures indicate fragility — must fix before adding new features
- Adding file upload without event system means no post-processing pipeline (thumbnails, virus scan, CDN invalidation)
- WebSocket without domain events means custom notification logic per endpoint (more coupling)
- No caching could become a bottleneck under load with current pool settings
