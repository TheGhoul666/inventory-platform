# Bus Maintenance Inventory & Operational Intelligence Platform

Enterprise-grade inventory management system for public transportation companies. Designed to prevent maintenance-related bus downtime through real-time stock visibility, predictive depletion alerts, and complete operational auditability.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         NGINX (Reverse Proxy)                    │
│                    Rate limiting · SSL · Routing                  │
└───────────────┬───────────────────────┬─────────────────────────┘
                │                       │
     ┌──────────▼──────┐     ┌─────────▼──────────┐
     │   React Frontend │     │  FastAPI Backend    │
     │  Vite · Tailwind │     │  Async · Python 3.12│
     │  Zustand · RQ    │     │  SQLAlchemy 2.x     │
     └─────────────────┘     └──────┬──────────────┘
                                    │
               ┌────────────────────┼───────────────────┐
               │                    │                   │
    ┌──────────▼───┐   ┌───────────▼────┐   ┌──────────▼──────┐
    │  PostgreSQL   │   │     Redis      │   │   RabbitMQ      │
    │  Primary DB   │   │  Cache/Limits  │   │  Event Queue    │
    │  Row-locking  │   │  Session Store │   │  Workers · DLQ  │
    └──────────────┘   └────────────────┘   └────────┬────────┘
                                                      │
                                          ┌───────────▼──────────┐
                                          │    Background Workers │
                                          │  Alert · Webhook      │
                                          └──────────────────────┘

Observability Stack: Prometheus + Grafana + ELK (Elasticsearch, Kibana)
```

### Layered Architecture

| Layer | Responsibility | Location |
|-------|----------------|----------|
| **Presentation** | React SPA, dark UI, real-time updates | `frontend/src/` |
| **API** | FastAPI routes, auth, rate limiting, validation | `backend/app/api/` |
| **Application** | Orchestrates use cases, services, DTOs | `backend/app/application/` |
| **Domain** | Business rules, entities, domain events | `backend/app/domain/` |
| **Repository** | Data access, locking, queries | `backend/app/repositories/` |
| **Infrastructure** | DB, Redis, RabbitMQ, webhooks, logging | `backend/app/infrastructure/` |

---

## Concurrency Design

This is the most critical engineering concern in any inventory system.

### Problem
Multiple technicians issuing parts simultaneously from the same warehouse can produce:
- Lost updates (two reads see 10 units, both subtract 5, result is 5 instead of 0)
- Negative inventory (issuing 8 + 7 from 10 units)
- Phantom reads, dirty reads under weak isolation

### Solution: Three-layer protection

**Layer 1 — Database row-level lock** (`SELECT FOR UPDATE NOWAIT`)
```python
# InventoryRepository.get_item_with_lock()
result = await session.execute(
    select(InventoryItem)
    .where(InventoryItem.id == item_id)
    .with_for_update(nowait=True)   # Fail immediately if locked
)
```
- Serializes all writes to a single item's row
- `NOWAIT`: returns 409 Conflict immediately instead of waiting (prevents request pile-up)
- Client retries with exponential backoff

**Layer 2 — Domain rule** (`assert_sufficient_stock`)
- Pure function, no DB access
- Validates available quantity before mutation

**Layer 3 — DB CHECK constraint**
```sql
CHECK (quantity >= 0)
```
- Last resort: catches any bug that slips through layers 1 and 2

**Transfer deadlock prevention**
- Always acquires locks in UUID sort order: `min(src_id, dst_id)` first
- Prevents A→B / B→A deadlock

---

## Quick Start

### Prerequisites
- Docker Desktop 4.x+
- Docker Compose v2.x+

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env — set all CHANGE_ME values
```

### 2. Run database migrations

```bash
docker compose --profile migrate up migrate
```

### 3. Start development stack

```bash
docker compose --profile dev up
```

Services:
| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1 |
| API Docs | http://localhost:8000/api/docs |
| RabbitMQ Management | http://localhost:15672 |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |
| Kibana | http://localhost:5601 |

### 4. Create first admin user

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@depot.com","username":"admin","password":"SecurePass123!","full_name":"System Admin"}'
```

Then in the database, promote to SuperAdmin:
```sql
UPDATE users SET is_superadmin = true WHERE email = 'admin@depot.com';
```

---

## Running Tests

```bash
# Unit tests (no external dependencies)
cd backend
pytest tests/unit/ -v

# Integration tests (requires running postgres + redis)
pytest tests/integration/ -v

# Concurrency tests (requires real PostgreSQL)
INTEGRATION_DB_URL=postgresql+asyncpg://inv_user:password@localhost:5432/bus_inventory \
  pytest tests/concurrency/ -v

