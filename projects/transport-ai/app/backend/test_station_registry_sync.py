"""Offline self-check for station_registry_sync.py — no network, no real
Postgres. Record shape verified against a live call to the resource_id's
datastore_search API on 2026-08-10.

Run: python station_registry_sync.py --demo
"""
import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Private SQLite engine, independent of db.py's Postgres-bound `engine` — see
# test_gtfs_sync.py for why.
_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
engine = create_engine(f"sqlite:///{_db_file.name}")
SessionLocal = sessionmaker(bind=engine)

from models import Base, Stop  # noqa: E402
from station_registry_sync import sync_registry  # noqa: E402

RECORDS = [
    {
        "StationId": 2228,
        "CityName": "אבו גוש",
        "MetropolinName": "ירושלים",
        "StationOperatorTypeName": "מפעילי אוטובוסים",
    },
    {
        "StationId": 404,
        "CityName": "ירושלים",
        "MetropolinName": "ירושלים",
        "StationOperatorTypeName": "מפעילי אוטובוסים",
    },
    # a registry row with no matching stop_code in our fleet — must be skipped, not inserted
    {"StationId": 999999, "CityName": "אילת", "MetropolinName": None, "StationOperatorTypeName": "רכבת"},
]


def _fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.add(Stop(official_name="Abu Ghosh Junction", stop_code="2228"))
    db.commit()
    return db


def test_sync_registry_enriches_matching_stop():
    db = _fresh_db()
    n = sync_registry(db, iter(RECORDS))
    db.commit()
    assert n == 1  # only StationId 2228 matches an existing stop_code
    stop = db.query(Stop).filter_by(stop_code="2228").first()
    assert stop.city_name == "אבו גוש"
    assert stop.metropolitan_name == "ירושלים"
    assert stop.operator_type_name == "מפעילי אוטובוסים"
    db.close()


def test_sync_registry_skips_unmatched_station_id():
    db = _fresh_db()
    sync_registry(db, iter(RECORDS))
    db.commit()
    assert db.query(Stop).count() == 1  # the 999999 record created nothing
    db.close()


def demo():
    test_sync_registry_enriches_matching_stop()
    test_sync_registry_skips_unmatched_station_id()
    print("station_registry_sync self-check: OK")


if __name__ == "__main__":
    demo()
