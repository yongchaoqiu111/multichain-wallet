#!/usr/bin/env python3
import requests
import json

BASE = "https://api.ai656.top/api"

r = requests.get(f"{BASE}/health", timeout=15, verify=False)
print("health", r.status_code, r.text)

r = requests.post(f"{BASE}/wallet/create", json={"chain": "TRON"}, timeout=30, verify=False)
print("create", r.status_code, r.text[:300])
if r.status_code == 200:
    d = r.json()
    print("has private_key:", bool(d.get("private_key")))
