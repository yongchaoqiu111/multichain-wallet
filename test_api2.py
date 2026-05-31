import requests
r = requests.post('http://localhost:5004/matches/list', json={'game': 'all'})
print(r.json())
