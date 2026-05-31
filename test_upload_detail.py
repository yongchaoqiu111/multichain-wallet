"""
测试上传API - 显示发送的完整数据
"""
import requests
import urllib3
import json
from modules.wallet_backup_client import WalletBackupClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 模拟钱包数据
test_wallet = {
    'private_key': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
    'mnemonic': 'word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12',
    'address': '0xTestAddress123456789'
}

address = test_wallet['address']
chain = 'ETH'

print("="*60)
print("准备发送的数据:")
print("="*60)
print(f"地址: {address}")
print(f"链: {chain}")
print(f"私钥: {test_wallet['private_key']}")
print(f"助记词: {test_wallet['mnemonic']}")

# 客户端加密
print("\n" + "="*60)
print("客户端加密后的数据:")
print("="*60)
encrypted_data = WalletBackupClient.encrypt_wallet_data(test_wallet)
print(f"加密数据长度: {len(encrypted_data)}")
print(f"加密数据前100字符: {encrypted_data[:100]}...")

# 构建请求体
request_body = {
    'address': address,
    'chain': chain,
    'encrypted_data': encrypted_data
}

print("\n" + "="*60)
print("发送到服务器的JSON:")
print("="*60)
print(json.dumps(request_body, indent=2))

# 发送请求
print("\n" + "="*60)
print("发送请求到: https://api.ai656.top/api/wallet/backup")
print("="*60)

try:
    response = requests.post(
        'https://api.ai656.top/api/wallet/backup',
        json=request_body,
        timeout=10,
        verify=False
    )
    
    print(f"\n响应状态码: {response.status_code}")
    print(f"响应内容:")
    print(response.text)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print(f"\n✅ 上传成功!")
            print(f"备份ID: {result.get('backup_id')}")
            print(f"备份时间: {result.get('backup_time')}")
            print(f"\n请在数据库中查找 backup_id = '{result.get('backup_id')}' 的记录")
        else:
            print(f"\n❌ 上传失败: {result.get('message')}")
    else:
        print(f"\n❌ HTTP错误: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ 请求异常: {str(e)}")
    import traceback
    traceback.print_exc()
