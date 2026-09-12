import json, urllib.request
data = json.dumps({"email": "admin@codecoroner.dev", "password": "adminadmin"}).encode()
req = urllib.request.Request("http://nginx:80/api/v1/auth/login/", data=data, headers={"Content-Type": "application/json"}, method="POST")
try:
    resp = urllib.request.urlopen(req)
    print(resp.read().decode())
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'read'):
        print(e.read().decode())
