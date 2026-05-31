import requests
import json

# 模拟数据
data = {
    "address": "0xTestAddress123456789",
    "chain": "ETH",
    "encrypted_data": "dGVzdGRhdGFlbmNyeXB0ZWQ="
}

print("发送数据:", json.dumps(data, indent=2))

try:
    r = requests.post(
        'https://api.ai656.top/api/wallet/backup',
        json=data,
        timeout=10,
        verify=False
    )
    print(f"\n状态码: {r.status_code}")
    print(f"响应: {r.text}")
except Exception as e:
    print(f"错误: {e}")