# Full suite with coverage
pytest tests/ --cov=app --cov-report=html
```

---

## API Reference

### Authentication
```
POST /api/v1/auth/login      — Login → access_token + refresh_token
POST /api/v1/auth/register   — Register new user
POST /api/v1/auth/refresh    — Rotate refresh token
```

### Inventory
```
GET  /api/v1/inventory/items              — List items (paginated, filterable)
POST /api/v1/inventory/items              — Create item
GET  /api/v1/inventory/items/{id}         — Get item detail
POST /api/v1/inventory/transactions/issue    — Issue items to maintenance job
POST /api/v1/inventory/transactions/restock  — Restock from supplier
POST /api/v1/inventory/transactions/transfer — Transfer between warehouses
GET  /api/v1/inventory/transactions          — Transaction history
POST /api/v1/inventory/transactions/{id}/rollback — Rollback transaction
```

### Analytics
```
GET /api/v1/analytics/dashboard       — Operational dashboard summary
GET /api/v1/analytics/usage/{item_id} — Consumption rate + depletion prediction
GET /api/v1/analytics/depletion/{id}  — EMA trend + days to depletion
GET /api/v1/analytics/anomalies/{id}  — Usage spike detection
```

### Alerts
```
GET  /api/v1/alerts                        — List alerts (filterable)
POST /api/v1/alerts/{id}/acknowledge       — Acknowledge alert
POST /api/v1/alerts/{id}/resolve           — Mark resolved
```

---

## RBAC Roles

| Role | Capabilities |
|------|-------------|
| **SuperAdmin** | Full access to all resources |
| **WarehouseManager** | Full inventory + warehouse management, alert management |
| **Technician** | Issue/restock inventory, read analytics |
| **Viewer** | Read-only access to inventory, warehouses, alerts |

---

## Predictive Analytics

### Consumption Rate
```
rate = total_issued_last_30_days / 30   (units per day)
```

### Days to Depletion
```
days_left = current_quantity / daily_rate
```

### Exponential Moving Average (EMA)
```
EMA_t = α × actual_t + (1 - α) × EMA_(t-1)
α = 0.3  (configurable)
```
Smooths short-term spikes for more stable trend lines.

### Anomaly Detection
```
is_spike = (rate_7d / rate_30d) > 2.0
```
Triggers `ABNORMAL_USAGE` alert and webhook event.

---

## Webhook Events

All webhook payloads are HMAC-SHA256 signed:
```
X-Webhook-Signature: sha256=<hex_digest>
X-Webhook-Event: CRITICAL_LOW_STOCK
X-Idempotency-Key: <uuid>
```

Example payload:
```json
{
  "event": "CRITICAL_LOW_STOCK",
  "event_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "item_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "warehouse_id": "8d86573b-a8b7-4a6a-a6f4-1c2e3d4f5a6b",
  "current_quantity": 3,
  "threshold": 10,
  "predicted_days_left": 0.8,
  "timestamp": "2026-05-17T12:00:00Z"
}
```

Retry schedule: 1s → 5s → 30s → 2min → 10min. Failed deliveries go to dead-letter queue.

---

## Production Deployment

```bash
# Production stack
docker compose --profile prod up -d

# Scale backend workers
docker compose up -d --scale backend-prod=4

# Run migrations
docker compose --profile migrate run --rm migrate

# View logs
docker compose logs -f backend-prod alert-worker
```

### Environment Variables (production must-set)
- `APP_SECRET_KEY` — 32+ char random string
- `JWT_SECRET_KEY` — 64+ char random string  
- `POSTGRES_PASSWORD` — strong unique password
- `REDIS_PASSWORD` — strong unique password
- `RABBITMQ_PASSWORD` — strong unique password
- `WEBHOOK_SIGNING_SECRET` — 32+ char random string
- `GRAFANA_ADMIN_PASSWORD` — strong password

---

## Scaling Guide

| Bottleneck | Solution |
|------------|----------|
| DB reads | Add read replicas, point analytics queries at replica |
| API throughput | Scale `backend-prod` horizontally (stateless workers) |
| Alert processing | Scale `alert-worker` replicas (RabbitMQ distributes messages) |
| Cache pressure | Redis Cluster for >10K items |
| Long-term | Extract Inventory, Analytics, Webhook into microservices (domain boundaries are pre-drawn) |

---

## Monitoring

- **Prometheus** at `:9090` — scrapes backend, PostgreSQL, Redis, RabbitMQ
- **Grafana** at `:3001` — pre-built dashboards (import from `infrastructure/monitoring/grafana/dashboards/`)
- **Kibana** at `:5601` — structured JSON log search and alerting
- **Health check** at `GET /health` — load balancer probe
- **Readiness check** at `GET /ready` — checks DB + Redis

---

## Project Structure

```
inventory_platform/
├── backend/
│   ├── app/
│   │   ├── api/           — FastAPI routes, middleware, dependencies
│   │   ├── application/   — Services, use cases, DTOs
│   │   ├── domain/        — Models, entities, business rules, events
│   │   ├── repositories/  — Data access with row-level locking
│   │   ├── infrastructure/— DB, Redis, RabbitMQ, webhooks, logging
│   │   ├── auth/          — JWT, bcrypt, RBAC
│   │   ├── workers/       — Alert + webhook background workers
│   │   └── main.py        — FastAPI app factory
│   ├── alembic/           — Database migrations
│   └── tests/             — Unit, integration, concurrency, load
├── frontend/
│   └── src/
│       ├── pages/         — Dashboard, Inventory, Alerts, Analytics
│       ├── components/    — Shared UI components
│       ├── services/      — API client layer
│       ├── store/         — Zustand auth + UI state
│       └── types/         — TypeScript domain types
├── infrastructure/
│   ├── nginx/             — Reverse proxy config
│   ├── monitoring/        — Prometheus + Grafana configs
│   └── scripts/           — DB init scripts
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## License

Proprietary — All rights reserved.
