# BusOps — Bus Fleet Inventory Management Platform

Full-stack inventory management system for bus fleets: web dashboard, FastAPI backend, Android and iOS apps — all synced via Supabase Realtime.

## Stack

| Layer | Tech |
|-------|------|
| Web | React 18 + Vite + Tailwind |
| Backend | FastAPI + Supabase PostgREST |
| Database | Supabase (PostgreSQL 17) |
| Android | Kotlin + Jetpack Compose + Hilt |
| iOS | Swift + SwiftUI |
| Realtime | Supabase Realtime (all 3 platforms) |

## Structure

```
busops-monorepo/
├── web/              React frontend
├── backend/          FastAPI service
├── mobile-android/   Kotlin app
├── mobile-ios/       Swift app
├── database/         SQL schema
├── scripts/          Seed and migration utilities
├── infrastructure/   nginx + prometheus
└── docker-compose.yml
```

## Quick Start

```bash
# Web
cd web && npm install && npm run dev

# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

# Seed database
python scripts/seed.py
```

## Environment

Copy `.env.example` to `.env` and fill in values from Supabase Dashboard → Settings → API.

Supabase project: `wrspszdkmjdrhupvjblu`

## Architecture

- **Reads**: all 3 platforms query Supabase PostgREST directly (bypasses FastAPI — avoids IPv6 DNS issue)
- **Writes**: issue/restock/transfer go through FastAPI for business-rule enforcement
- **Realtime**: Supabase channels broadcast inventory + alert changes to all connected clients instantly
