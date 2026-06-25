"""
Seed script: inserts 6 inventory items and 3 buses using existing warehouses.
Run: python seed_data.py
"""
import urllib.request
import urllib.error
import urllib.parse
import json
import uuid

SUPABASE_URL = "https://wrspszdkmjdrhupvjblu.supabase.co"
SERVICE_KEY = "sb_secret_e2KaQgxwa7ODEN6ZUyNP-A_XF9C_Ejk"

HEADERS = {
    "apikey": SERVICE_KEY,
    "Authorization": "Bearer " + SERVICE_KEY,
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


def api_request(method, path, body=None):
    url = SUPABASE_URL + "/rest/v1/" + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=HEADERS, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else []
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print("  ERROR " + str(e.code) + ": " + err)
        return None


def get_all(table, select="*"):
    return api_request("GET", table + "?select=" + select) or []


def insert_row(table, row):
    result = api_request("POST", table, row)
    if result and isinstance(result, list):
        return result[0]
    return result


print("=== Seeding sample data ===")

# --- 1. Get existing warehouses ---
print("\nChecking existing warehouses...")
warehouses = get_all("warehouses", "id,name,code,is_active")
active_wh = [w for w in warehouses if w.get("is_active", True)]
print("  Found " + str(len(warehouses)) + " warehouses (" + str(len(active_wh)) + " active):")
for w in warehouses:
    print("    [" + w["code"] + "] " + w["name"] + " -> " + w["id"])

if len(warehouses) < 2:
    print("  Not enough warehouses. Please create at least 2 first.")
    exit(1)

wh_a = warehouses[0]["id"]
wh_b = warehouses[1]["id"]
print("\n  Using warehouses:")
print("  WH_A: " + warehouses[0]["name"])
print("  WH_B: " + warehouses[1]["name"])

# --- 2. Inventory Items ---
print("\nChecking existing inventory items...")
existing_items = get_all("inventory_items", "sku")
existing_skus = {i["sku"] for i in existing_items}
print("  Found " + str(len(existing_items)) + " existing items.")

sample_items = [
    {
        "id": str(uuid.uuid4()),
        "sku": "ENG-OIL-5W40",
        "name": "Engine Oil 5W-40 (1L)",
        "unit": "bottle",
        "quantity": "120",
        "reserved_quantity": "0",
        "low_stock_threshold": "20",
        "critical_stock_threshold": "5",
        "reorder_quantity": "50",
        "warehouse_id": wh_a,
        "supplier_name": "Castrol",
        "unit_cost": "18.50",
    },
    {
        "id": str(uuid.uuid4()),
        "sku": "BRK-PAD-FRNT",
        "name": "Front Brake Pads (Set)",
        "unit": "set",
        "quantity": "35",
        "reserved_quantity": "2",
        "low_stock_threshold": "10",
        "critical_stock_threshold": "3",
        "reorder_quantity": "20",
        "warehouse_id": wh_a,
        "supplier_name": "Bosch",
        "unit_cost": "145.00",
    },
    {
        "id": str(uuid.uuid4()),
        "sku": "AIR-FILT-STD",
        "name": "Air Filter Standard",
        "unit": "piece",
        "quantity": "60",
        "reserved_quantity": "0",
        "low_stock_threshold": "15",
        "critical_stock_threshold": "5",
        "reorder_quantity": "30",
        "warehouse_id": wh_a,
        "supplier_name": "Mann Filter",
        "unit_cost": "32.00",
    },
    {
        "id": str(uuid.uuid4()),
        "sku": "COOLANT-5L",
        "name": "Coolant / Antifreeze 5L",
        "unit": "can",
        "quantity": "8",
        "reserved_quantity": "0",
        "low_stock_threshold": "10",
        "critical_stock_threshold": "3",
        "reorder_quantity": "20",
        "warehouse_id": wh_b,
        "supplier_name": "Shell",
        "unit_cost": "55.00",
    },
    {
        "id": str(uuid.uuid4()),
        "sku": "WIPER-BLADE-26",
        "name": "Wiper Blade 26 inch",
        "unit": "piece",
        "quantity": "24",
        "reserved_quantity": "0",
        "low_stock_threshold": "8",
        "critical_stock_threshold": "2",
        "reorder_quantity": "16",
        "warehouse_id": wh_b,
        "supplier_name": "Bosch",
        "unit_cost": "22.00",
    },
    {
        "id": str(uuid.uuid4()),
        "sku": "TRANS-FLUID-ATF",
        "name": "Transmission Fluid ATF (1L)",
        "unit": "bottle",
        "quantity": "45",
        "reserved_quantity": "0",
        "low_stock_threshold": "10",
        "critical_stock_threshold": "3",
        "reorder_quantity": "25",
        "warehouse_id": wh_b,
        "supplier_name": "Valvoline",
        "unit_cost": "28.00",
    },
]

for item in sample_items:
    if item["sku"] in existing_skus:
        print("  Item " + item["sku"] + " already exists, skipping.")
    else:
        row = insert_row("inventory_items", item)
        if row:
            print("  Created: " + item["name"] + " (" + item["sku"] + ") qty=" + item["quantity"])
        else:
            print("  FAILED to create item " + item["sku"])

# --- 3. Buses ---
print("\nChecking existing buses...")
existing_buses = get_all("buses", "fleet_number")
existing_fleet = {b["fleet_number"] for b in existing_buses}
print("  Found " + str(len(existing_buses)) + " existing buses.")

sample_buses = [
    {
        "id": str(uuid.uuid4()),
        "fleet_number": "BUS-001",
        "license_plate": "12-345-67",
        "make": "Mercedes-Benz",
        "model": "Citaro G",
        "year": 2019,
        "status": "ACTIVE",
        "depot_id": wh_a,
        "mileage_km": 185000,
    },
    {
        "id": str(uuid.uuid4()),
        "fleet_number": "BUS-002",
        "license_plate": "23-456-78",
        "make": "Volvo",
        "model": "7900",
        "year": 2021,
        "status": "ACTIVE",
        "depot_id": wh_a,
        "mileage_km": 92000,
    },
    {
        "id": str(uuid.uuid4()),
        "fleet_number": "BUS-003",
        "license_plate": "34-567-89",
        "make": "MAN",
        "model": "Lion City",
        "year": 2018,
        "status": "IN_MAINTENANCE",
        "depot_id": wh_b,
        "mileage_km": 240000,
    },
]

for bus in sample_buses:
    if bus["fleet_number"] in existing_fleet:
        print("  Bus " + bus["fleet_number"] + " already exists, skipping.")
    else:
        row = insert_row("buses", bus)
        if row:
            print("  Created: " + bus["fleet_number"] + " - " + bus["make"] + " " + bus["model"])
        else:
            print("  FAILED to create bus " + bus["fleet_number"])

print("\n=== Seeding complete ===")
