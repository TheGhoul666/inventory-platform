"""Offline self-check for load_gtfs.py — no network, no real Postgres.

Run: python load_gtfs.py --demo
"""
import csv
import tempfile
import zipfile
from pathlib import Path

from load_gtfs import FILES, extract_gtfs, setup_database, load_data_to_postgres

SAMPLE = {
    "stops": [
        ["stop_id", "stop_name", "stop_lat", "stop_lon"],
        ["1", "Central Station", "32.08", "34.78"],
    ],
    "routes": [
        ["route_id", "route_short_name", "route_type"],
        ["100", "Line 100", "3"],
    ],
    # calendar/agency/trips/stop_times/shapes deliberately omitted —
    # exercises the "file missing from feed" skip path.
}


class FakeCursor:
    """Records executed SQL / copy_expert calls instead of hitting a real DB."""

    def __init__(self, log):
        self.log = log

    def execute(self, sql, *a):
        self.log.append(("execute", sql))

    def copy_expert(self, sql, fileobj):
        self.log.append(("copy_expert", sql, fileobj.read()))

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class FakeConn:
    def __init__(self):
        self.log = []

    def cursor(self):
        return FakeCursor(self.log)

    def commit(self):
        pass


def _write_sample_zip(zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w") as z:
        for name, rows in SAMPLE.items():
            buf = "\n".join(",".join(row) for row in rows) + "\n"
            z.writestr(f"{name}.txt", buf)


def demo() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        zip_path = tmp / "gtfs.zip"
        _write_sample_zip(zip_path)

        gtfs_dir = extract_gtfs(zip_path, tmp / "extracted")
        assert (gtfs_dir / "stops.txt").exists()

        conn = FakeConn()
        setup_database(conn, gtfs_dir)
        load_data_to_postgres(conn, gtfs_dir)

        executes = [e[1] for e in conn.log if e[0] == "execute"]
        copies = [e for e in conn.log if e[0] == "copy_expert"]

        # tables for present files got created...
        assert any("CREATE TABLE gtfs_stops" in s for s in executes)
        assert any("CREATE TABLE gtfs_routes" in s for s in executes)
        # ...and missing files (agency, trips, ...) were silently skipped, not errored
        assert not any("gtfs_agency" in s for s in executes if "CREATE TABLE" in s)

        assert len(copies) == 2  # stops + routes only
        assert any("Central Station" in c[2] for c in copies)

    print("load_gtfs self-check: OK")


if __name__ == "__main__":
    demo()
