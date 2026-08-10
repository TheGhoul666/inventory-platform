"""Reassignment ("גלגול") logic — spec ו.6 (AI-proposed) and ו.7 (manual
assign / driver search / trip closure). All reassignments in this system
are pre-trip by definition (נספח קנוני) — there's no "hot" reassignment.

Simplification: only scope=single_trip is implemented (round_trip_column
and full_day_schedule are not). Blast Radius here is a deterministic list
of the candidate's other trips that day, exactly as the spec requires
(not a prediction) — but the "Blast Radius Miss Rate" monitoring from
Record-and-Replay data (י.5) isn't built.
"""
from datetime import datetime, timedelta, timezone

from adapter import get_adapter
from models import Driver, DriverScheduleFrame, DriverMessage, Reassignment, Trip
from notify import notify_driver

CLOSURE_REASONS = {
    "trip_burn": {"mechanical_failure", "route_blocking_incident", "driver_awol_unresolved", "other"},
    "trip_no_show": {"no_driver_available", "no_vehicle_available", "other"},
}


def _now():
    return datetime.now(timezone.utc)


def _day_bounds(dt: datetime):
    start = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=1)


def _overlaps(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end


def is_trip_open(trip: Trip) -> bool:
    """A trip needs a (re)assignment if it has no driver, or its driver is AWOL."""
    if trip.driver_id is None:
        return True
    return bool(trip.driver and (trip.driver.awol_confirmed or trip.driver.status != "active"))


def compute_blast_radius(session, trip: Trip, candidate_driver_id: str) -> str:
    day_start, day_end = _day_bounds(trip.plan_start_time)
    others = (
        session.query(Trip)
        .filter(
            Trip.driver_id == candidate_driver_id,
            Trip.trip_id != trip.trip_id,
            Trip.plan_start_time >= day_start,
            Trip.plan_start_time < day_end,
            Trip.status.in_(["planned", "active"]),
        )
        .all()
    )
    if not others:
        return "No other trips scheduled for this driver today — no impact."
    parts = [f"{t.plan_start_time.strftime('%H:%M')} on line {t.line.line_number if t.line else t.line_id}" for t in others]
    return "Driver already has: " + "; ".join(parts)


def find_candidates(session, trip: Trip):
    """Active, licensed, non-conflicting drivers, ranked by least schedule impact."""
    candidates = (
        session.query(Driver)
        .filter(Driver.status == "active", Driver.driver_id != trip.driver_id)
        .all()
    )
    results = []
    for d in candidates:
        if d.license_expiry and d.license_expiry < trip.plan_start_time:
            continue
        conflict = (
            session.query(Trip)
            .filter(
                Trip.driver_id == d.driver_id,
                Trip.status.in_(["planned", "active"]),
            )
            .all()
        )
        if any(_overlaps(trip.plan_start_time, trip.plan_end_time, t.plan_start_time, t.plan_end_time) for t in conflict):
            continue
        summary = compute_blast_radius(session, trip, d.driver_id)
        impact = 0 if summary.startswith("No other") else summary.count(";") + 1
        results.append({"driver_id": d.driver_id, "full_name": d.full_name, "blast_radius_summary": summary, "impact": impact})
    return sorted(results, key=lambda r: (r["impact"], r["full_name"]))


def _append_to_schedule_frame(session, driver_id: str, trip: Trip):
    work_date, _ = _day_bounds(trip.plan_start_time)
    frame = (
        session.query(DriverScheduleFrame)
        .filter_by(driver_id=driver_id, work_date=work_date)
        .first()
    )
    if not frame:
        frame = DriverScheduleFrame(driver_id=driver_id, work_date=work_date, trip_slot_sequence=[])
        session.add(frame)
        session.flush()
    # ponytail: append-only sequence, not gap-aware re-ordering — fine for a demo, revisit for real dispatch use.
    seq = list(frame.trip_slot_sequence or [])
    if trip.trip_id not in seq:
        seq.append(trip.trip_id)
        frame.trip_slot_sequence = seq


def propose_reassignment(session, trip_id: str, initiated_by: str = "ai_engine") -> Reassignment | None:
    trip = session.query(Trip).get(trip_id)
    if trip is None:
        raise ValueError("trip not found")
    candidates = find_candidates(session, trip)
    if not candidates:
        return None
    best = candidates[0]
    r = Reassignment(
        trip_id=trip.trip_id,
        from_driver_id=trip.driver_id,
        to_driver_id=best["driver_id"],
        scope="single_trip",
        blast_radius_summary=best["blast_radius_summary"],
        status="proposed",
        initiated_by=initiated_by,
    )
    session.add(r)
    session.commit()
    session.refresh(r)
    return r


def approve_reassignment(session, reassignment_id: str) -> Reassignment:
    r = session.query(Reassignment).get(reassignment_id)
    if r is None:
        raise ValueError("reassignment not found")
    trip = session.query(Trip).get(r.trip_id)
    trip.driver_id = r.to_driver_id
    r.status = "executed"
    r.decided_at = _now()
    _append_to_schedule_frame(session, r.to_driver_id, trip)
    driver = session.query(Driver).get(r.to_driver_id)
    notify_driver(session, driver, f"שובצת לנסיעה בקו {trip.line.line_number if trip.line else trip.line_id} בשעה {trip.plan_start_time.strftime('%H:%M')}")
    get_adapter().write_trip_assignment(trip.trip_id, r.to_driver_id, trip.vehicle_id)
    session.commit()
    session.refresh(r)
    return r


def reject_reassignment(session, reassignment_id: str, reason: str) -> Reassignment:
    r = session.query(Reassignment).get(reassignment_id)
    if r is None:
        raise ValueError("reassignment not found")
    r.status = "rejected"
    r.rejection_reason = reason
    r.decided_at = _now()
    session.commit()
    session.refresh(r)
    return r


def find_available_drivers(session, start: datetime, end: datetime):
    """ו.7 FR-53 — dispatcher-initiated search, no AI proposal involved."""
    active = session.query(Driver).filter(Driver.status == "active").all()
    available = []
    for d in active:
        conflict = (
            session.query(Trip)
            .filter(Trip.driver_id == d.driver_id, Trip.status.in_(["planned", "active"]))
            .all()
        )
        if not any(_overlaps(start, end, t.plan_start_time, t.plan_end_time) for t in conflict):
            available.append(d)
    return available


def manual_assign(session, trip_id: str, driver_id: str) -> Reassignment:
    """ו.7 FR-53/54 — dispatcher picks a driver directly, no AI suggestion round-trip."""
    trip = session.query(Trip).get(trip_id)
    driver = session.query(Driver).get(driver_id)
    if trip is None or driver is None:
        raise ValueError("trip or driver not found")
    summary = compute_blast_radius(session, trip, driver_id)
    r = Reassignment(
        trip_id=trip.trip_id,
        from_driver_id=trip.driver_id,
        to_driver_id=driver_id,
        scope="single_trip",
        blast_radius_summary=summary,
        status="executed",
        initiated_by="dispatcher_manual",
        decided_at=_now(),
    )
    trip.driver_id = driver_id
    session.add(r)
    _append_to_schedule_frame(session, driver_id, trip)
    notify_driver(session, driver, f"שובצת לנסיעה בקו {trip.line.line_number if trip.line else trip.line_id} בשעה {trip.plan_start_time.strftime('%H:%M')}")
    get_adapter().write_trip_assignment(trip.trip_id, driver_id, trip.vehicle_id)
    session.commit()
    session.refresh(r)
    return r


def close_trip(session, trip_id: str, status: str, closure_reason: str) -> Trip:
    """ו.7 FR-55 — trip_burn / trip_no_show require a mandatory reason."""
    if status not in CLOSURE_REASONS:
        raise ValueError(f"status must be one of {list(CLOSURE_REASONS)}")
    if closure_reason not in CLOSURE_REASONS[status]:
        raise ValueError(f"closure_reason for {status} must be one of {CLOSURE_REASONS[status]}")
    trip = session.query(Trip).get(trip_id)
    if trip is None:
        raise ValueError("trip not found")
    trip.status = status
    trip.closure_reason = closure_reason
    get_adapter().write_trip_closure(trip.trip_id, status, closure_reason)
    session.commit()
    session.refresh(trip)
    return trip
