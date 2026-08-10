"""Adapter Service (spec יג.1, referenced by ב.5/ב.5.1) — the ONLY layer
that's supposed to know which fleet-management product is behind it.
Swapping vendors means swapping the instance returned by get_adapter();
nothing else in the app touches vendor specifics — that's the whole
point of ב.5.1 ("not an architectural lock-in").

No real vendor is contracted yet (see README) — both adapters below are
mocks that log what they *would* send, standing in for a real HTTP/MQTT
integration once ב.5.1's Phase-0 decision is closed with an actual
supplier.
"""
from abc import ABC, abstractmethod
from typing import Optional


class FleetSoftwareAdapter(ABC):
    @abstractmethod
    def write_trip_assignment(self, trip_id: str, driver_id: str, vehicle_id: Optional[str]) -> None: ...

    @abstractmethod
    def write_trip_closure(self, trip_id: str, status: str, closure_reason: str) -> None: ...


class MockNativeVendorAdapter(FleetSoftwareAdapter):
    """Stands in for Option A (ב.5) — an existing native product (YIT-pattern) already
    integrated with ISR. This is the decision made in README — Option A."""

    def write_trip_assignment(self, trip_id, driver_id, vehicle_id):
        print(f"[adapter:native_mock] POST /assignments  trip={trip_id} driver={driver_id} vehicle={vehicle_id}")

    def write_trip_closure(self, trip_id, status, closure_reason):
        print(f"[adapter:native_mock] POST /trips/{trip_id}/close  status={status} reason={closure_reason}")


class InHouseAdapter(FleetSoftwareAdapter):
    """Stands in for Option B (ב.5) — talking straight to ISR/Teltonika, no vendor
    middleman. Not wired in by default; exists to prove the swap really is a
    one-line change (ב.5.1), not a rewrite."""

    def write_trip_assignment(self, trip_id, driver_id, vehicle_id):
        print(f"[adapter:in_house] MQTT publish assignment  trip={trip_id} driver={driver_id} vehicle={vehicle_id}")

    def write_trip_closure(self, trip_id, status, closure_reason):
        print(f"[adapter:in_house] MQTT publish closure  trip={trip_id} status={status} reason={closure_reason}")


_adapter: FleetSoftwareAdapter = MockNativeVendorAdapter()  # ב.5.1 Phase-0 decision: Option A


def get_adapter() -> FleetSoftwareAdapter:
    return _adapter
