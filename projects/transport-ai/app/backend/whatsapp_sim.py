"""SIMULATED WhatsApp channel (spec ט.1). No Meta/WhatsApp Business API
credentials or real delivery here — outbound messages are just logged to
driver_messages so the dashboard can show "what would have been sent".
Real integration needs an approved Meta Business template (see ט.1.1 in
the spec) and API credentials this environment doesn't have.
"""
from models import DriverMessage


def send_whatsapp(session, driver, body: str) -> DriverMessage:
    msg = DriverMessage(driver_id=driver.driver_id, direction="outbound", body=body)
    session.add(msg)
    session.flush()
    print(f"[whatsapp_sim] -> {driver.full_name} ({driver.whatsapp_number}): {body}")
    return msg
