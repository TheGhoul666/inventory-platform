"""data.gov.il station registry → Stop enrichment.

Separate from gtfs_sync.py: that script creates/positions Stop rows from
the static GTFS feed. This one only *enriches* stops that already exist,
adding city_name/metropolitan_name/operator_type_name from the
government's CKAN-hosted station registry (resource_id below) — fields
GTFS stops.txt doesn't carry. Matched on Stop.stop_code == StationId,
which gtfs_sync.py populates from GTFS stop_code; run gtfs_sync.py first.

Dataset: https://data.gov.il/dataset/bus-stops (34k+ rows, live API, no
bulk download) — paginated via limit/offset, default page size 1000.

Usage:
    python station_registry_sync.py --dsn postgresql://...  # DSN is for the app DB (db.py), not GTFS
    python station_registry_sync.py --demo   # offline self-check, no network needed
"""
import argparse
from typing import Callable, Iterator

import requests

from db import Base, SessionLocal, engine
from models import Stop

RESOURCE_ID = "e873e6a2-66c1-494f-a677-f5e77348edb0"
API_URL = "https://data.gov.il/api/3/action/datastore_search"


def fetch_page(resource_id: str, offset: int, limit: int) -> list:
    r = requests.get(
        API_URL, params={"resource_id": resource_id, "offset": offset, "limit": limit}, timeout=30
    )
    r.raise_for_status()
    return r.json()["result"]["records"]


def fetch_all_records(
    resource_id: str = RESOURCE_ID, page_size: int = 1000, page_fetcher: Callable = fetch_page
) -> Iterator[dict]:
    offset = 0
    while True:
        page = page_fetcher(resource_id, offset, page_size)
        if not page:
            return
        yield from page
        offset += len(page)


def sync_registry(session, records: Iterator[dict]) -> int:
    """Enrich existing Stop rows only — a station in the registry with no
    matching GTFS stop_code isn't one of this fleet's stops."""
    count = 0
    for rec in records:
        stop_code = str(rec.get("StationId") or "").strip()
        if not stop_code:
            continue
        stop = session.query(Stop).filter_by(stop_code=stop_code).first()
        if not stop:
            continue
        stop.city_name = rec.get("CityName")
        stop.metropolitan_name = rec.get("MetropolinName")
        stop.operator_type_name = rec.get("StationOperatorTypeName")
        count += 1
    session.flush()
    return count


def run(dsn: str = None):
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        n = sync_registry(session, fetch_all_records())
        session.commit()
        print(f"enriched {n} stops from station registry")
    finally:
        session.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--demo", action="store_true", help="run offline self-check instead")
    args = p.parse_args()  # app DB comes from $DATABASE_URL (see db.py) — no --dsn flag needed here

    if args.demo:
        import test_station_registry_sync

        test_station_registry_sync.demo()
    else:
        run()
