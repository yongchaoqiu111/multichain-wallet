#!/usr/bin/env python3
import requests

url = "http://127.0.0.1:5000/api/wallet/balance"
data = {
    "address": "TSfXD9bidCC2fojPUhXNvtJger5yUEnqb7",
    "chain": "TRON",
    "token": "USDT"
}

r = requests.post(url, json=data)
print(f"状态码: {r.status_code}")
print(f"响应: {r.json()}")
