"""Execute SQL on Supabase via every available method."""
import urllib.request, json, ssl, urllib.parse

PROJECT = "wrspszdkmjdrhupvjblu"
URL = f"https://{PROJECT}.supabase.co"
SERVICE_KEY = "sb_secret_e2KaQgxwa7ODEN6ZUyNP-A_XF9C_Ejk"
ctx = ssl.create_default_context()

REALTIME_SQL = """
ALTER PUBLICATION supabase_realtime ADD TABLE public.inventory_items;
ALTER PUBLICATION supabase_realtime ADD TABLE public.alerts;
"""

def try_req(label, method, url, headers, body=None):
    data = body.encode() if body else None
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, context=ctx, timeout=15) as resp:
            raw = resp.read()
            result = raw[:200].decode(errors="replace")
            print(f"  {label}: HTTP {resp.status} -> {result}")
            return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read()
        print(f"  {label}: HTTP {e.code} -> {raw[:150].decode(errors='replace')}")
        return e.code, raw
    except Exception as e:
        print(f"  {label}: ERROR {e}")
        return 0, b""

print("=== Attempt 1: Management API /database/query ===")
try_req(
    "mgmt-api",
    "POST",
    f"https://api.supabase.com/v1/projects/{PROJECT}/database/query",
    {
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "supabase-py/2.0",
    },
    json.dumps({"query": REALTIME_SQL})
)

print()
print("=== Attempt 2: PostgREST realtime schema ===")
# Try accessing realtime schema tables
for schema in ["realtime", "_realtime", "supabase_realtime"]:
    try_req(
        f"schema:{schema}",
        "GET",
        f"{URL}/rest/v1/subscription?limit=1",
        {
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Accept-Profile": schema,
            "Content-Profile": schema,
        }
    )

print()
print("=== Attempt 3: pg_net / execute function ===")
for fn in ["exec_sql", "execute_sql", "run_sql", "pg_execute"]:
    try_req(
        f"rpc/{fn}",
        "POST",
        f"{URL}/rest/v1/rpc/{fn}",
        {
            "apikey": SERVICE_KEY,
            "Authorization": f"Bearer {SERVICE_KEY}",
            "Content-Type": "application/json",
        },
        json.dumps({"sql": REALTIME_SQL})
    )

print()
print("=== Attempt 4: Supabase pg endpoint ===")
try_req(
    "pg-query",
    "POST",
    f"{URL}/pg/query",
    {
        "apikey": SERVICE_KEY,
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    },
    json.dumps({"query": REALTIME_SQL})
)

print()
print("=== Attempt 5: Edge function exec (if deployed) ===")
try_req(
    "edge-exec",
    "POST",
    f"{URL}/functions/v1/exec-sql",
    {
        "Authorization": f"Bearer {SERVICE_KEY}",
        "Content-Type": "application/json",
    },
    json.dumps({"sql": REALTIME_SQL})
)
