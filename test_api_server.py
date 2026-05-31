import requests
import json

try:
    r = requests.post(
        'http://localhost:5004/matches/list',
        json={'game': 'lol', 'status': 'upcoming', 'page': 1},
        timeout=5
    )
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text[:1000]}")
except Exception as e:
    print(f"Error: {e}")
