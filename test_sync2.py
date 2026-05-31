import requests

try:
    r = requests.post(
        'http://47.83.0.101:5004/matches/sync',
        json={'game': 'lol'},
        timeout=30
    )
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
