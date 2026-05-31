#!/usr/bin/env python3
import requests
import json

url = "http://127.0.0.1:5000/api/wallet/import/mnemonic"
data = {
    "mnemonic": "aisle define upon property force sentence country tonight wife autumn normal entry",
    "chain": "TRON"
}

response = requests.post(url, json=data)
print(f"状态码: {response.status_code}")
print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
