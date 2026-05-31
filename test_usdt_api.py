import requests

url = "http://47.83.0.101:5000/api/wallet/balance"
data = {
    "address": "TSfXD9bidCC2fojPUhXNvtJger5yUEnqb7",
    "chain": "TRON",
    "token": "USDT"
}

resp = requests.post(url, json=data)
print(f"状态码: {resp.status_code}")
print(f"响应: {resp.json()}")
