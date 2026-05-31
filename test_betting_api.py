import requests

r = requests.post(
    "http://localhost:5004/matches/list",
    json={"game": "lol", "status": "upcoming", "page": 1}
)
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")
