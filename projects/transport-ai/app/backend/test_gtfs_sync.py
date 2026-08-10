"""Offline self-check for gtfs_sync.py — no network, no real Postgres.
Canned rows are shaped exactly like the real feed's columns, verified
against an actual download of gtfs.mot.gov.il on 2026-08-09.

Run: python gtfs_sync.py --demo
"""
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# A private SQLite engine, independent of db.py's module-level `engine` (which is
# bound to the real Postgres DSN at import time) — avoids needing a live Postgres
# just to import gtfs_sync.py for this self-check.
_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
engine = create_engine(f"sqlite:///{_db_file.name}")
SessionLocal = sessionmaker(bind=engine)

from gtfs_sync import sync_lines, sync_stops  # noqa: E402
from models import Base, Line, Stop  # noqa: E402

ROUTES = [
    {"route_id": "1001", "route_short_name": "480", "agency_id": "3"},
    {"route_id": "1002", "route_short_name": "12", "agency_id": "3"},
]
# route_id -> [(shape_id, count), ...] pre-aggregated & sorted, most-used shape first
TRIPS_BY_ROUTE = {
    "1001": [("shape-a", 5), ("shape-b", 1)],
    "1002": [],  # a route with no trips on file yet — must not crash
}
SHAPES = {
    "shape-a": [("32.0800", "34.7800"), ("32.0850", "34.7850"), ("32.0900", "34.7900")],
}
STOPS = [
    {"stop_id": "1", "stop_code": "12345", "stop_name": "Central Bus Station", "stop_lat": "32.0809", "stop_lon": "34.7806"},
    {"stop_id": "2", "stop_code": "", "stop_name": "Rothschild Blvd", "stop_lat": "32.0648", "stop_lon": "34.7737"},
]


class FakeCursor:
    def __init__(self):
        self._rows = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=()):
        if "FROM gtfs_routes" in sql:
            self._rows = list(ROUTES)
        elif "FROM gtfs_trips" in sql:
            self._rows = TRIPS_BY_ROUTE.get(params[0], [])
        elif "FROM gtfs_shapes" in sql:
            self._rows = list(SHAPES.get(params[0], []))
        elif "FROM gtfs_stops" in sql:
            self._rows = list(STOPS)
        else:
            raise AssertionError(f"unexpected query: {sql}")

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class FakeConn:
    def cursor(self, cursor_factory=None):
        return FakeCursor()


def _fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_sync_lines_builds_geometry_from_most_used_shape():
    db = _fresh_db()
    n = sync_lines(FakeConn(), db, agency_id="3", route_limit=30)
    db.commit()
    assert n == 2
    line = db.query(Line).filter_by(line_number="480").first()
    assert line is not None
    assert line.route_geometry == [[32.08, 34.78], [32.085, 34.785], [32.09, 34.79]]
    assert line.schedule_code == "1001"
    db.close()


def test_sync_lines_handles_route_with_no_shape():
    db = _fresh_db()
    sync_lines(FakeConn(), db, agency_id="3", route_limit=30)
    db.commit()
    line = db.query(Line).filter_by(line_number="12").first()
    assert line is not None and line.route_geometry is None
    db.close()


def test_sync_lines_upserts_not_duplicates():
    db = _fresh_db()
    sync_lines(FakeConn(), db, agency_id="3", route_limit=30)
    db.commit()
    sync_lines(FakeConn(), db, agency_id="3", route_limit=30)  # run twice
    db.commit()
    assert db.query(Line).filter_by(line_number="480").count() == 1
    db.close()


def test_sync_stops_populates_location_and_name():
    db = _fresh_db()
    n = sync_stops(FakeConn(), db, stop_limit=200)
    db.commit()
    assert n == 2
    stop = db.query(Stop).filter_by(official_name="Central Bus Station").first()
    assert stop is not None and stop.lat == 32.0809 and stop.lon == 34.7806
    assert stop.stop_code == "12345"  # join key for station_registry_sync.py
    db.close()


def test_sync_stops_upserts_by_stop_code_not_duplicates():
    db = _fresh_db()
    sync_stops(FakeConn(), db, stop_limit=200)
    db.commit()
    sync_stops(FakeConn(), db, stop_limit=200)  # run twice
    db.commit()
    assert db.query(Stop).filter_by(stop_code="12345").count() == 1
    db.close()


def demo():
    test_sync_lines_builds_geometry_from_most_used_shape()
    test_sync_lines_handles_route_with_no_shape()
    test_sync_lines_upserts_not_duplicates()
    test_sync_stops_populates_location_and_name()
    test_sync_stops_upserts_by_stop_code_not_duplicates()
    print("gtfs_sync self-check: OK")


if __name__ == "__main__":
    demo()
