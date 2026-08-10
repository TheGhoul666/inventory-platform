"""תחבורה AI — Phase-1 MVP demo API.

Single FastAPI service covering the AI/ERP layers of ב.4 as one process
(not separate Python+FastAPI / Java+Spring Boot services, and no
Kafka/Kong/GKE) — a monolith is the lazy-correct choice for an MVP demo at
this scale; split out when real throughput or team boundaries demand it.
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import inspect

import reassignment as reassign
from db import Base, SessionLocal, engine
from gps_sim import tick_vehicle
from models import Driver, Line, RouteBlockingIncident, RouteDiversion, Stop, Trip, Vehicle, DriverMessage, Reassignment

app = FastAPI(title="Transport AI — MVP demo")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


def row_to_dict(obj):
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


def rows(objs):
    return [row_to_dict(o) for o in objs]


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)  # ponytail: no Alembic — add real migrations before this touches prod data
    asyncio.create_task(_gps_sim_loop())


async def _gps_sim_loop():
    while True:
        try:
            db = SessionLocal()
            for v in db.query(Vehicle).all():
                tick_vehicle(v)
            db.commit()
            db.close()
        except Exception as exc:  # pragma: no cover
            print("gps sim tick failed:", exc)
        await asyncio.sleep(5)  # spec ד — one telemetry report per vehicle per 5s


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/vehicles")
def list_vehicles():
    db = SessionLocal()
    try:
        return rows(db.query(Vehicle).all())
    finally:
        db.close()


@app.get("/drivers")
def list_drivers():
    db = SessionLocal()
    try:
        return rows(db.query(Driver).all())
    finally:
        db.close()


@app.get("/drivers/available")
def drivers_available(start: datetime, end: datetime):
    db = SessionLocal()
    try:
        return rows(reassign.find_available_drivers(db, start, end))
    finally:
        db.close()


@app.get("/drivers/{driver_id}/messages")
def driver_messages(driver_id: str):
    db = SessionLocal()
    try:
        msgs = db.query(DriverMessage).filter_by(driver_id=driver_id).order_by(DriverMessage.sent_at.desc()).all()
        return rows(msgs)
    finally:
        db.close()


@app.get("/drivers/{driver_id}/trips-today")
def driver_trips_today(driver_id: str):
    """Backs the simulated native driver-app view (driver.html) — spec ב.4's 'Kotlin driver app'."""
    db = SessionLocal()
    try:
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow = today + timedelta(days=1)
        trips = (
            db.query(Trip)
            .filter(Trip.driver_id == driver_id, Trip.plan_start_time >= today, Trip.plan_start_time < tomorrow)
            .order_by(Trip.plan_start_time)
            .all()
        )
        return rows(trips)
    finally:
        db.close()


@app.post("/drivers/{driver_id}/checkin")
def driver_checkin(driver_id: str):
    """Morning vehicle-in-place confirmation (ה.2), via the app instead of WhatsApp."""
    db = SessionLocal()
    try:
        driver = db.query(Driver).get(driver_id)
        if not driver:
            raise HTTPException(404, "driver not found")
        msg = DriverMessage(driver_id=driver_id, direction="inbound", body="Vehicle confirmed in place", channel="app_checkin")
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return row_to_dict(msg)
    finally:
        db.close()


@app.get("/lines")
def list_lines():
    db = SessionLocal()
    try:
        return rows(db.query(Line).all())
    finally:
        db.close()


@app.get("/stops")
def list_stops():
    db = SessionLocal()
    try:
        return rows(db.query(Stop).all())
    finally:
        db.close()


