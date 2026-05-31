import requests

try:
    r = requests.post(
        'http://47.83.0.101:5004/matches/list',
        json={'game': 'lol', 'status': 'upcoming', 'page': 1},
        timeout=5
    )
    print(f"Status Code: {r.status_code}")
    print(f"Response: {r.text[:500]}")
except Exception as e:
    print(f"Error: {e}")
