import urllib.request, json, ssl, sys

url = "https://wrspszdkmjdrhupvjblu.supabase.co"
service_key = "sb_secret_e2KaQgxwa7ODEN6ZUyNP-A_XF9C_Ejk"
ctx = ssl.create_default_context()

def apireq(method, path, body=None, params=""):
    full = (f"{url}{path}?{params}" if params else f"{url}{path}")
    headers = {
        "apikey": service_key,
        "Authorization": "Bearer " + service_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(full, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, context=ctx, timeout=10) as resp:
            raw = resp.read()
            return (json.loads(raw) if raw else {}), resp.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        return (json.loads(raw) if raw else {}), e.code

# ── 1. Table access ──────────────────────────────────────────
tables = [
    "warehouses", "inventory_items", "inventory_transactions", "alerts",
    "buses", "warehouse_locations", "inventory_categories", "maintenance_events",
    "inventory_snapshots", "webhook_endpoints", "webhook_deliveries", "audit_logs",
]
print("=== Table Access (service_role) ===")
for t in tables:
    data, status = apireq("GET", "/rest/v1/" + t, params="limit=1")
    icon = "OK" if status == 200 else "ERR"
    print(f"  {icon}  {t}: HTTP {status}")

# ── 2. Auth users ─────────────────────────────────────────────
print()
print("=== Auth Users ===")
data, status = apireq("GET", "/auth/v1/admin/users")
users = data.get("users", [])
print(f"  Total users: {len(users)}")
for u in users:
    email = u.get("email", "?")
    confirmed = u.get("email_confirmed_at") is not None
    meta = u.get("app_metadata", {})
    roles = meta.get("roles", [])
    print(f"  - {email} | confirmed={confirmed} | roles={roles}")

# ── 3. Realtime publication check ─────────────────────────────
print()
print("=== Realtime (checking via REST) ===")
# Check if inventory_items & alerts are replication-enabled by querying
for table in ["inventory_items", "alerts"]:
    _, status = apireq("GET", "/rest/v1/" + table, params="limit=0")
    print(f"  {table}: accessible={status == 200}")

print()
print("Done.")
