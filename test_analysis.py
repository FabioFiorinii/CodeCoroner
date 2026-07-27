"""Test analysis creation and polling."""
import requests, sys, time, json

BASE = "http://localhost:8000/api/v1"
TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg1MjUyNzYzLCJpYXQiOjE3ODUxNjYzNjMsImp0aSI6ImEyMjNiYTFhNDAzOTQ1MmNiYTM2NjAzZmZmNDM1ZDc1IiwidXNlcl9pZCI6ImQxMzM2MTc3LTllMzUtNDNiOC1hNGIzLWE0ODk5YmU1Mjc4YSJ9.Dbcv2mxTFv9YLe_E03rZpHCeiTjCHWCbw1gKC-VQxSo"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def req(method, path, **kw):
    kw.setdefault("headers", HEADERS)
    kw.setdefault("timeout", 30)
    r = requests.request(method, f"{BASE}{path}", **kw)
    try: data = r.json()
    except: data = r.text
    print(f">>> {method} {path} -> {r.status_code}")
    return r.status_code, data

# Check repos
print("Existing repos:")
status, repos = req("GET", "/repositories/")
for r in repos.get("results", []):
    print(f"  {r['id']}: {r['git_url']} status={r['status']}")

# Pick the indexed repo
repo_id = None
for r in repos.get("results", []):
    if r["status"] in ("ready", "indexed"):
        repo_id = r["id"]
        project_id = r["project"]
        break

if not repo_id:
    print("No ready repo found")
    sys.exit(1)

print(f"\nUsing repo: {repo_id}  project: {project_id}")

# Create analysis
print("\nCreating analysis...")
status, analysis = req("POST", "/analyses/", json={
    "project": project_id,
    "repository": repo_id,
    "title": "TypeError in requests library",
    "error_context": {
        "error_message": "TypeError: expected string or bytes-like object",
        "stacktrace": "File 'requests/models.py', line 456, in prepare_body",
        "description": "Happens when passing an integer as the data parameter in a POST request",
    }
})

analysis_id = analysis.get("id")
if not analysis_id:
    print(f"FAILED to create analysis: {json.dumps(analysis, indent=2)}")
    sys.exit(1)

print(f"Analysis: {analysis_id}")

# Poll
print("\nPolling...")
for i in range(60):
    status, a = req("GET", f"/analyses/{analysis_id}/")
    s = a.get("status", "?")
    bl = a.get("bug_localization") is not None
    rc = a.get("root_cause") is not None
    rp = a.get("report") is not None
    print(f"  [{i+1}/60] status={s}  bl={bl}  rca={rc}  report={rp}")
    if s in ("completed", "failed"):
        break
    time.sleep(5)

print("\n=== FINAL RESULT ===")
print(json.dumps(a, indent=2, default=str))
