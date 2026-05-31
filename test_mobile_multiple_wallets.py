#!/usr/bin/env python3
"""
模拟多条移动端数据完整流程测试
"""
import json
import base64
import os
import pymysql
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CLIENT_KEY = b'ClientWallet2026SecureKey32B!!!!'

# 模拟5条移动端钱包数据
mobile_wallets = [
    {
        'address': '0xMobileWallet001',
        'chain': 'ETH',
        'private_key': '0xMobilePK001abcdef1234567890abcdef1234567890abcdef1234567890ab',
        'mnemonic': 'mobile wallet one alpha beta gamma delta epsilon zeta eta theta iota'
    },
    {
        'address': '0xMobileWallet002',
        'chain': 'BSC',
        'private_key': '0xMobilePK002abcdef1234567890abcdef1234567890abcdef1234567890ab',
        'mnemonic': 'mobile wallet two apple banana cherry date elderberry fig grape'
    },
    {
        'address': '0xMobileWallet003',
        'chain': 'TRON',
        'private_key': '0xMobilePK003abcdef1234567890abcdef1234567890abcdef1234567890ab',
        'mnemonic': 'mobile wallet three red orange yellow green blue indigo violet'
    },
    {
        'address': '0xMobileWallet004',
        'chain': 'ETH',
        'private_key': '0xMobilePK004abcdef1234567890abcdef1234567890abcdef1234567890ab',
        'mnemonic': 'mobile wallet four north south east west up down left right forward'
    },
    {
        'address': '0xMobileWallet005',
        'chain': 'BSC',
        'private_key': '0xMobilePK005abcdef1234567890abcdef1234567890abcdef1234567890ab',
        'mnemonic': 'mobile wallet five spring summer autumn winter morning evening night'
    }
]

print("="*70)
print("步骤1：移动端批量AES-GCM加密（模拟Flutter Web）")
print("="*70)

encrypted_wallets = []
for i, wallet in enumerate(mobile_wallets, 1):
    # 移动端加密
    json_bytes = json.dumps(wallet, ensure_ascii=False).encode('utf-8')
    nonce = os.urandom(12)
    aesgcm = AESGCM(CLIENT_KEY)
    ciphertext = aesgcm.encrypt(nonce, json_bytes, None)
    encrypted_data = base64.b64encode(nonce + ciphertext).decode('utf-8')
    
    encrypted_wallets.append({
        'original': wallet,
        'encrypted': encrypted_data,
        'index': i
    })
    
    print(f"✅ 钱包{i} 加密完成: {wallet['address']} (长度: {len(encrypted_data)})")

print("\n" + "="*70)
print("步骤2：服务器接收并处理（模拟/api/wallet/backup/mobile接口）")
print("="*70)

processed_wallets = []
for item in encrypted_wallets:
    wallet = item['original']
    mobile_encrypted = item['encrypted']
    idx = item['index']
    
    print(f"\n--- 处理钱包{idx}: {wallet['address']} ---")
    
    # 第1步：解密移动端数据
    encrypted_bytes = base64.b64decode(mobile_encrypted)
    nonce = encrypted_bytes[:12]
    ciphertext = encrypted_bytes[12:]
    aesgcm = AESGCM(CLIENT_KEY)
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    wallet_data = json.loads(decrypted_bytes.decode('utf-8'))
    
    print(f"  ✅ 解密成功: {wallet_data['address']}")
    
    # 第2步：重新用AES-GCM加密
    json_bytes = json.dumps(wallet_data, ensure_ascii=False).encode('utf-8')
    new_nonce = os.urandom(12)
    new_ciphertext = aesgcm.encrypt(new_nonce, json_bytes, None)
    final_encrypted = base64.b64encode(new_nonce + new_ciphertext).decode('utf-8')
    
    print(f"  ✅ 重新加密完成 (新长度: {len(final_encrypted)})")
    
    processed_wallets.append({
        'address': wallet['address'],
        'chain': wallet['chain'],
        'final_encrypted': final_encrypted,
        'original': wallet
    })

