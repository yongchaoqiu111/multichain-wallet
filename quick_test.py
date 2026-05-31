import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    r = requests.post(
        'https://api.ai656.top/api/wallet/backup',
        json={
            'address': '0xTest',
            'chain': 'ETH',
            'encrypted_data': 'test'
        },
        timeout=10,
        verify=False
    )
    print(f'状态码: {r.status_code}')
    print(f'响应: {r.text[:500]}')
except Exception as e:
    print(f'错误: {e}')
