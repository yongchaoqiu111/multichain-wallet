"""
测试钱包备份上传API接口
"""
import requests
import json
from modules.wallet_backup_client import WalletBackupClient

def test_upload_api():
    """测试上传API接口"""
    print("="*60)
    print(" 测试钱包备份上传API")
    print("="*60)
    
    # 模拟钱包数据
    test_wallet = {
        'private_key': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
        'mnemonic': 'word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12',
        'address': '0x1E6a9D41c5bF8e9e5e5e5e5e5e5e5e5e5e5e5e5e'
    }
    
    address = test_wallet['address']
    chain = 'ETH'
    
    print(f"\n1. 准备测试数据:")
    print(f"   地址: {address}")
    print(f"   链: {chain}")
    print(f"   私钥: {test_wallet['private_key'][:20]}...")
    
    # 客户端加密
    print(f"\n2. 客户端加密...")
    encrypted_data = WalletBackupClient.encrypt_wallet_data(test_wallet)
    print(f"   加密后长度: {len(encrypted_data)} 字符")
    print(f"   加密数据前50位: {encrypted_data[:50]}...")
    
    # 上传到服务器
    print(f"\n3. 上传到服务器...")
    server_url = WalletBackupClient.SERVER_URL
    
    try:
        response = requests.post(
            f"{server_url}/api/wallet/backup",
            json={
                'address': address,
                'chain': chain,
                'encrypted_data': encrypted_data
            },
            timeout=10
        )
        
        print(f"   响应状态码: {response.status_code}")
        print(f"   响应内容: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"\n✅ 上传成功!")
                print(f"   备份ID: {result.get('backup_id')}")
                print(f"   备份时间: {result.get('backup_time')}")
                return True
            else:
                print(f"\n❌ 上传失败: {result.get('message')}")
                return False
        else:
            print(f"\n❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ 请求异常: {str(e)}")
        return False


def test_health_check():
    """测试健康检查接口"""
    print("\n" + "="*60)
    print(" 测试健康检查接口")
    print("="*60)
    
    server_url = WalletBackupClient.SERVER_URL
    
    try:
        response = requests.get(f"{server_url}/api/health", timeout=5)
        print(f"   响应状态码: {response.status_code}")
        print(f"   响应内容: {response.text}")
        
        if response.status_code == 200:
            print(f"\n✅ 服务正常运行")
            return True
        else:
            print(f"\n❌ 服务异常")
            return False
            
    except Exception as e:
        print(f"\n❌ 连接失败: {str(e)}")
        return False


if __name__ == '__main__':
    # 先测试健康检查
    health_ok = test_health_check()
    
    if health_ok:
        # 再测试上传
        upload_ok = test_upload_api()
        
        if upload_ok:
            print("\n" + "="*60)
            print(" ✅ 所有测试通过!")
            print("="*60)
        else:
            print("\n" + "="*60)
            print(" ❌ 上传测试失败")
            print("="*60)
    else:
        print("\n" + "="*60)
        print(" ❌ 服务不可用，请先启动服务器")
        print("="*60)
