#!/usr/bin/env python3
import os, json, base64, pymysql, datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CLIENT_KEY = b'ClientWallet2026SecureKey32B!!!!'

def encrypt_wallet_data(wallet_data):
    json_bytes = json.dumps(wallet_data, ensure_ascii=False).encode('utf-8')
    nonce = os.urandom(12)
    aesgcm = AESGCM(CLIENT_KEY)
    ciphertext = aesgcm.encrypt(nonce, json_bytes, None)
    return base64.b64encode(nonce + ciphertext).decode('utf-8')

def decrypt_wallet_data(encrypted_str):
    encrypted_bytes = base64.b64decode(encrypted_str)
    nonce = encrypted_bytes[:12]
    ciphertext = encrypted_bytes[12:]
    aesgcm = AESGCM(CLIENT_KEY)
    return json.loads(aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8'))

test_wallets = [
    {'address': '0xTestAddress001', 'chain': 'BSC', 'private_key': '0xPrivateKey001abcdef1234567890abcdef1234567890abcdef1234567890abcdef', 'mnemonic': 'test zero one two three four five six seven eight nine ten'},
    {'address': '0xTestAddress002', 'chain': 'ETH', 'private_key': '0xPrivateKey002abcdef1234567890abcdef1234567890abcdef1234567890abcdef', 'mnemonic': 'test alpha beta gamma delta epsilon zeta eta theta iota kappa lambda'}
]

conn = pymysql.connect(host='127.0.0.1', user='root', password='WalletBackup2026!', database='wallet_backup')
cursor = conn.cursor()

print("="*60)
print("测试1：客户端加密并插入数据库")
print("="*60)

for i, wallet in enumerate(test_wallets, 1):
    encrypted = encrypt_wallet_data(wallet)
    backup_id = f"test_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{i}"
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO wallet_backups (backup_id, address, chain, encrypted_data, backup_time, version, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                   (backup_id, wallet['address'], wallet['chain'], encrypted, now, '1.0', now))
    print(f'✅ 钱包{i} 已插入: {wallet["address"]}')
    print(f'   加密数据前60位: {encrypted[:60]}...')

conn.commit()

print("\n" + "="*60)
print("测试2：客服工具解密验证")
print("="*60)

cursor.execute('SELECT * FROM wallet_backups ORDER BY id DESC LIMIT 2')
rows = cursor.fetchall()

for i, row in enumerate(rows, 1):
    print(f'\n--- 钱包{i} (ID: {row[0]}) ---')
    print(f'地址: {row[2]} | 链: {row[3]}')
    print(f'加密数据前60位: {row[4][:60]}...')
    
    if row[4].startswith('{'):
        print('❌ 这是明文JSON数据！')
    else:
        try:
            data = decrypt_wallet_data(row[4])
            print(f'✅ 解密成功！')
            print(f'  地址: {data["address"]}')
            print(f'  私钥: {data["private_key"][:30]}...')
            print(f'  助记词: {data["mnemonic"][:40]}...')
        except Exception as e:
            print(f'❌ 解密失败: {str(e)}')

cursor.close()
conn.close()

print("\n" + "="*60)
print("✅ 测试完成！现在可以重启decrypt_tool_gui验证")
print("="*60)
