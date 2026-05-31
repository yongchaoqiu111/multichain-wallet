#!/usr/bin/env python3
"""
测试移动端专用接口完整流程：
1. 移动端AES-GCM加密
2. 服务器接收并解密
3. 服务器重新AES-GCM加密
4. 客服工具解密验证
"""
import json
import base64
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CLIENT_KEY = b'ClientWallet2026SecureKey32B!!!!'

# 原始钱包数据
original_wallet = {
    'address': '0xMobileTestAddress',
    'chain': 'ETH',
    'private_key': '0xMobilePrivateKey1234567890abcdef1234567890abcdef1234567890ab',
    'mnemonic': 'mobile test wallet backup phrase one two three four five six'
}

print("="*70)
print("步骤1：移动端AES-GCM加密（模拟Flutter Web）")
print("="*70)

# 移动端加密
json_bytes = json.dumps(original_wallet, ensure_ascii=False).encode('utf-8')
nonce = os.urandom(12)
aesgcm = AESGCM(CLIENT_KEY)
ciphertext = aesgcm.encrypt(nonce, json_bytes, None)
mobile_encrypted = base64.b64encode(nonce + ciphertext).decode('utf-8')

print(f"原始数据: {json.dumps(original_wallet, ensure_ascii=False)}")
print(f"加密后长度: {len(mobile_encrypted)}")
print(f"加密数据前80位: {mobile_encrypted[:80]}...")
print(f"✅ 移动端加密完成")

print("\n" + "="*70)
print("步骤2：服务器接收并解密（模拟server.py的/api/wallet/backup/mobile）")
print("="*70)

# 服务器接收到移动端数据
received_data = mobile_encrypted
print(f"📱 接收到移动端加密数据，长度: {len(received_data)}")

# 第1步：解密移动端数据
encrypted_bytes = base64.b64decode(received_data)
nonce = encrypted_bytes[:12]
ciphertext = encrypted_bytes[12:]
aesgcm = AESGCM(CLIENT_KEY)
decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
wallet_data = json.loads(decrypted_bytes.decode('utf-8'))

print(f"✅ 移动端数据解密成功: {wallet_data['address']}")
print(f"   私钥: {wallet_data['private_key'][:30]}...")
print(f"   助记词: {wallet_data['mnemonic'][:40]}...")

print("\n" + "="*70)
print("步骤3：服务器重新AES-GCM加密（确保格式统一）")
print("="*70)

# 第2步：重新用AES-GCM加密
json_bytes = json.dumps(wallet_data, ensure_ascii=False).encode('utf-8')
new_nonce = os.urandom(12)
new_ciphertext = aesgcm.encrypt(new_nonce, json_bytes, None)
final_encrypted = base64.b64encode(new_nonce + new_ciphertext).decode('utf-8')

print(f"✅ 重新加密完成")
print(f"   新长度: {len(final_encrypted)}")
print(f"   新数据前80位: {final_encrypted[:80]}...")

# 模拟存储到数据库
stored_data = final_encrypted
print(f"💾 数据存储到数据库")

print("\n" + "="*70)
print("步骤4：客服工具获取并解密（模拟decrypt_tool_gui.py）")
print("="*70)

# 客服工具从API获取数据
fetched_encrypted = stored_data
print(f"获取到加密数据长度: {len(fetched_encrypted)}")

# AES-GCM解密
encrypted_bytes = base64.b64decode(fetched_encrypted)
nonce = encrypted_bytes[:12]
ciphertext = encrypted_bytes[12:]
aesgcm = AESGCM(CLIENT_KEY)
decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
decrypted_wallet = json.loads(decrypted_bytes.decode('utf-8'))

print(f"✅ 解密成功！")
print(f"地址: {decrypted_wallet['address']}")
print(f"链: {decrypted_wallet['chain']}")
print(f"私钥: {decrypted_wallet['private_key']}")
print(f"助记词: {decrypted_wallet['mnemonic']}")

print("\n" + "="*70)
print("步骤5：验证数据完整性")
print("="*70)

assert decrypted_wallet['address'] == original_wallet['address'], "地址不匹配！"
assert decrypted_wallet['chain'] == original_wallet['chain'], "链不匹配！"
assert decrypted_wallet['private_key'] == original_wallet['private_key'], "私钥不匹配！"
assert decrypted_wallet['mnemonic'] == original_wallet['mnemonic'], "助记词不匹配！"

print("✅ 地址匹配: PASS")
print("✅ 链匹配: PASS")
print("✅ 私钥匹配: PASS")
print("✅ 助记词匹配: PASS")

print("\n" + "="*70)
print("✅✅✅ 移动端专用接口流程测试通过！")
print("流程：移动端加密 → 服务器解密重加密 → 存储 → 客服工具解密")
print("="*70)
