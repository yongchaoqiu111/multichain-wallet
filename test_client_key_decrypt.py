#!/usr/bin/env python3
import pymysql
import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='WalletBackup2026!',
    database='wallet_backup'
)

cursor = conn.cursor(pymysql.cursors.DictCursor)
cursor.execute("SELECT id, address, encrypted_data FROM wallet_backups LIMIT 1")
wallet = cursor.fetchone()

print(f"钱包ID: {wallet['id']}")
print(f"地址: {wallet['address']}")

# 尝试用CLIENT_KEY解密
try:
    CLIENT_KEY = b'ClientWallet2026SecureKey32B!!!!'
    encrypted_bytes = base64.b64decode(wallet['encrypted_data'])
    nonce = encrypted_bytes[:12]
    ciphertext = encrypted_bytes[12:]
    
    aesgcm = AESGCM(CLIENT_KEY)
    decrypted_json = aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
    decrypted_wallet = json.loads(decrypted_json)
    
    print(f"\n✅ CLIENT_KEY解密成功！")
    print(f"私钥: {decrypted_wallet.get('private_key')}")
    print(f"助记词: {decrypted_wallet.get('mnemonic')}")
    
except Exception as e:
    print(f"\n❌ CLIENT_KEY解密失败: {e}")

cursor.close()
conn.close()
