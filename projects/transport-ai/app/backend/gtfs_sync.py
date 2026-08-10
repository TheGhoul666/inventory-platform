"""GTFS → app data integration (spec ד.3) — connects gtfs_loader's raw
gtfs_* Postgres tables to the app's own Line/Stop tables.

gtfs_loader downloads Israel MOT's national feed and loads it as raw
TEXT columns straight from the government CSVs (see ../gtfs_loader/).
That feed covers every operator in the country, not just this fleet —
so this script scopes to one agency_id (--agency-id) and caps row
counts (--route-limit/--stop-limit); real routes.txt/shapes.txt/
stops.txt run 900KB/228MB/5MB nationwide, unfiltered sync would flood
the app's Line/Stop tables with routes this fleet doesn't operate.

Line.route_geometry comes from shapes.txt via one representative shape
per route (GTFS gives each *trip* its own shape_id; picking the
most-used one per route is enough for a Line's reference geometry —
not exact per-trip routing). Stop.official_name/location come straight
from stops.txt.

Usage:
    python gtfs_sync.py --dsn postgresql://... --agency-id 3 --route-limit 30
    python gtfs_sync.py --demo   # offline self-check, no DB needed
"""
import argparse
from typing import Optional

import psycopg2
from psycopg2.extras import RealDictCursor

from db import Base, SessionLocal, engine
from models import Line, Stop


def fetch_routes(conn, agency_id: Optional[str], limit: int):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        sql = "SELECT route_id, route_short_name, agency_id FROM gtfs_routes"
        params = []
        if agency_id:
            sql += " WHERE agency_id = %s"
            params.append(agency_id)
        sql += " ORDER BY route_id LIMIT %s"
        params.append(limit)
        cur.execute(sql, params)
        return cur.fetchall()


def fetch_representative_shape_id(conn, route_id: str) -> Optional[str]:
    """Most-used shape_id among this route's trips — good enough for one
    reference geometry per Line; not per-trip-accurate routing."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT shape_id, COUNT(*) c FROM gtfs_trips
               WHERE route_id = %s AND shape_id IS NOT NULL AND shape_id != ''
               GROUP BY shape_id ORDER BY c DESC LIMIT 1""",
            (route_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def fetch_shape_points(conn, shape_id: str):
    with conn.cursor() as cur:
        cur.execute(
            """SELECT shape_pt_lat, shape_pt_lon FROM gtfs_shapes
               WHERE shape_id = %s ORDER BY CAST(shape_pt_sequence AS INTEGER)""",
            (shape_id,),
        )
        return [[float(lat), float(lon)] for lat, lon in cur.fetchall()]


def fetch_stops(conn, limit: int):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT stop_id, stop_code, stop_name, stop_lat, stop_lon FROM gtfs_stops LIMIT %s",
            (limit,),
        )
        return cur.fetchall()


def sync_lines(pg_conn, session, agency_id: Optional[str], route_limit: int) -> int:
    count = 0
    for r in fetch_routes(pg_conn, agency_id, route_limit):
        line_number = r["route_short_name"] or r["route_id"]
        shape_id = fetch_representative_shape_id(pg_conn, r["route_id"])
        geometry = fetch_shape_points(pg_conn, shape_id) if shape_id else None

        line = session.query(Line).filter_by(line_number=line_number).first()
        if not line:
            line = Line(line_number=line_number)
            session.add(line)
        line.route_geometry = geometry
        line.schedule_code = r["route_id"]  # traceability back to the GTFS source route
        count += 1
    session.flush()
    return count


def sync_stops(pg_conn, session, stop_limit: int) -> int:
    count = 0
    for s in fetch_stops(pg_conn, stop_limit):
        stop_code = s.get("stop_code") or None
        # stop_code is GTFS's stable id (and the join key station_registry_sync.py uses) —
        # prefer it when present; fall back to name matching for older feeds without one.
        stop = (
            session.query(Stop).filter_by(stop_code=stop_code).first()
            if stop_code
            else session.query(Stop).filter_by(official_name=s["stop_name"]).first()
        )
        if not stop:
            stop = Stop(official_name=s["stop_name"])
            session.add(stop)
        stop.official_name = s["stop_name"]
        stop.stop_code = stop_code
        stop.lat = float(s["stop_lat"]) if s["stop_lat"] else None
        stop.lon = float(s["stop_lon"]) if s["stop_lon"] else None
        count += 1
    session.flush()
    return count


def run(dsn: str, agency_id: Optional[str], route_limit: int, stop_limit: int):
    Base.metadata.create_all(bind=engine)
    pg_conn = psycopg2.connect(dsn)
    session = SessionLocal()
    try:
        n_lines = sync_lines(pg_conn, session, agency_id, route_limit)
        n_stops = sync_stops(pg_conn, session, stop_limit)
        session.commit()
        print(f"synced {n_lines} lines, {n_stops} stops from GTFS")
    finally:
        pg_conn.close()
        session.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dsn", help="postgresql://user:pass@host/db — same DB gtfs_loader wrote to")
    p.add_argument("--agency-id", default=None, help="gtfs_routes.agency_id to scope to (recommended — see docstring)")
    p.add_argument("--route-limit", type=int, default=30)
    p.add_argument("--stop-limit", type=int, default=200)
    p.add_argument("--demo", action="store_true", help="run offline self-check instead")
    args = p.parse_args()

    if args.demo:
        import test_gtfs_sync
        test_gtfs_sync.demo()
    elif not args.dsn:
        p.error("--dsn is required (or pass --demo)")
    else:
        run(args.dsn, args.agency_id, args.route_limit, args.stop_limit)
