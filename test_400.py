import requests, json
TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg1MjUyNzYzLCJpYXQiOjE3ODUxNjYzNjMsImp0aSI6ImEyMjNiYTFhNDAzOTQ1MmNiYTM2NjAzZmZmNDM1ZDc1IiwidXNlcl9pZCI6ImQxMzM2MTc3LTllMzUtNDNiOC1hNGIzLWE0ODk5YmU1Mjc4YSJ9.Dbcv2mxTFv9YLe_E03rZpHCeiTjCHWCbw1gKC-VQxSo'
H = {'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json'}
BASE = 'http://localhost:8000/api/v1'

# reproduce what the frontend sends
payload = {
    'project': '7da42c4b-155f-471c-8011-df6314254f65',
    'repository': 'd64d3303-4bc4-48b8-b8e0-0097b446c276',
    'title': 'Test error',
    'error_context': {'error_message': 'Something broke'}
}
r = requests.post(f'{BASE}/analyses/', headers=H, json=payload)
print('status:', r.status_code)
print('body:', r.text)
