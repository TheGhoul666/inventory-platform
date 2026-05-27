"""Try to enable Realtime and find the DB connection string."""
import urllib.request, json, ssl

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
        "Prefer": "return=representation",
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

# List available RPC functions
print("=== Available RPC functions ===")
data, status = apireq("GET", "/rest/v1/")
swagger = data
paths = swagger.get("paths", {})
rpc_paths = [p for p in paths if p.startswith("/rpc/")]
print(f"  {rpc_paths}")

# Try rls_auto_enable
print()
print("=== Trying rls_auto_enable RPC ===")
data, status = apireq("POST", "/rest/v1/rpc/rls_auto_enable", body={})
print(f"  HTTP {status}: {str(data)[:200]}")

# Try to INSERT a test warehouse to verify write access
print()
print("=== Test write access ===")
import uuid
test_id = str(uuid.uuid4())
data, status = apireq("POST", "/rest/v1/warehouses", body={
    "id": test_id,
    "name": "Test Depot HQ",
    "code": "TEST-01",
    "country": "IL",
    "is_active": True,
    "is_deleted": False,
})
print(f"  Insert warehouse: HTTP {status} {str(data)[:150]}")

if status in (200, 201):
    # Delete it
    data2, status2 = apireq("DELETE", "/rest/v1/warehouses", params=f"id=eq.{test_id}")
    print(f"  Cleanup: HTTP {status2}")
