"""
双重加密测试脚本
验证：客户端加密 → 服务器加密 → 存储 → 服务器解密 → 客户端解密
"""
import sys
sys.path.insert(0, 'f:\\qianbao')

from modules.wallet_backup_client import WalletBackupClient
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# 服务器密钥（与server.py一致）
SERVER_ENCRYPTION_KEY = b'ServerWallet2026SecureKey32B!!!!'

def server_encrypt(client_encrypted_data: str) -> str:
    """模拟服务器二次加密"""
    nonce = os.urandom(12)
    aesgcm = AESGCM(SERVER_ENCRYPTION_KEY)
    ciphertext = aesgcm.encrypt(nonce, client_encrypted_data.encode('utf-8'), None)
    encrypted_data = nonce + ciphertext
    return base64.b64encode(encrypted_data).decode('utf-8')

def server_decrypt(server_encrypted_data: str) -> str:
    """模拟服务器解密"""
    encrypted_data = base64.b64decode(server_encrypted_data)
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    aesgcm = AESGCM(SERVER_ENCRYPTION_KEY)
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted_bytes.decode('utf-8')

print("="*60)
print(" 双重加密完整流程测试")
print("="*60)

# 原始钱包数据
original_wallet = {
    'private_key': '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
    'mnemonic': 'word1 word2 word3 word4 word5 word6 word7 word8 word9 word10 word11 word12',
    'address': '0x1E6a9D41c5bF8e9e5e5e5e5e5e5e5e5e5e5e5e5e'
}

print("\n【步骤1】原始钱包数据")
print(f"  私钥: {original_wallet['private_key'][:20]}...")
print(f"  助记词: {original_wallet['mnemonic'][:30]}...")

# 第1层加密：客户端加密
print("\n【步骤2】客户端加密（第1层）")
client_encrypted = WalletBackupClient.encrypt_wallet_data(original_wallet)
print(f"  加密后长度: {len(client_encrypted)} 字符")
print(f"  前50位: {client_encrypted[:50]}...")

# 第2层加密：服务器加密
print("\n【步骤3】服务器加密（第2层）")
double_encrypted = server_encrypt(client_encrypted)
print(f"  双重加密后长度: {len(double_encrypted)} 字符")
print(f"  前50位: {double_encrypted[:50]}...")

# 模拟从数据库取出
print("\n【步骤4】从数据库取出双重加密数据")
print(f"  数据长度: {len(double_encrypted)} 字符")

# 第1次解密：服务器解密
print("\n【步骤5】服务器解密（去掉第2层）")
after_server_decrypt = server_decrypt(double_encrypted)
print(f"  解密后长度: {len(after_server_decrypt)} 字符")
print(f"  与客户端加密结果匹配: {after_server_decrypt == client_encrypted}")

# 第2次解密：客户端解密
print("\n【步骤6】客户端解密（去掉第1层）")
final_decrypted = WalletBackupClient.decrypt_wallet_data(after_server_decrypt)
print(f"  私钥匹配: {final_decrypted['private_key'] == original_wallet['private_key']}")
print(f"  助记词匹配: {final_decrypted['mnemonic'] == original_wallet['mnemonic']}")
print(f"  地址匹配: {final_decrypted['address'] == original_wallet['address']}")

print("\n" + "="*60)
if (final_decrypted['private_key'] == original_wallet['private_key'] and
    final_decrypted['mnemonic'] == original_wallet['mnemonic'] and
    final_decrypted['address'] == original_wallet['address']):
    print(" ✅ 双重加密测试通过！")
else:
    print(" ❌ 双重加密测试失败！")
print("="*60)
