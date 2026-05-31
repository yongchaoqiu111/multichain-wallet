#!/usr/bin/env python3
import pymysql
import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# 连接数据库
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
print(f"encrypted_data长度: {len(wallet['encrypted_data'])}")
print(f"前50字符: {wallet['encrypted_data'][:50]}")

# 尝试解密
try:
    SERVER_KEY = b'ServerWallet2026SecureKey32B!!!!'
    encrypted_bytes = base64.b64decode(wallet['encrypted_data'])
    nonce = encrypted_bytes[:12]
    ciphertext = encrypted_bytes[12:]
    
    aesgcm = AESGCM(SERVER_KEY)
    decrypted_json = aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
    decrypted_wallet = json.loads(decrypted_json)
    
    print(f"\n✅ 解密成功！")
    print(f"私钥: {decrypted_wallet.get('private_key')}")
    print(f"助记词: {decrypted_wallet.get('mnemonic')}")
    
except Exception as e:
    print(f"\n❌ 解密失败: {e}")
    import traceback
    traceback.print_exc()

cursor.close()
conn.close()
