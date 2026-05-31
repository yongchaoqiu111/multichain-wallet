import requests
import json

url = "http://api.ai656.top/betting/exchange/to_trx"
data = {
    "address": "TVAxmL3ofYT1WFN8PAq2LgV6yJxtxfb6o6",
    "points_amount": 0
}

response = requests.post(url, json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
