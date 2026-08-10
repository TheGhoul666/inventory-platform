"""SQLAlchemy models — one class per entity in spec appendix ו' (ו.1–ו.9),
plus driver_messages for the simulated WhatsApp channel (ט.1).

Audit fields (created_on/created_by/modified_on/owner_id) are kept as
plain columns, not backed by a real user/auth system — there isn't one in
this MVP. created_by/owner_id default to "system"/"dispatcher_demo".
ponytail: add real auth + FKs to a users table when there's more than one
demo dispatcher.
"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from db import Base


def _uuid() -> str:
    return str(uuid4())


def now() -> datetime:
    return datetime.now(timezone.utc)


def audit_columns():
    return dict(
        created_on=Column(DateTime, default=now),
        created_by=Column(String(100), default="system"),
        modified_on=Column(DateTime, default=now, onupdate=now),
        owner_id=Column(String(100), default="dispatcher_demo"),
    )


class Line(Base):
    __tablename__ = "lines"
    line_id = Column(String(36), primary_key=True, default=_uuid)
    line_number = Column(String(10), nullable=False)
    route_geometry = Column(JSON)  # [[lat, lon], ...] — from GTFS shapes.txt when loaded
    short_line_flag = Column(Boolean, default=False)
    accessibility_required = Column(Boolean, default=False)
    # use_alter: breaks the Line<->RouteDiversion circular FK so create_all can order the tables
    active_diversion_id = Column(
        String(36),
        ForeignKey("route_diversions.diversion_id", use_alter=True, name="fk_line_active_diversion"),
        nullable=True,
    )
    schedule_code = Column(String(50))
    created_on = Column(DateTime, default=now)
    created_by = Column(String(100), default="system")
    modified_on = Column(DateTime, default=now, onupdate=now)
    owner_id = Column(String(100), default="dispatcher_demo")

    trips = relationship("Trip", back_populates="line")


class Stop(Base):
    __tablename__ = "stops"
    stop_id = Column(String(36), primary_key=True, default=_uuid)
    official_name = Column(String(100), nullable=False)
    gazetteer_aliases = Column(JSON, default=list)
    lat = Column(Float)
    lon = Column(Float)
    line_ids = Column(JSON, default=list)  # many-to-many kept simple as an id list for MVP
    accessibility_flag = Column(Boolean, default=False)
    # stop_code: GTFS stops.txt "stop_code" — same id as data.gov.il station registry's
    # StationId, so it's the join key station_registry_sync.py matches on.
    stop_code = Column(String(20), nullable=True, index=True)
    city_name = Column(String(100), nullable=True)
    metropolitan_name = Column(String(100), nullable=True)
    operator_type_name = Column(String(100), nullable=True)
    created_on = Column(DateTime, default=now)
    created_by = Column(String(100), default="system")
    modified_on = Column(DateTime, default=now, onupdate=now)
    owner_id = Column(String(100), default="dispatcher_demo")


class Driver(Base):
    __tablename__ = "drivers"
    driver_id = Column(String(36), primary_key=True, default=_uuid)
    full_name = Column(String(100), nullable=False)
    license_type = Column(String(30), nullable=False)  # license_d | license_d1 | license_articulated
    license_expiry = Column(DateTime)
    whatsapp_number = Column(String(20))
    onboarding_date = Column(DateTime, default=now)
    absence_signal = Column(Boolean, default=False)
    awol_confirmed = Column(Boolean, default=False)
    status = Column(String(20), default="active")  # active | unavailable | departed
    exit_date = Column(DateTime, nullable=True)
    created_on = Column(DateTime, default=now)
    created_by = Column(String(100), default="system")
    modified_on = Column(DateTime, default=now, onupdate=now)
    owner_id = Column(String(100), default="dispatcher_demo")

    trips = relationship("Trip", back_populates="driver", foreign_keys="Trip.driver_id")


class Vehicle(Base):
    __tablename__ = "vehicles"
    vehicle_id = Column(String(36), primary_key=True, default=_uuid)
    license_plate = Column(String(20), nullable=False)
    telematics_tier = Column(String(10), default="full")  # full | partial | basic
    accessibility_flag = Column(Boolean, default=False)
    insurance_expiry = Column(DateTime)
    sensor_health_status = Column(String(20), default="healthy")  # healthy | needs_check | dead
    last_known_lat = Column(Float, nullable=True)
    last_known_lon = Column(Float, nullable=True)
    gps_confidence_score = Column(Numeric(5, 2), default=0)  # 99 / 85 / 60 / 0 per ג.1
    created_on = Column(DateTime, default=now)
    created_by = Column(String(100), default="system")
    modified_on = Column(DateTime, default=now, onupdate=now)
    owner_id = Column(String(100), default="dispatcher_demo")

    trips = relationship("Trip", back_populates="vehicle")


class DriverScheduleFrame(Base):
    __tablename__ = "driver_schedule_frames"
    frame_id = Column(String(36), primary_key=True, default=_uuid)
    driver_id = Column(String(36), ForeignKey("drivers.driver_id"), nullable=False)
    work_date = Column(DateTime, nullable=False)  # date-only in practice; DateTime kept for simplicity
    trip_slot_sequence = Column(JSON, default=list)  # ordered list of trip_id — Collection, not Stack
    tag_trip_id = Column(String(36), ForeignKey("trips.trip_id"), nullable=True)
    split_segment_number = Column(Integer, default=1)
    work_hours_start_ref = Column(DateTime, nullable=True)
    status = Column(String(10), default="draft")  # draft | final
    created_on = Column(DateTime, default=now)
    created_by = Column(String(100), default="system")
    modified_on = Column(DateTime, default=now, onupdate=now)
    owner_id = Column(String(100), default="dispatcher_demo")


class Trip(Base):
    __tablename__ = "trips"
    trip_id = Column(String(36), primary_key=True, default=_uuid)
    line_id = Column(String(36), ForeignKey("lines.line_id"), nullable=False)
    driver_id = Column(String(36), ForeignKey("drivers.driver_id"), nullable=True)
    vehicle_id = Column(String(36), ForeignKey("vehicles.vehicle_id"), nullable=True)
    plan_start_time = Column(DateTime, nullable=False)
    plan_end_time = Column(DateTime, nullable=False)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    schedule_variance = Column(Integer, nullable=True)  # minutes, actual - plan
    late_departure_severity = Column(String(20), nullable=True)  # minor|moderate|major_delay
    trip_tag = Column(String(20), default="none")  # new_start_flag (pink) | critical_flag (red) | none
    status = Column(String(20), default="planned")  # planned|active|completed|trip_burn|trip_no_show
    diversion_active = Column(Boolean, default=False)
    diversion_id = Column(String(36), ForeignKey("route_diversions.diversion_id"), nullable=True)
    trip_risk_score = Column(Numeric(4, 3), nullable=True)  # 0-1, attributed to the TRIP not the driver
    accessibility_required = Column(Boolean, default=False)
    closure_reason = Column(String(50), nullable=True)
    created_on = Column(DateTime, default=now)
    created_by = Column(String(100), default="system")
    modified_on = Column(DateTime, default=now, onupdate=now)
    owner_id = Column(String(100), default="dispatcher_demo")

    line = relationship("Line", back_populates="trips")
    driver = relationship("Driver", back_populates="trips", foreign_keys=[driver_id])
    vehicle = relationship("Vehicle", back_populates="trips")


class Reassignment(Base):
    __tablename__ = "reassignments"
    reassignment_id = Column(String(36), primary_key=True, default=_uuid)
    trip_id = Column(String(36), ForeignKey("trips.trip_id"), nullable=False)
    from_driver_id = Column(String(36), ForeignKey("drivers.driver_id"), nullable=True)
    to_driver_id = Column(String(36), ForeignKey("drivers.driver_id"), nullable=False)
    scope = Column(String(30), default="single_trip")  # single_trip only, implemented in this MVP
    blast_radius_summary = Column(Text)
    status = Column(String(20), default="proposed")  # proposed|approved|rejected|executed
    rejection_reason = Column(String(30), nullable=True)
    proposed_at = Column(DateTime, default=now)
    decided_at = Column(DateTime, nullable=True)
    initiated_by = Column(String(20), default="ai_engine")  # ai_engine | dispatcher_manual
    created_on = Column(DateTime, default=now)
    created_by = Column(String(100), default="system")
    modified_on = Column(DateTime, default=now, onupdate=now)
    owner_id = Column(String(100), default="dispatcher_demo")


class RouteBlockingIncident(Base):
    __tablename__ = "route_blocking_incidents"
    incident_id = Column(String(36), primary_key=True, default=_uuid)
    source = Column(String(30), default="dispatcher_manual")  # sos_report|dispatcher_manual|external_traffic_api
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    location_desc = Column(String(200), nullable=True)
    detected_at = Column(DateTime, default=now)
    cleared_at = Column(DateTime, nullable=True)
    status = Column(String(10), default="active")  # active | closed
    affected_line_ids = Column(JSON, default=list)
    created_on = Column(DateTime, default=now)
    created_by = Column(String(100), default="system")
    modified_on = Column(DateTime, default=now, onupdate=now)
    owner_id = Column(String(100), default="dispatcher_demo")


class RouteDiversion(Base):
    __tablename__ = "route_diversions"
    diversion_id = Column(String(36), primary_key=True, default=_uuid)
    line_id = Column(String(36), ForeignKey("lines.line_id"), nullable=False)
    incident_id = Column(String(36), ForeignKey("route_blocking_incidents.incident_id"), nullable=False)
    alternate_geometry = Column(JSON, nullable=True)
    skipped_stops = Column(JSON, default=list)
    estimated_added_time = Column(Integer, nullable=True)  # minutes
    approval_status = Column(String(20), default="pending_approval")
    approved_by = Column(String(100), nullable=True)
    activated_at = Column(DateTime, nullable=True)
    reverted_at = Column(DateTime, nullable=True)
    created_on = Column(DateTime, default=now)
    created_by = Column(String(100), default="system")
    modified_on = Column(DateTime, default=now, onupdate=now)
    owner_id = Column(String(100), default="dispatcher_demo")


class DriverMessage(Base):
    """SIMULATED WhatsApp channel (ט.1) — no real Meta/WhatsApp Business API here."""
    __tablename__ = "driver_messages"
    message_id = Column(String(36), primary_key=True, default=_uuid)
    driver_id = Column(String(36), ForeignKey("drivers.driver_id"), nullable=False)
    direction = Column(String(10), default="outbound")
    body = Column(Text, nullable=False)
    sent_at = Column(DateTime, default=now)
    channel = Column(String(20), default="whatsapp_sim")