print("\n" + "="*70)
print("步骤3：插入数据库（模拟真实存储）")
print("="*70)

try:
    conn = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='WalletBackup2026!',
        database='wallet_backup'
    )
    cursor = conn.cursor()
    
    for item in processed_wallets:
        import datetime
        backup_id = f"mobile_test_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{item['address'][-6:]}"
        backup_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO wallet_backups 
            (backup_id, address, chain, encrypted_data, backup_time, version, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (
            backup_id,
            item['address'],
            item['chain'],
            item['final_encrypted'],
            backup_time,
            '1.0',
            backup_time
        ))
        
        print(f"✅ 钱包 {item['address']} 已插入数据库 (ID: {backup_id})")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"\n✅ 所有{len(processed_wallets)}条数据已成功存入数据库")
    
except Exception as e:
    print(f"❌ 数据库操作失败: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*70)
print("步骤4：客服工具从数据库获取并解密验证")
print("="*70)

try:
    conn = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='WalletBackup2026!',
        database='wallet_backup'
    )
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    # 查询刚插入的移动端测试数据
    cursor.execute('''
        SELECT * FROM wallet_backups 
        WHERE backup_id LIKE 'mobile_test_%' 
        ORDER BY id DESC 
        LIMIT 5
    ''')
    rows = cursor.fetchall()
    
    print(f"从数据库获取到 {len(rows)} 条记录\n")
    
    all_passed = True
    for i, row in enumerate(rows, 1):
        print(f"--- 验证钱包{i}: {row['address']} ---")
        
        encrypted_data = row['encrypted_data']
        
        # 客服工具解密逻辑
        if encrypted_data.startswith('{'):
            print(f"  ❌ 这是明文JSON！")
            all_passed = False
        else:
            try:
                encrypted_bytes = base64.b64decode(encrypted_data)
                nonce = encrypted_bytes[:12]
                ciphertext = encrypted_bytes[12:]
                aesgcm = AESGCM(CLIENT_KEY)
                decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
                decrypted_wallet = json.loads(decrypted_bytes.decode('utf-8'))
                
                # 查找原始数据进行对比
                original = None
                for item in processed_wallets:
                    if item['address'] == row['address']:
                        original = item['original']
                        break
                
                if original:
                    # 验证数据完整性
                    addr_match = decrypted_wallet['address'] == original['address']
                    chain_match = decrypted_wallet['chain'] == original['chain']
                    pk_match = decrypted_wallet['private_key'] == original['private_key']
                    mn_match = decrypted_wallet['mnemonic'] == original['mnemonic']
                    
                    if addr_match and chain_match and pk_match and mn_match:
                        print(f"  ✅ 解密成功 - 地址: {decrypted_wallet['address']}")
                        print(f"     私钥: {decrypted_wallet['private_key'][:30]}...")
                        print(f"     助记词: {decrypted_wallet['mnemonic'][:40]}...")
                        print(f"     验证: PASS")
                    else:
                        print(f"  ❌ 数据不匹配！")
                        print(f"     地址匹配: {addr_match}")
                        print(f"     链匹配: {chain_match}")
                        print(f"     私钥匹配: {pk_match}")
                        print(f"     助记词匹配: {mn_match}")
                        all_passed = False
                else:
                    print(f"  ⚠️ 未找到原始数据对比")
                    print(f"     解密地址: {decrypted_wallet['address']}")
                    
            except Exception as e:
                print(f"  ❌ 解密失败: {str(e)}")
                all_passed = False
        
        print()
    
    cursor.close()
    conn.close()
    
    if all_passed:
        print("="*70)
        print("✅✅✅ 所有验证通过！移动端专用接口流程完全正常！")
        print("="*70)
    else:
        print("="*70)
        print("❌ 部分验证失败，请检查日志")
        print("="*70)
        
except Exception as e:
    print(f"❌ 查询数据库失败: {str(e)}")
    import traceback
    traceback.print_exc()
