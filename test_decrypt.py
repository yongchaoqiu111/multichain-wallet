#!/usr/bin/env python3
import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# 从API获取的encrypted_data
data = "2oJTpLyxvJKyiS5MmFI9wZg3Nlk2Cye2lG1C2PmlYFME6SCHiBq6lpXcRi9z/bYskmJ+9OAomTC93ObVSDQANj/qmBxxqxGK+ySsRewgCwG1+Jr2B+YI+YH/hzVDDM9yTxvjjyU85x+56egQYAo2xIeuYAr0gqf+K7QJOQbFbtCKCioCb9Otqt4t2ZgJUELoxSyxrtZ1RxEdSsKq4Z6gZeRG1yPtJ5grwLRlRJDZ+nfKP0J15dRI4w3ITmSTzMSpMWWxiX5w+29LrgNNVzCJFqGOuWAaKXH0+9DRce+R3TkHIDNveG5zCee8OMrxARA4YK/e8Q9Qxio="

try:
    # Base64解码
    encrypted_bytes = base64.b64decode(data)
    
    # 提取nonce和ciphertext
    nonce = encrypted_bytes[:12]
    ciphertext = encrypted_bytes[12:]
    
    # 使用服务器密钥解密
    SERVER_KEY = b'ServerWallet2026SecureKey32B!!!!'
    aesgcm = AESGCM(SERVER_KEY)
    decrypted = aesgcm.decrypt(nonce, ciphertext, None)
    
    # 解析JSON
    wallet_data = json.loads(decrypted)
    
    print("✅ 解密成功！")
    print(f"地址: {wallet_data.get('address')}")
    print(f"私钥: {wallet_data.get('private_key')}")
    print(f"助记词: {wallet_data.get('mnemonic')}")
    
except Exception as e:
    print(f"❌ 解密失败: {e}")
