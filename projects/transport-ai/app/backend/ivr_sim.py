"""SIMULATED IVR backup channel (spec ט.2) — DTMF only, no speech
recognition, and per the spec's channel hierarchy (ט.1, נספח קנוני) used
only when WhatsApp isn't reachable for a driver. No real telephony here —
this logs the call and a synthetic keypress reply. See notify.py for the
WhatsApp-first / IVR-fallback routing.
"""
import random

from models import DriverMessage


def call_ivr(session, driver, body: str) -> DriverMessage:
    msg = DriverMessage(driver_id=driver.driver_id, direction="outbound", body=body, channel="ivr_sim")
    session.add(msg)
    session.flush()
    print(f"[ivr_sim] calling {driver.full_name}: {body}")

    # simulated driver keypress, logged as its own inbound message
    pressed = random.choice(["1", "9"])  # 1 = confirm, 9 = decline — typical DTMF menu
    reply = DriverMessage(driver_id=driver.driver_id, direction="inbound", body=f"DTMF:{pressed}", channel="ivr_sim")
    session.add(reply)
    session.flush()
    return msg
