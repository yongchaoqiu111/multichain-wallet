import requests
import json

r = requests.post('http://localhost:5004/matches/list', json={'game': 'all', 'page': 1})
result = r.json()
print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
