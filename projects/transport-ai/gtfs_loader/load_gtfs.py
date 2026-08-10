"""GTFS static loader — תחבורה AI spec section ד.3 / FR-56.

Downloads Israel MOT's national GTFS feed (gtfs.mot.gov.il), extracts it,
and loads each file into its own PostgreSQL table (gtfs_<name>), then
indexes the join keys. Feeds route_geometry (from shapes) and
stop location/official_name (from stops) per the spec.

Usage:
    python load_gtfs.py --dsn postgresql://user:pass@host/db
    python load_gtfs.py --demo    # offline self-check, see test_load_gtfs.py
"""
import argparse
import csv
import sys
import tempfile
import zipfile
from pathlib import Path

import psycopg2
import requests

# ponytail: MOT has renamed this file before — verify against gtfs.mot.gov.il before Phase 0 go-live.
GTFS_URL = "https://gtfs.mot.gov.il/gtfsfiles/israel-public-transportation.zip"

# The seven tables named in the spec. Columns are read from each file's own
# header rather than hardcoded — real-world feeds carry optional/extra
# columns beyond the official spec, and this avoids drifting out of sync.
# ponytail: no schema validation beyond "table exists"; add typed views if downstream queries need it.
FILES = ["agency", "routes", "stops", "trips", "stop_times", "shapes", "calendar"]

# Join keys worth indexing, per spec ד.3.
INDEX_COLS = {
    "stops": ["stop_id"],
    "routes": ["route_id"],
    "trips": ["trip_id", "route_id", "shape_id"],
    "stop_times": ["trip_id", "stop_id"],
    "shapes": ["shape_id"],
}


def download_gtfs(dest: Path, url: str = GTFS_URL) -> Path:
    r = requests.get(url, stream=True, timeout=300)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def extract_gtfs(zip_path: Path, out_dir: Path) -> Path:
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(out_dir)
    return out_dir


def setup_database(conn, gtfs_dir: Path) -> None:
    """(Re)create one table per present GTFS file, columns = file's own header, all TEXT."""
    with conn.cursor() as cur:
        for name in FILES:
            path = gtfs_dir / f"{name}.txt"
            if not path.exists():
                print(f"skip {name}: not present in this feed", file=sys.stderr)
                continue
            with open(path, encoding="utf-8-sig", newline="") as f:
                header = next(csv.reader(f))
            cur.execute(f"DROP TABLE IF EXISTS gtfs_{name} CASCADE")
            cols_sql = ", ".join(f'"{c}" TEXT' for c in header)
            cur.execute(f"CREATE TABLE gtfs_{name} ({cols_sql})")
    conn.commit()


def load_data_to_postgres(conn, gtfs_dir: Path) -> None:
    """COPY each present file straight in — far faster than row-by-row INSERT at feed scale."""
    with conn.cursor() as cur:
        for name in FILES:
            path = gtfs_dir / f"{name}.txt"
            if not path.exists():
                continue
            with open(path, encoding="utf-8-sig", newline="") as f:
                cur.copy_expert(f"COPY gtfs_{name} FROM STDIN WITH (FORMAT csv, HEADER true)", f)
    conn.commit()


def create_indexes(conn) -> None:
    with conn.cursor() as cur:
        for table, cols in INDEX_COLS.items():
            for col in cols:
                cur.execute(
                    f'CREATE INDEX IF NOT EXISTS idx_gtfs_{table}_{col} ON gtfs_{table} ("{col}")'
                )
    conn.commit()


def run(dsn: str, url: str = GTFS_URL) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        zip_path = download_gtfs(tmp / "gtfs.zip", url)
        gtfs_dir = extract_gtfs(zip_path, tmp / "extracted")
        conn = psycopg2.connect(dsn)
        try:
            setup_database(conn, gtfs_dir)
            load_data_to_postgres(conn, gtfs_dir)
            create_indexes(conn)
        finally:
            conn.close()
    print("GTFS load complete.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--dsn", help="postgresql://user:pass@host/db")
    p.add_argument("--url", default=GTFS_URL, help="override feed URL")
    p.add_argument("--demo", action="store_true", help="run offline self-check instead")
    args = p.parse_args()

    if args.demo:
        import test_load_gtfs
        test_load_gtfs.demo()
    elif not args.dsn:
        p.error("--dsn is required (or pass --demo)")
    else:
        run(args.dsn, args.url)
