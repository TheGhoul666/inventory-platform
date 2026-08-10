# תחבורה AI (Transport AI)

Source spec: `תחבורה_AI_v3_14_1.docx` (v3.14, July 2026) in
`פרוייקט סטארטאפ/`. Full doc is ~50 pages — a multi-phase (15+ months,
₪1.3–2M) platform spanning Kafka, GKE, Kong, Spring Boot, FastAPI,
PostgreSQL/PostGIS/TimescaleDB, a Python AI/optimization engine, WhatsApp +
IVR driver comms, and native Android/iOS apps. Not something to scaffold in
full up front — this repo grows one working phase-0/MVP slice at a time.

## Key decision already made

**Section ב.5 — Fleet-management software layer: Option A** (existing
Native product pre-integrated with ISR/Teltonika, e.g. YIT-pattern), not
building that layer in-house. Transport AI talks to it through an Adapter
Service (יג.1) — swappable later without touching core logic. Whichever
vendor gets picked still needs the write-API check from ב.5 (read-only
vendors are disqualified outright, per the spec's own hard rule).

## Quickest way to try it (no Docker)

```
.\run_local.ps1   # installs deps, seeds demo data, opens the dashboard
.\stop_local.ps1  # stops both servers it started
```

Uses SQLite instead of Postgres — fine for the UI/workflow demo, but
`gtfs_loader` only speaks Postgres (the spec names it explicitly in ד.3),
so real GTFS ingestion still needs the Docker path below or a real
`$env:DATABASE_URL` pointing at Postgres.

## What's built so far

### `gtfs_loader/` — spec ד.3 / FR-56
Downloads Israel MOT's national GTFS feed (gtfs.mot.gov.il, ~150MB —
routes/stops/trips/shapes/calendar for *every* operator in the country)
and loads it as raw tables into PostgreSQL, one per GTFS file
(`gtfs_routes`, `gtfs_stops`, ...).

```
cd gtfs_loader
pip install -r requirements.txt
python load_gtfs.py --dsn postgresql://user:pass@host/db
python load_gtfs.py --demo   # offline self-check, no network/DB needed
```

### `app/backend/gtfs_sync.py` — connects the two
Reads those raw `gtfs_*` tables and upserts the app's own `Line`/`Stop`
rows: `route_geometry` from `shapes.txt` (via each route's most-used
`shape_id` in `trips.txt` — one reference geometry per Line, not exact
per-trip routing) and `Stop.official_name`/location straight from
`stops.txt`. Scoped with `--agency-id` and row limits — the national
feed is nationwide, not just this fleet's routes; syncing unfiltered
would flood the app with routes it doesn't operate. Safe to run before
or after `seed.py` in either order — `seed.py` reuses whatever Lines
already exist instead of assuming it owns that table.

```
cd app/backend
python gtfs_sync.py --dsn postgresql://user:pass@host/db --agency-id 3 --route-limit 30
python gtfs_sync.py --demo   # offline self-check against canned rows shaped like the real feed
```

Query logic (route→shape→geometry join, upsert-not-duplicate) was
verified against an actual downloaded copy of the government feed
(2026-08-09) — confirmed real routes resolve to real, correctly-ordered
shape points — via a throwaway SQLite mirror, since this sandbox has no
local Postgres to run the real script end-to-end against. `--demo`
exercises the same code path with fixtures shaped identically to what
that verification confirmed.

### `app/backend/station_registry_sync.py` — station registry enrichment
Adds `city_name`/`metropolitan_name`/`operator_type_name` to existing
`Stop` rows from data.gov.il's live station-registry API (34k+ stations
nationwide, resource `e873e6a2-66c1-494f-a677-f5e77348edb0`) — metadata
GTFS `stops.txt` doesn't carry. Matches on `Stop.stop_code`, which
`gtfs_sync.py` now also populates (from GTFS `stop_code`), so run
`gtfs_sync.py` first. Only enriches stops that already exist — a
registry row with no matching `stop_code` isn't one of this fleet's
stops, so it's skipped rather than inserted.

```
cd app/backend
python station_registry_sync.py   # uses $DATABASE_URL, same as db.py
python station_registry_sync.py --demo   # offline self-check, no network needed
```

### `app/` — Phase-1 MVP dispatcher app
A single FastAPI service + Postgres + a no-build-step HTML/Leaflet
dashboard, implementing the full 9-entity data model from נספח ו' and the
core Phase-1 workflows: live vehicle map, AI-proposed reassignment with
deterministic Blast Radius (ו.6), manual driver search/assign, trip
closure with mandatory reason (ו.7), and route-blocking-incident /
diversion records (ו.5, propose+approve only — no live geometry
intersection).

```
cd app
docker compose up --build
docker compose exec backend python seed.py   # demo drivers/vehicles/lines/trips
# API:       http://localhost:8000/docs
# Dashboard: http://localhost:5173
```

Backend logic (GPS fusion, reassignment candidate search, closure
validation) has an offline self-check with no Docker/Postgres needed:

```
cd app/backend
pip install -r requirements.txt
python test_backend.py
```

### What's real vs. simulated in `app/`
This runs as **one FastAPI monolith**, not the spec's six-layer
microservices/Kafka/GKE/Kong architecture — that split is real
engineering effort with no payoff at demo scale; revisit if/when actual
load or team size demands it.

| Spec concept | Status here |
|---|---|
| 3-source GPS Fusion (ג.1), bad-point filtering (ג.2) | **Real logic**, simulated data sources (no ISR/Itouran/phone hardware) |
| Reassignment candidates + Blast Radius (ו.6) | **Real logic** — deterministic conflict + impact check |
| Driver search / manual assign / trip closure (ו.7) | **Real**, full workflow |
| Route-blocking incident → diversion (ו.5) | Records + approval flow only; no live route-geometry intersection or Google Directions call |
| GTFS → Line/Stop data integration (ד.3) | **Real** — `gtfs_sync.py`, verified against real government data |
| WhatsApp driver channel (ט.1), IVR fallback (ט.2) | **Simulated** — logged to `driver_messages`; WhatsApp-first/IVR-fallback routing is real logic, no Meta Business API or real telephony |
| Adapter Service (יג.1 / ב.5.1) | **Real pattern**, mock vendors — swapping `adapter.py`'s implementation is genuinely a one-line change, but neither implementation calls a real vendor API (none contracted yet) |
| Native driver app (ב.4) | `driver.html` — mobile-shaped web view standing in for a real Kotlin/Swift build |
| Online-learning prediction models, Yesterday+Delta optimizer (י, יא) | Not built — reassignment here is a rules-based candidate ranker, not ML |
| Shortage/emergency mode (ו.3) | Not built — dropped from the dashboard rather than shipped as a UI toggle with no logic behind it |
| Kafka, GKE, Kong, Spring Boot ERP layer, native mobile builds | Not built — out of scope for a local MVP demo |

## Not built yet (deliberately)

Real WhatsApp Business API / IVR telephony integration, a real native
mobile build, the real Adapter Service against an actual vendor
(depends on picking one — see ב.5's write-API requirement), infra
(Kafka/GKE/Kong), ISO 27001/DPIA, multi-tenant Fleet Profiler
auto-calibration, the ML optimization engine, shortage/emergency mode.
These depend on decisions the spec explicitly defers to Phase 0 (vendor
selection, Sandbox access) or on real infra this environment doesn't
have — see נספח ז' for the full list of open items. Pick the next slice
against טז.1's phase plan rather than building speculatively.
