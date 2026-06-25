---
title: BusOps Monorepo — Architecture
date: 2026-06-25
status: current
---

# System Architecture

## Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         SINGLE SOURCE OF TRUTH                           │
│                     Supabase PostgreSQL + Realtime                        │
└───────────┬──────────────────────┬───────────────────────────────────────┘
            │                      │ Realtime WebSocket (sub-second)
            │         ┌────────────▼──────────────────────────┐
            │         │         All clients subscribe          │
            │         │  Web · Android · iOS · Future Desktop  │
            │         └────────────────────────────────────────┘
            │
  ┌─────────▼──────────┐
  │   FastAPI Backend   │  ← Single source of business rules + permissions
  │   /api/v1/*         │
  └──────┬─────────────┘
         │
   ┌─────┴──────┐
   │   Redis    │  Cache + rate limiting
   │  RabbitMQ  │  Event queue + alert workers
   └────────────┘
```

## Real-Time Sync Flow

```
[Android: Technician issues 5 brake pads]
       │
       ▼
POST /api/v1/inventory/transactions/issue
       │
       ▼
FastAPI validates (row-lock, stock check, RBAC)
       │
       ▼
PostgreSQL UPDATE inventory_items SET quantity = quantity - 5
       │
       ▼
Supabase Realtime broadcasts UPDATE event to all subscribers
       │
   ┌───┴──────────────────────────┐
   ▼                              ▼
iOS supervisor receives event   Web dashboard receives event
items list updates instantly    quantity badge updates instantly
```

## Monorepo Layout

```
busops-monorepo/
├── web/                # React + Vite + Supabase JS (existing platform)
├── mobile-android/     # Kotlin + Jetpack Compose + Hilt + Supabase Kotlin
├── mobile-ios/         # Swift + SwiftUI + Supabase Swift
├── backend/            # FastAPI + SQLAlchemy + Alembic (existing platform)
├── shared/             # OpenAPI spec + codegen configs
├── database/           # Schema SQL + seed scripts
├── infrastructure/     # Docker Compose + GitHub Actions + future Terraform/K8s
├── docs/               # Architecture decisions + API design
└── scripts/            # Utility scripts
```

## Authentication Flow (all platforms)

1. User enters email + password
2. Client calls Supabase Auth directly (`auth.signIn`)
3. Supabase returns JWT access token (15min) + refresh token (7 days)
4. Client attaches `Authorization: Bearer <token>` to all backend API calls
5. FastAPI verifies JWT signature against Supabase JWKS endpoint
6. Token refresh handled by each platform's Supabase SDK automatically

## RBAC

Roles are stored in Supabase `app_metadata` (enforced at JWT level) and in
the PostgreSQL `roles` table (enforced at backend level). Both must agree —
Supabase is the identity provider, PostgreSQL is the permission store.

| Role | Android | iOS | Web |
|------|---------|-----|-----|
| SuperAdmin | Full | Full | Full |
| WarehouseManager | Issue/Restock/Transfer + Alerts | Same | Same |
| Technician | Issue/Restock | Same | Same |
| Viewer | Read-only | Read-only | Read-only |

## Future Expansion

| Platform | Path |
|----------|------|
| Windows Desktop | Electron wrapping the web app, or WinUI 3 native |
| macOS Desktop | SwiftUI app reusing iOS code (Catalyst/native) |
| Linux Desktop | Electron or Flutter Linux |
| Multi-tenant SaaS | Add `tenant_id` column to all tables + Row Level Security |
| AI integrations | Add `/api/v1/ai/predict-depletion` using the existing analytics data |
