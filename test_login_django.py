import json, urllib.request
data = json.dumps({"email": "admin@codecoroner.dev", "password": "adminadmin"}).encode()
req = urllib.request.Request("http://localhost:8000/api/v1/auth/login/", data=data, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
print(resp.read().decode())
