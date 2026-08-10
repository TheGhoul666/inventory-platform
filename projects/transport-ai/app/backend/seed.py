"""Seed demo drivers/vehicles/trips — standalone, no GTFS/network dependency
required. Safe to run before or after gtfs_sync.py: this only checks/creates
Drivers (its own domain), and reuses whatever Lines already exist (synthetic
or real, from gtfs_sync) instead of assuming it owns the Line table.
"""
from datetime import datetime, timedelta, timezone

from db import Base, SessionLocal, engine
from models import Driver, Line, Stop, Trip, Vehicle

LINES = [("1", "32.0800,34.7800 32.0850,34.7850 32.0900,34.7900"), ("5", None), ("18", None)]
STOPS = [
    ("Central Bus Station", 32.0809, 34.7806),
    ("Rothschild Blvd", 32.0648, 34.7737),
    ("Azrieli Center", 32.0740, 34.7925),
    ("HaShalom Junction", 32.0731, 34.7930),
]
DRIVERS = [
    ("Yossi Cohen", "license_d"),
    ("Miriam Levi", "license_d"),
    ("Ahmad Khalil", "license_d1"),
    ("Dana Peretz", "license_articulated"),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Driver).count() > 0:
            print("already seeded, skipping")
            return

        lines = db.query(Line).all()
        if lines:
            print(f"reusing {len(lines)} existing line(s) (from gtfs_sync or a prior seed)")
        else:
            for number, geom in LINES:
                geometry = None
                if geom:
                    geometry = [[float(p.split(",")[0]), float(p.split(",")[1])] for p in geom.split()]
                line = Line(line_number=number, route_geometry=geometry)
                db.add(line)
                lines.append(line)
            db.flush()

        if db.query(Stop).count() == 0:
            for name, lat, lon in STOPS:
                db.add(Stop(official_name=name, lat=lat, lon=lon, line_ids=[lines[0].line_id]))

        drivers = []
        for name, lic in DRIVERS:
            d = Driver(full_name=name, license_type=lic, whatsapp_number="+9725" + str(1000000 + len(drivers)))
            db.add(d)
            drivers.append(d)
        db.flush()

        vehicles = []
        for i in range(4):
            v = Vehicle(
                license_plate=f"12-345-{i}",
                telematics_tier="full" if i < 2 else "basic",
                last_known_lat=32.08 + i * 0.01,
                last_known_lon=34.78 + i * 0.01,
            )
            db.add(v)
            vehicles.append(v)
        db.flush()

        now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
        for i in range(6):
            start = now + timedelta(hours=i % 3)
            db.add(
                Trip(
                    line_id=lines[i % len(lines)].line_id,
                    driver_id=drivers[i % 2].driver_id if i % 3 != 0 else None,  # leave some trips open
                    vehicle_id=vehicles[i % len(vehicles)].vehicle_id,
                    plan_start_time=start,
                    plan_end_time=start + timedelta(minutes=45),
                )
            )

        db.commit()
        print(f"seeded: {len(lines)} line(s), 4 drivers, 4 vehicles, 6 trips (some unassigned)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
