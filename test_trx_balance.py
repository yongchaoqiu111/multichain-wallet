import requests
import json

url = "http://127.0.0.1:5000/api/wallet/balance"
data = {
    "chain": "TRON",
    "address": "TJf2V4YKvPbHjJLzXkQXQJp7XqQqQmQvJX"
}

res = requests.post(url, json=data)
print(f"状态码: {res.status_code}")
print(f"响应: {json.dumps(res.json(), ensure_ascii=False, indent=2)}")
