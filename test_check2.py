import requests, json
TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg1MjUyNzYzLCJpYXQiOjE3ODUxNjYzNjMsImp0aSI6ImEyMjNiYTFhNDAzOTQ1MmNiYTM2NjAzZmZmNDM1ZDc1IiwidXNlcl9pZCI6ImQxMzM2MTc3LTllMzUtNDNiOC1hNGIzLWE0ODk5YmU1Mjc4YSJ9.Dbcv2mxTFv9YLe_E03rZpHCeiTjCHWCbw1gKC-VQxSo'
H = {'Authorization': 'Bearer ' + TOKEN}
BASE = 'http://localhost:8000/api/v1'

# Direct to the DB - can't from API, so let's test bug_localization directly
# by hitting the ai-engine localize-bug endpoint
r = requests.post('http://localhost:8002/localize-bug', json={
    'repo_id': 'd64d3303-4bc4-48b8-b8e0-0097b446c276',
    'error_context': {'error_message': 'TypeError: expected string or bytes-like object'},
    'log_analysis': {'status': 'ok'},
    'chunks': [{'file_path': 'requests/models.py', 'content': 'def prepare_body(): pass', 'language': 'python', 'similarity': 0.9}]
})
print(r.status_code)
print(json.dumps(r.json(), indent=2))
