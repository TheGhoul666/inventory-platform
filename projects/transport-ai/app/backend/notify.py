"""Single entry point for driver messaging — enforces the spec's channel
hierarchy (ט.1, נספח קנוני): WhatsApp is primary; IVR is backup-only,
used only when WhatsApp isn't reachable for this driver.
"""
from ivr_sim import call_ivr
from whatsapp_sim import send_whatsapp


def notify_driver(session, driver, body: str):
    if driver.whatsapp_number:
        return send_whatsapp(session, driver, body)
    return call_ivr(session, driver, body)
