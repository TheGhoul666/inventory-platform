"""Seed demo data into Supabase via REST API."""
import urllib.request, json, ssl, uuid

URL = "https://wrspszdkmjdrhupvjblu.supabase.co"
KEY = "sb_secret_e2KaQgxwa7ODEN6ZUyNP-A_XF9C_Ejk"
ctx = ssl.create_default_context()

def req(method, table, body=None, params=""):
    full = f"{URL}/rest/v1/{table}" + (f"?{params}" if params else "")
    headers = {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(full, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, context=ctx, timeout=15) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else [], resp.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        print(f"  ERR {e.code}: {raw[:200].decode(errors='replace')}")
        return [], e.code

def uid(): return str(uuid.uuid4())

# ── 1. Warehouses ──────────────────────────────────────────────
print("=== Warehouses ===")
wh_id = uid()
_, s = req("POST", "warehouses", {
    "id": wh_id, "name": "Tel Aviv Central Bus Depot", "code": "TLV-01",
    "address": "Derech Petah Tikva 56", "city": "Tel Aviv", "country": "IL",
    "is_active": True, "is_deleted": False, "capacity_sqm": 5000,
})
print(f"  TLV-01: HTTP {s}")

wh2_id = uid()
_, s = req("POST", "warehouses", {
    "id": wh2_id, "name": "Haifa North Depot", "code": "HFA-01",
    "address": "HaNamal 12", "city": "Haifa", "country": "IL",
    "is_active": True, "is_deleted": False, "capacity_sqm": 3000,
})
print(f"  HFA-01: HTTP {s}")

if s not in (200, 201):
    print("  Warehouse insert failed — aborting")
    raise SystemExit(1)

# ── 2. Categories ──────────────────────────────────────────────
print()
print("=== Categories ===")
cat_engine = uid()
cat_tires = uid()
cat_electric = uid()
cat_body = uid()

for cat_id, name, desc in [
    (cat_engine, "Engine Parts", "Filters, belts, pumps and engine components"),
    (cat_tires, "Tires & Wheels", "Bus tires, rims and related hardware"),
    (cat_electric, "Electrical", "Batteries, alternators, wiring and electronics"),
    (cat_body, "Body & Chassis", "Doors, windows, panels and structural parts"),
]:
    _, s = req("POST", "inventory_categories", {
        "id": cat_id, "name": name, "description": desc, "is_deleted": False,
    })
    print(f"  {name}: HTTP {s}")

# ── 3. Inventory Items ─────────────────────────────────────────
print()
print("=== Inventory Items ===")

items_def = [
    # name, sku, qty, low, crit, unit, cat, supplier, cost
    ("Oil Filter - Volvo 7900",        "OIL-FLT-001", 3,  20, 5,  "pcs", cat_engine,   "VolvoPartsIL",   45.00),
    ("Air Filter - Mercedes Citaro",   "AIR-FLT-002", 8,  15, 3,  "pcs", cat_engine,   "Mercedes Parts", 38.00),
    ("Diesel Fuel Filter",             "FUEL-FLT-003", 2, 10, 2,  "pcs", cat_engine,   "Bosch IL",       28.00),
    ("Drive Belt - Alternator",        "BLT-ALT-004", 1,  8,  2,  "pcs", cat_engine,   "Gates Corp",     65.00),
    ("Michelin 295/80 R22.5",          "TIR-MCH-005", 4,  12, 2,  "pcs", cat_tires,    "Michelin IL",   980.00),
    ("Bridgestone R268 Bus Tire",      "TIR-BRG-006", 18, 10, 2,  "pcs", cat_tires,    "Bridgestone IL",850.00),
    ("Lead-Acid Battery 24V 150Ah",    "BAT-LA-007",  6,  8,  2,  "pcs", cat_electric, "Exide IL",      420.00),
    ("Alternator 28V 150A",            "ALT-28V-008", 2,  5,  1,  "pcs", cat_electric, "Bosch IL",      780.00),
    ("Windshield Wiper Blade 700mm",   "WPR-700-009", 12, 20, 5,  "pcs", cat_electric, "Valeo IL",       35.00),
    ("Bus Door Seal - Volvo",          "SEAL-DRV-010", 5, 10, 2,  "m",   cat_body,     "VolvoPartsIL",   22.00),
    ("Windshield Glass - Mercedes",    "GLS-MBZ-011", 1,  3,  1,  "pcs", cat_body,     "SafeGlass Ltd",2200.00),
    ("Brake Pad Set - Front Axle",     "BRK-PAD-012", 9,  15, 3,  "set", cat_engine,   "Brembo IL",     340.00),
    ("Coolant 50L",                    "COL-50L-013", 25, 30, 8,  "L",   cat_engine,   "Prestone IL",   180.00),
    ("Interior LED Panel 120cm",       "LED-INT-014", 7,  10, 2,  "pcs", cat_electric, "LightTech IL",   95.00),
    ("Hydraulic Oil 20L - Steering",   "HYD-OIL-015", 16, 12, 4,  "L",   cat_engine,   "Castrol IL",    140.00),
]

item_ids = []
for name, sku, qty, low, crit, unit, cat, supplier, cost in items_def:
    iid = uid()
    item_ids.append((iid, name, qty, low, crit))
    _, s = req("POST", "inventory_items", {
        "id": iid, "sku": sku, "name": name, "unit": unit,
        "quantity": qty, "reserved_quantity": 0,
        "low_stock_threshold": low, "critical_stock_threshold": crit,
        "reorder_quantity": low * 3,
        "warehouse_id": wh_id, "category_id": cat,
        "supplier_name": supplier, "lead_time_days": 7,
        "unit_cost": cost, "is_deleted": False,
    })
    tag = "CRIT" if qty <= crit else ("LOW " if qty <= low else "OK  ")
    print(f"  [{tag}] {name}: qty={qty}  HTTP {s}")

# ── 4. Alerts ──────────────────────────────────────────────────
print()
print("=== Alerts ===")

critical_items = [(i, n, q, l, c) for i, n, q, l, c in item_ids if q <= c]
low_items      = [(i, n, q, l, c) for i, n, q, l, c in item_ids if c < q <= l]

for iid, name, qty, low, crit in critical_items:
    _, s = req("POST", "alerts", {
        "id": uid(), "alert_type": "CRITICAL_STOCK", "severity": "CRITICAL",
        "status": "OPEN",
        "title": f"Critical stock: {name}",
        "message": f"Only {qty} units remaining (critical threshold: {crit}). Immediate reorder required.",
        "item_id": iid, "warehouse_id": wh_id, "is_deleted": False,
    })
    print(f"  CRITICAL {name}: HTTP {s}")

for iid, name, qty, low, crit in low_items[:4]:
    _, s = req("POST", "alerts", {
        "id": uid(), "alert_type": "LOW_STOCK", "severity": "WARNING",
        "status": "OPEN",
        "title": f"Low stock: {name}",
        "message": f"Stock at {qty} units (low threshold: {low}). Consider restocking soon.",
        "item_id": iid, "warehouse_id": wh_id, "is_deleted": False,
    })
    print(f"  WARNING  {name}: HTTP {s}")

print()
print(f"Done! 2 warehouses, 4 categories, {len(items_def)} items, "
      f"{len(critical_items)} critical + {min(len(low_items),4)} warning alerts")
