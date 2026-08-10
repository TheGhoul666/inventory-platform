"""Offline self-check — SQLite temp file, no Postgres/Docker needed.

Run: python test_backend.py
"""
import os
import tempfile
from datetime import datetime, timedelta, timezone

_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["DATABASE_URL"] = f"sqlite:///{_db_file.name}"

import adapter as adapter_mod  # noqa: E402
import reassignment as reassign  # noqa: E402
from db import Base, SessionLocal, engine  # noqa: E402
from gps_sim import fuse_gps, validate_point  # noqa: E402
from models import Driver, DriverMessage, Line, Trip  # noqa: E402
from notify import notify_driver  # noqa: E402


def test_gps_validation():
    assert validate_point(0, 0) is False, "0,0 must be rejected"
    assert validate_point(32.08, 34.78) is True
    assert validate_point(10, 10) is False, "outside Israel must be rejected"
    assert validate_point(32.7, 34.78, prev=(32.08, 34.78)) is False, "50km+ jump must be rejected"
    assert validate_point(32.08, 34.85, prev=(32.08, 34.78), dt_seconds=5) is False, ">120km/h implied speed must be rejected"


def test_gps_fusion_confidence():
    p = (32.08, 34.78)
    near = (32.08001, 34.78001)
    far = (31.0, 34.0)
    assert fuse_gps([p, near, near])[2] == 99
    assert fuse_gps([p, near, far])[2] == 85
    assert fuse_gps([p, None, None])[2] == 60
    assert fuse_gps([None, None, None])[2] == 0


def _fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return SessionLocal()


def test_reassignment_candidates_and_blast_radius():
    db = _fresh_db()
    line = Line(line_number="1")
    db.add(line)
    db.flush()

    busy = Driver(full_name="Busy Driver", license_type="license_d")
    free = Driver(full_name="Free Driver", license_type="license_d")
    db.add_all([busy, free])
    db.flush()

    start = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)
    other_trip = Trip(line_id=line.line_id, driver_id=busy.driver_id, plan_start_time=start, plan_end_time=start + timedelta(minutes=30))
    open_trip = Trip(line_id=line.line_id, driver_id=None, plan_start_time=start, plan_end_time=start + timedelta(minutes=30))
    db.add_all([other_trip, open_trip])
    db.commit()

    assert reassign.is_trip_open(open_trip) is True

    candidates = reassign.find_candidates(db, open_trip)
    ids = {c["driver_id"] for c in candidates}
    assert busy.driver_id not in ids, "driver with an overlapping trip must be excluded"
    assert free.driver_id in ids

    r = reassign.propose_reassignment(db, open_trip.trip_id)
    assert r is not None and r.to_driver_id == free.driver_id and r.status == "proposed"

    approved = reassign.approve_reassignment(db, r.reassignment_id)
    assert approved.status == "executed"
    db.refresh(open_trip)
    assert open_trip.driver_id == free.driver_id
    db.close()


def test_close_trip_requires_valid_reason():
    db = _fresh_db()
    line = Line(line_number="1")
    db.add(line)
    db.flush()
    start = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)
    trip = Trip(line_id=line.line_id, plan_start_time=start, plan_end_time=start + timedelta(minutes=30))
    db.add(trip)
    db.commit()

    try:
        reassign.close_trip(db, trip.trip_id, "trip_burn", "not_a_real_reason")
        raise AssertionError("should have rejected an invalid closure_reason")
    except ValueError:
        pass

    closed = reassign.close_trip(db, trip.trip_id, "trip_burn", "mechanical_failure")
    assert closed.status == "trip_burn" and closed.closure_reason == "mechanical_failure"
    db.close()


def test_notify_falls_back_to_ivr_when_no_whatsapp():
    db = _fresh_db()
    has_whatsapp = Driver(full_name="Has WhatsApp", license_type="license_d", whatsapp_number="+972500000000")
    no_whatsapp = Driver(full_name="No WhatsApp", license_type="license_d", whatsapp_number=None)
    db.add_all([has_whatsapp, no_whatsapp])
    db.commit()

    notify_driver(db, has_whatsapp, "hello")
    db.commit()
    sent = db.query(DriverMessage).filter_by(driver_id=has_whatsapp.driver_id).all()
    assert len(sent) == 1 and sent[0].channel == "whatsapp_sim"

    notify_driver(db, no_whatsapp, "hello")
    db.commit()
    sent = db.query(DriverMessage).filter_by(driver_id=no_whatsapp.driver_id).all()
    assert len(sent) == 2, "IVR call logs an outbound message plus a simulated DTMF reply"
    assert all(m.channel == "ivr_sim" for m in sent)
    db.close()


def test_adapter_is_called_on_assignment():
    db = _fresh_db()
    line = Line(line_number="1")
    driver = Driver(full_name="Adapter Test Driver", license_type="license_d")
    db.add_all([line, driver])
    db.flush()
    start = datetime(2026, 1, 5, 8, 0, tzinfo=timezone.utc)
    trip = Trip(line_id=line.line_id, plan_start_time=start, plan_end_time=start + timedelta(minutes=30))
    db.add(trip)
    db.commit()

    class SpyAdapter:
        def __init__(self):
            self.calls = []

        def write_trip_assignment(self, *args):
            self.calls.append(("assign", args))

        def write_trip_closure(self, *args):
            self.calls.append(("close", args))

    spy = SpyAdapter()
    original = adapter_mod._adapter
    adapter_mod._adapter = spy
    try:
        reassign.manual_assign(db, trip.trip_id, driver.driver_id)
        assert spy.calls and spy.calls[0][0] == "assign", "swapping the adapter must actually change who gets called"
    finally:
        adapter_mod._adapter = original
    db.close()


def demo():
    test_gps_validation()
    test_gps_fusion_confidence()
    test_reassignment_candidates_and_blast_radius()
    test_close_trip_requires_valid_reason()
    test_notify_falls_back_to_ivr_when_no_whatsapp()
    test_adapter_is_called_on_assignment()
    print("transport-ai backend self-check: OK")


if __name__ == "__main__":
    demo()
