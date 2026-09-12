"""End-to-end test: create project → add repo → create analysis → poll results."""
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
    if r.status_code >= 400: print(f"    ERROR: {data}")
    return data

# 1. Create project
print("=" * 60)
print("STEP 1: Create project")
proj = req("POST", "/projects/", json={"name": "E2E Test Project", "description": "Auto test"})
project_id = proj.get("id")
if not project_id:
    print(f"FAILED. Response: {proj}")
    sys.exit(1)
print(f"Project: {project_id}")

# 2. Create repository (NOT nested — /api/v1/repositories/)
print("=" * 60)
print("STEP 2: Create repository")
repo = req("POST", "/repositories/", json={
    "project": project_id,
    "git_url": "https://github.com/psf/requests.git",
    "git_branch": "main",
})
repo_id = repo.get("id")
if not repo_id:
    print(f"FAILED. Response: {repo}")
    sys.exit(1)
print(f"Repo: {repo_id}")

# 3. Wait for repo to finish cloning/indexing
print("=" * 60)
print("STEP 3: Wait for repo indexing")
for i in range(30):
    r = req("GET", f"/repositories/{repo_id}/")
    status = r.get("status", "unknown")
    print(f"  [{i+1}/30] status={status}")
    if status == "ready":
        print("Repo is ready!")
        break
    time.sleep(10)
else:
    print("Repo not ready after 5 min, continuing anyway...")

# 4. Create analysis
print("=" * 60)
print("STEP 4: Create analysis")
analysis = req("POST", "/analyses/", json={
    "project": project_id,
    "repository": repo_id,
    "title": "TypeError in requests library",
    "error_context": {
        "error_message": "TypeError: expected string or bytes-like object",
        "stacktrace": "File 'requests/models.py', line 456, in prepare_body\n    raise TypeError('expected string or bytes-like object')",
        "description": "Happens when passing an integer as the data parameter in a POST request",
    }
})
analysis_id = analysis.get("id")
if not analysis_id:
    print(f"Response: {analysis}")
    sys.exit(1)
print(f"Analysis: {analysis_id}")

# 5. Poll analysis status
print("=" * 60)
print("STEP 5: Poll analysis")
for i in range(60):
    a = req("GET", f"/analyses/{analysis_id}/")
    status = a.get("status", "unknown")
    has_bl = a.get("bug_localization") is not None
    has_rc = a.get("root_cause") is not None
    has_rp = a.get("report") is not None
    print(f"  [{i+1}/60] status={status} bl={has_bl} rca={has_rc} report={has_rp}")
    if status == "completed" or status == "failed":
        break
    time.sleep(5)

# 6. Print results
print("=" * 60)
print("STEP 6: Results")
if isinstance(a, dict):
    print(json.dumps(a, indent=2, default=str))
else:
    print(a)
