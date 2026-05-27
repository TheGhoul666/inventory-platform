# Inventory Platform — Bus Maintenance System

> פלטפורמת ניהול מלאי לחברות תחבורה ציבורית. מונעת השבתה הנדסית על ידי ניהול מלאי בזמן אמת, התראות חזויות ועקיבות מלאה.

## מה זה?

Full-stack enterprise app:
- **Backend**: FastAPI (Python), SQLAlchemy, PostgreSQL, Redis, RabbitMQ
- **Frontend**: React + TypeScript + Vite + Tailwind (dark UI)
- **Auth**: Supabase Auth + JWT
- **Realtime**: Supabase Realtime (Postgres WAL)
- **Monitoring**: Prometheus + Grafana + Kibana

## מיקום הקוד

`C:\Users\beni3\OneDrive\שולחן העבודה\Python\inventory_platform\`

## ארכיטקטורה

```
NGINX → React Frontend  ←→  FastAPI Backend
                              ├── PostgreSQL (row-level locking)
                              ├── Redis (cache, rate limiting)
                              └── RabbitMQ (async events / workers)
```

## מה כבר בוצע

### Backend (מלא)
- [x] FastAPI app factory עם Lifespan (Redis + RabbitMQ + Webhooks)
- [x] Domain models: InventoryItem, Transaction, Alert, Warehouse, Bus, Audit
- [x] Repositories עם `SELECT FOR UPDATE NOWAIT` למניעת race conditions
- [x] Services: InventoryService, AnalyticsService (EMA, depletion prediction)
- [x] Auth: JWT + Supabase + RBAC (SuperAdmin / WarehouseManager / Technician / Viewer)
- [x] Background workers: AlertWorker, WebhookEngine
- [x] Alembic migrations
- [x] Tests: unit, integration, concurrency

### Frontend (עבד על זה)
- [x] Dashboard — real-time overview, stat cards, critical items, open alerts
- [x] AlertsPage — filter by status, acknowledge/resolve
- [x] InventoryPage — search, filter, table עם pagination

## שיפורים שבוצעו ב-2026-05-19

### InventoryPage — הוספת modals ו-drawer חסרים:

| פיצ'ר | לפני | אחרי |
|-------|------|-------|
| כפתור Restock | לא עשה כלום | RestockModal — qty + PO reference + notes |
| כפתור Add Item | לא עשה כלום | AddItemModal — form מלא עם כל שדות ה-InventoryItem |
| לחיצה על שורה | selectedItem הוגדר אבל לא הוצג | ItemDetailDrawer — slide-over עם פרטים + היסטוריית עסקאות |
| Transfer | כפתור עם icon | מוביל ל-ItemDetailDrawer (Transfer מורכב — צריך item destination) |

### AnalyticsPage — שיפור UX:

| לפני | אחרי |
|------|-------|
| הדבקת UUID ידנית | Searchable dropdown — מחפש לפי SKU/שם, בוחר מרשימה |

## API Endpoints

```
POST /api/v1/inventory/transactions/issue     — הוצאת פריטים
POST /api/v1/inventory/transactions/restock   — מילוי מחדש
POST /api/v1/inventory/transactions/transfer  — העברה בין מחסנים
GET  /api/v1/analytics/usage/{id}            — קצב צריכה
GET  /api/v1/analytics/depletion/{id}        — תחזית ריקון + EMA
GET  /api/v1/analytics/anomalies/{id}        — זיהוי חריגות
```

## הפעלה

```bash
# Docker (כל השירותים)
docker compose --profile dev up

# Frontend בלבד
cd inventory_platform/frontend
npm run dev   # http://localhost:3000

# Backend בלבד
cd inventory_platform/backend
uvicorn app.main:app --reload   # http://localhost:8000
```

## מה נשאר

- [ ] TransferModal — בחירת מחסן יעד + item matching
- [ ] Warehouses management page
- [ ] User management (admin UI)
- [ ] Dashboard — "Items Monitored" count (currently shows "—")
- [ ] Analytics — transaction history chart per item
