#!/usr/bin/env python3
"""
完整测试加密→解密→显示流程
"""
import json
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CLIENT_KEY = b'ClientWallet2026SecureKey32B!!!!'

# 模拟服务器返回的数据（从数据库查出来的）
test_data = {
    'id': 999,
    'address': '0xTestAddress001',
    'chain': 'BSC',
    'encrypted_data': '加密后的Base64数据',
    'backup_time': '2026-05-28 01:55:16'
}

# 测试数据
original_wallet = {
    'address': '0xTestAddress001',
    'chain': 'BSC',
    'private_key': '0xPrivateKey001abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
    'mnemonic': 'test zero one two three four five six seven eight nine ten'
}

print("="*60)
print("步骤1：客户端加密（模拟wallet_backup_client.py）")
print("="*60)

# 加密
json_bytes = json.dumps(original_wallet, ensure_ascii=False).encode('utf-8')
nonce = b'\x00' * 12  # 固定nonce便于测试
aesgcm = AESGCM(CLIENT_KEY)
ciphertext = aesgcm.encrypt(nonce, json_bytes, None)
encrypted_data = base64.b64encode(nonce + ciphertext).decode('utf-8')

print(f"原始数据: {json.dumps(original_wallet, ensure_ascii=False)}")
print(f"加密后: {encrypted_data[:80]}...")

# 模拟服务器存储
test_data['encrypted_data'] = encrypted_data
print(f"\n✅ 数据已准备好，模拟存储在数据库中")

print("\n" + "="*60)
print("步骤2：客服工具解密（模拟decrypt_tool_gui.py的decrypt_row）")
print("="*60)

# 解密逻辑（与decrypt_tool_gui.py完全一致）
wallet = test_data
encrypted_data_str = wallet.get('encrypted_data', '')

print(f"接收到的encrypted_data: {encrypted_data_str[:80]}...")

# 判断数据类型
if encrypted_data_str.startswith('{'):
    print("检测到明文JSON")
    wallet_data = json.loads(encrypted_data_str)
else:
    print("检测到Base64加密数据，开始解密...")
    encrypted_bytes = base64.b64decode(encrypted_data_str)
    nonce = encrypted_bytes[:12]
    ciphertext = encrypted_bytes[12:]
    aesgcm = AESGCM(CLIENT_KEY)
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    wallet_data = json.loads(decrypted_bytes.decode('utf-8'))

print("\n✅ 解密成功！")
print(f"地址: {wallet_data.get('address')}")
print(f"私钥: {wallet_data.get('private_key')}")
print(f"助记词: {wallet_data.get('mnemonic')}")

print("\n" + "="*60)
print("步骤3：验证数据完整性")
print("="*60)

assert wallet_data['address'] == original_wallet['address'], "地址不匹配！"
assert wallet_data['private_key'] == original_wallet['private_key'], "私钥不匹配！"
assert wallet_data['mnemonic'] == original_wallet['mnemonic'], "助记词不匹配！"

print("✅ 地址匹配: PASS")
print("✅ 私钥匹配: PASS")
print("✅ 助记词匹配: PASS")
print("\n" + "="*60)
print("✅✅✅ 完整流程测试通过！现在可以更新decrypt_tool_gui了")
print("="*60)
