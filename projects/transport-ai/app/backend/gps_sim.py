"""SIMULATED three-source GPS fusion (spec ג.1/ג.2). There is no real
Teltonika/ISR/Itouran hardware here — each "source" is a random walk with
its own dropout rate, standing in for a vehicle's real telemetry feed.
Pure functions below (validate_point, fuse_gps) are the real logic and are
covered by test_backend.py; simulate_tick() is just a data generator.
"""
import math
import random
from datetime import datetime, timezone

# Israel bounding box (ג.2 — "outside Israel" rejection)
LAT_MIN, LAT_MAX = 29.4, 33.4
LON_MIN, LON_MAX = 34.2, 35.95

MAX_JUMP_KM = 50
MAX_SPEED_KMH = 120
AGREE_RADIUS_M = 30  # how close two readings must be to "agree"

# Per-source simulated dropout probability (source 3 = driver's phone, flakiest)
SOURCE_DROPOUT = [0.05, 0.15, 0.25]
SOURCE_JITTER_M = [3, 8, 15]  # ISR is most precise, phone least


def haversine_m(a, b) -> float:
    lat1, lon1 = a
    lat2, lon2 = b
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def validate_point(lat, lon, prev=None, dt_seconds=None):
    """ג.2 — reject readings that are protocol-valid but physically impossible."""
    if lat == 0 and lon == 0:
        return False
    if not (LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX):
        return False
    if prev is not None:
        dist_km = haversine_m(prev, (lat, lon)) / 1000
        if dist_km > MAX_JUMP_KM:
            return False
        if dt_seconds and dt_seconds > 0:
            speed_kmh = dist_km / (dt_seconds / 3600)
            if speed_kmh > MAX_SPEED_KMH:
                return False
    return True


def fuse_gps(readings, prev=None, dt_seconds=None):
    """readings: list of (lat, lon) or None (source didn't report this tick).
    Returns (lat, lon, confidence) — confidence in {0, 60, 85, 99} per ג.1.
    """
    valid = [
        p for p in readings
        if p is not None and validate_point(p[0], p[1], prev, dt_seconds)
    ]
    if not valid:
        return None, None, 0
    if len(valid) == 1:
        lat, lon = valid[0]
        return lat, lon, 60

    def agree(a, b):
        return haversine_m(a, b) <= AGREE_RADIUS_M

    best_cluster = max(([p for p in valid if agree(p, anchor)] for anchor in valid), key=len)
    lat = sum(p[0] for p in best_cluster) / len(best_cluster)
    lon = sum(p[1] for p in best_cluster) / len(best_cluster)
    confidence = 99 if len(best_cluster) == 3 else 85 if len(best_cluster) == 2 else 60
    return lat, lon, confidence


def _jitter(lat, lon, meters):
    # ~1 degree lat = 111km; cheap local approximation, fine at city scale
    dlat = (random.uniform(-meters, meters)) / 111000
    dlon = (random.uniform(-meters, meters)) / (111000 * math.cos(math.radians(lat or 32)))
    return (lat or 32.08) + dlat, (lon or 34.78) + dlon


def simulate_readings(prev_lat, prev_lon):
    """Generate this tick's 3 simulated source readings from a vehicle's last position."""
    base_lat = prev_lat if prev_lat is not None else random.uniform(31.8, 32.3)
    base_lon = prev_lon if prev_lon is not None else random.uniform(34.7, 35.0)
    # small forward drift so vehicles visibly move on the map
    base_lat += random.uniform(-0.0008, 0.0008)
    base_lon += random.uniform(-0.0008, 0.0008)

    readings = []
    for dropout, jitter_m in zip(SOURCE_DROPOUT, SOURCE_JITTER_M):
        if random.random() < dropout:
            readings.append(None)
        else:
            readings.append(_jitter(base_lat, base_lon, jitter_m))
    return readings


def tick_vehicle(vehicle, dt_seconds=5):
    """Advance one vehicle by one simulated telemetry tick. Mutates and returns the vehicle."""
    prev = (vehicle.last_known_lat, vehicle.last_known_lon)
    prev = prev if prev[0] is not None else None
    readings = simulate_readings(vehicle.last_known_lat, vehicle.last_known_lon)
    lat, lon, confidence = fuse_gps(readings, prev=prev, dt_seconds=dt_seconds)
    if lat is not None:
        vehicle.last_known_lat = lat
        vehicle.last_known_lon = lon
    vehicle.gps_confidence_score = confidence
    return vehicle
