"""
One-time Supabase setup:
  1. Create SuperAdmin user
  2. Enable Realtime for inventory_items + alerts
  3. Get project connection string
"""
import urllib.request, json, ssl, sys

url = "https://wrspszdkmjdrhupvjblu.supabase.co"
service_key = "sb_secret_e2KaQgxwa7ODEN6ZUyNP-A_XF9C_Ejk"
ctx = ssl.create_default_context()

def apireq(method, path, body=None, params="", base=None):
    base_url = base or url
    full = (f"{base_url}{path}?{params}" if params else f"{base_url}{path}")
    headers = {
        "apikey": service_key,
        "Authorization": "Bearer " + service_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(full, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, context=ctx, timeout=15) as resp:
            raw = resp.read()
            return (json.loads(raw) if raw else {}), resp.status
    except urllib.error.HTTPError as e:
        raw = e.read()
        return (json.loads(raw) if raw else {}), e.code

# ── 1. Create SuperAdmin user ──────────────────────────────────
print("=== Creating SuperAdmin User ===")
admin_email = "admin@busops.com"
admin_password = "BusOps2026!Admin"

data, status = apireq("POST", "/auth/v1/admin/users", body={
    "email": admin_email,
    "password": admin_password,
    "email_confirm": True,
    "user_metadata": {
        "full_name": "System Administrator",
    },
    "app_metadata": {
        "roles": ["SuperAdmin"],
        "permissions": ["*"],
        "is_superadmin": True,
    }
})

if status in (200, 201):
    uid = data.get("id", "?")
    print(f"  Created: {admin_email} (id={uid})")
    print(f"  Password: {admin_password}")
elif status == 422 and "already" in str(data).lower():
    print(f"  Already exists: {admin_email}")
else:
    print(f"  HTTP {status}: {data}")

# ── 2. List all users ─────────────────────────────────────────
print()
print("=== All Auth Users ===")
data, status = apireq("GET", "/auth/v1/admin/users")
users = data.get("users", [])
for u in users:
    email = u.get("email", "?")
    meta = u.get("app_metadata", {})
    roles = meta.get("roles", [])
    confirmed = u.get("email_confirmed_at") is not None
    print(f"  - {email} | roles={roles} | confirmed={confirmed}")

# ── 3. Enable Realtime via Management API ─────────────────────
print()
print("=== Enabling Realtime ===")
# Try management API
for table in ["inventory_items", "alerts"]:
    data, status = apireq(
        "POST",
        f"/v1/projects/wrspszdkmjdrhupvjblu/database/publications/supabase_realtime/tables",
        body={"name": table},
        base="https://api.supabase.com"
    )
    print(f"  {table}: HTTP {status} {str(data)[:80]}")

# ── 4. Get connection string ──────────────────────────────────
print()
print("=== Connection Strings ===")
data, status = apireq("GET", "/v1/projects/wrspszdkmjdrhupvjblu/database/connection",
                       base="https://api.supabase.com")
print(f"  HTTP {status}: {str(data)[:300]}")

print()
print("Setup complete.")
