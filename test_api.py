import requests
res = requests.post('http://localhost:5001/api/wallet/create', json={'chain': 'TRON'})
print('Status:', res.status_code)
print('Response:', res.text)