@app.get("/trips")
def list_trips(status: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(Trip)
        if status:
            q = q.filter(Trip.status == status)
        return rows(q.all())
    finally:
        db.close()


@app.get("/trips/{trip_id}")
def get_trip(trip_id: str):
    db = SessionLocal()
    try:
        t = db.query(Trip).get(trip_id)
        if not t:
            raise HTTPException(404, "trip not found")
        return row_to_dict(t)
    finally:
        db.close()


class AssignBody(BaseModel):
    driver_id: str


@app.post("/trips/{trip_id}/assign")
def assign_trip(trip_id: str, body: AssignBody):
    db = SessionLocal()
    try:
        r = reassign.manual_assign(db, trip_id, body.driver_id)
        return row_to_dict(r)
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        db.close()


class CloseBody(BaseModel):
    status: str  # trip_burn | trip_no_show
    closure_reason: str


@app.post("/trips/{trip_id}/close")
def close_trip(trip_id: str, body: CloseBody):
    db = SessionLocal()
    try:
        t = reassign.close_trip(db, trip_id, body.status, body.closure_reason)
        return row_to_dict(t)
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        db.close()


@app.get("/trips/{trip_id}/candidates")
def trip_candidates(trip_id: str):
    db = SessionLocal()
    try:
        trip = db.query(Trip).get(trip_id)
        if not trip:
            raise HTTPException(404, "trip not found")
        return reassign.find_candidates(db, trip)
    finally:
        db.close()


class ProposeBody(BaseModel):
    initiated_by: str = "ai_engine"


@app.post("/trips/{trip_id}/propose-reassignment")
def propose(trip_id: str, body: ProposeBody = ProposeBody()):
    db = SessionLocal()
    try:
        r = reassign.propose_reassignment(db, trip_id, body.initiated_by)
        if r is None:
            raise HTTPException(409, "no available candidate driver")
        return row_to_dict(r)
    except ValueError as e:
        raise HTTPException(400, str(e))
    finally:
        db.close()


@app.get("/reassignments")
def list_reassignments(status: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(Reassignment)
        if status:
            q = q.filter(Reassignment.status == status)
        return rows(q.order_by(Reassignment.proposed_at.desc()).all())
    finally:
        db.close()


@app.post("/reassignments/{reassignment_id}/approve")
def approve(reassignment_id: str):
    db = SessionLocal()
    try:
        r = reassign.approve_reassignment(db, reassignment_id)
        return row_to_dict(r)
    except ValueError as e:
        raise HTTPException(404, str(e))
    finally:
        db.close()


class RejectBody(BaseModel):
    reason: str = "other"


@app.post("/reassignments/{reassignment_id}/reject")
def reject(reassignment_id: str, body: RejectBody = RejectBody()):
    db = SessionLocal()
    try:
        r = reassign.reject_reassignment(db, reassignment_id, body.reason)
        return row_to_dict(r)
    except ValueError as e:
        raise HTTPException(404, str(e))
    finally:
        db.close()


class IncidentCreate(BaseModel):
    source: str = "dispatcher_manual"
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    location_desc: Optional[str] = None
    affected_line_ids: list[str] = []


@app.get("/incidents")
def list_incidents(status: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(RouteBlockingIncident)
        if status:
            q = q.filter(RouteBlockingIncident.status == status)
        return rows(q.all())
    finally:
        db.close()


@app.post("/incidents")
def create_incident(body: IncidentCreate):
    """affected_line_ids is taken as given by the caller here — the spec's real
    geometric intersection against route_geometry (ו.5) isn't implemented."""
    db = SessionLocal()
    try:
        inc = RouteBlockingIncident(**body.dict())
        db.add(inc)
        db.commit()
        db.refresh(inc)
        return row_to_dict(inc)
    finally:
        db.close()


@app.post("/incidents/{incident_id}/close")
def close_incident(incident_id: str):
    db = SessionLocal()
    try:
        inc = db.query(RouteBlockingIncident).get(incident_id)
        if not inc:
            raise HTTPException(404, "incident not found")
        inc.status = "closed"
        inc.cleared_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(inc)
        return row_to_dict(inc)
    finally:
        db.close()


class DiversionCreate(BaseModel):
    line_id: str
    incident_id: str
    alternate_geometry: Optional[list] = None
    skipped_stops: list[str] = []
    estimated_added_time: Optional[int] = None


@app.get("/diversions")
def list_diversions(incident_id: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(RouteDiversion)
        if incident_id:
            q = q.filter(RouteDiversion.incident_id == incident_id)
        return rows(q.all())
    finally:
        db.close()


@app.post("/diversions")
def create_diversion(body: DiversionCreate):
    """Dispatcher-proposed alternate route, pending approval — ו.5. Real alternate_geometry
    would come from Google Maps Directions API; here the caller supplies it (or leaves it null)."""
    db = SessionLocal()
    try:
        d = RouteDiversion(**body.dict())
        db.add(d)
        db.commit()
        db.refresh(d)
        return row_to_dict(d)
    finally:
        db.close()


@app.post("/diversions/{diversion_id}/approve")
def approve_diversion(diversion_id: str):
    db = SessionLocal()
    try:
        d = db.query(RouteDiversion).get(diversion_id)
        if not d:
            raise HTTPException(404, "diversion not found")
        d.approval_status = "approved"
        d.approved_by = "dispatcher_demo"
        d.activated_at = datetime.now(timezone.utc)
        line = db.query(Line).get(d.line_id)
        if line:
            line.active_diversion_id = d.diversion_id
        db.commit()
        db.refresh(d)
        return row_to_dict(d)
    finally:
        db.close()
