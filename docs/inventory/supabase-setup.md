# Supabase Setup Guide

## 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) → New Project
2. Choose region closest to your users
3. Set a strong database password

## 2. Get your credentials

**Dashboard → Settings → API:**

| Variable | Where to find it |
|----------|-----------------|
| `SUPABASE_URL` | Project URL (e.g. `https://abc123.supabase.co`) |
| `SUPABASE_ANON_KEY` | `anon` `public` key |
| `SUPABASE_SERVICE_ROLE_KEY` | `service_role` `secret` key — **never expose to browser** |
| `SUPABASE_JWT_SECRET` | Settings → API → JWT Secret |

**Dashboard → Settings → Database → Connection string (URI):**
- Copy the **Transaction pooler** string (port 6543) — use this as `DATABASE_URL`
- Replace `[YOUR-PASSWORD]` with your DB password

## 3. Configure environment

```bash
cp .env.example .env
# Fill in all Supabase values
```

## 4. Run database migrations

```bash
# Apply schema to your Supabase PostgreSQL
docker compose --profile migrate up migrate
```

Or run Alembic directly:
```bash
cd backend
alembic upgrade head
```

## 5. Enable Supabase Realtime

**Dashboard → Database → Replication:**

Enable publication for these tables:
- `inventory_items` — UPDATE events
- `alerts` — INSERT + UPDATE events

This powers the live dashboard updates without polling.

## 6. Create your first admin user

**Option A — Supabase Dashboard:**
1. Authentication → Users → Invite user
2. Then use the backend admin API to set their role:

```bash
# Get a SuperAdmin token first (use the service_role key)
curl -X PUT http://localhost:8000/api/v1/auth/users/{USER_ID}/role \
  -H "Authorization: Bearer SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"role": "SuperAdmin"}'
```

**Option B — Backend admin API:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/users \
  -H "Authorization: Bearer <superadmin-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "manager@depot.com",
    "password": "SecurePass123!",
    "full_name": "Depot Manager",
    "username": "depotmgr",
    "role": "WarehouseManager"
  }'
```

## 7. Row Level Security

Migrations automatically enable RLS on all tables. The `service_role` key (used by the backend) bypasses RLS, giving the FastAPI app full access.

For direct Supabase client queries from the frontend (future feature), add per-user RLS policies:

```sql
-- Example: users can only read their own warehouse's inventory
CREATE POLICY "warehouse_read"
ON inventory_items
FOR SELECT
TO authenticated
USING (
  warehouse_id IN (
    SELECT warehouse_id FROM user_profiles
    WHERE user_id = auth.uid()
  )
);
```

## 8. Auth settings

**Dashboard → Authentication → Settings:**

- Set `Site URL` to your frontend URL
- Add `http://localhost:3000` to Redirect URLs (for dev)
- Disable "Confirm email" for development (enable in production)
- Configure SMTP for email confirmation in production

## Architecture with Supabase

```
Browser
  │
  ├── supabase.auth.signInWithPassword()  →  Supabase Auth
  │        ↓ JWT access_token
  ├── Axios + Bearer token  →  FastAPI Backend
  │        ↓ verifies JWT locally (SUPABASE_JWT_SECRET)
  │        ↓ SQLAlchemy → Supabase PostgreSQL
  │
  └── supabase.channel()  →  Supabase Realtime
           ↓ PostgreSQL WAL
           → React Query invalidation → UI refresh
```

**What Supabase replaces vs. what we keep:**

| Component | Before | After |
|-----------|--------|-------|
| PostgreSQL | Self-hosted in Docker | Supabase Managed |
| Auth (login/signup) | Custom JWT + bcrypt | Supabase Auth |
| Token refresh | Custom refresh token in DB | Supabase auto-refresh |
| Realtime updates | RabbitMQ + WebSocket | Supabase Realtime (Postgres WAL) |
| **Redis** | — | **Still needed** (rate limiting, caching) |
| **Business logic** | FastAPI | **Still FastAPI** (inventory rules, transactions, analytics) |
| **Row-level locking** | SELECT FOR UPDATE | **Still PostgreSQL** via SQLAlchemy |
