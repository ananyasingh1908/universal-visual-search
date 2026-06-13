import json
import urllib.request

req = urllib.request.Request(
    'http://127.0.0.1:8001/scan-website',
    data=json.dumps({'url': 'https://example.com'}).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
)
with urllib.request.urlopen(req, timeout=60) as resp:
    print(resp.status)
    print(resp.read().decode())
