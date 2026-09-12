import requests, json

TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg1MjUyNzYzLCJpYXQiOjE3ODUxNjYzNjMsImp0aSI6ImEyMjNiYTFhNDAzOTQ1MmNiYTM2NjAzZmZmNDM1ZDc1IiwidXNlcl9pZCI6ImQxMzM2MTc3LTllMzUtNDNiOC1hNGIzLWE0ODk5YmU1Mjc4YSJ9.Dbcv2mxTFv9YLe_E03rZpHCeiTjCHWCbw1gKC-VQxSo'
H = {'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'}
BASE = 'http://localhost:8000/api/v1'

# Check analysis runs
a = requests.get(f'{BASE}/analyses/b35aebdf-37ff-478e-9220-cb86c1d59892/', headers=H).json()
for r in a.get('runs', []):
    print(f"{r['step']}: status={r['status']} error={r.get('error','')}")
