#!/usr/bin/env python3
import requests
import json

payload = {
    "address": "TMobileTest99",
    "chain": "TRON",
    "encrypted_data": json.dumps({
        "private_key": "testpk",
        "mnemonic": "",
        "address": "TMobileTest99",
    }),
}

for url in [
    "http://127.0.0.1:5002/api/wallet/backup",
    "https://api.ai656.top/api/wallet/backup",
]:
    try:
        r = requests.post(url, json=payload, timeout=15, verify=False)
        print(url, r.status_code, r.text[:200])
    except Exception as e:
        print(url, "ERR", e)

r = requests.post(
    "https://api.ai656.top/api/wallet/list",
    json={},
    timeout=15,
    verify=False,
)
print("list", r.status_code, r.text[:150])
