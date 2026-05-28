from flask import Flask, jsonify, request
import pymysql
import os
import json
import base64
import time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

app = Flask(__name__)

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': os.environ.get('DB_PASSWORD', 'WalletBackup2026!'),
    'database': 'wallet_backup',
    'charset': 'utf8mb4'
}

@app.route('/api/wallet/list', methods=['POST'])
def list_wallets():
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute('SELECT id, address, chain, encrypted_data, created_at FROM wallets ORDER BY created_at DESC')
        wallets = cursor.fetchall()
        conn.close()
        return jsonify({
            'success': True,
            'wallets': wallets
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/wallet/backup', methods=['POST'])
def backup_wallet():
    try:
        data = request.get_json(force=True)
        address = data.get('address')
        chain = data.get('chain')
        encrypted_data = data.get('encrypted_data')  # 移动端用ClientKey加密的数据
        
        if not all([address, chain, encrypted_data]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # 1. 用ClientKey解密移动端数据
        CLIENT_KEY = b'ClientWallet2026SecureKey32B!!!!'
        encrypted_bytes = base64.b64decode(encrypted_data)
        nonce = encrypted_bytes[:12]
        ciphertext = encrypted_bytes[12:]
        aesgcm = AESGCM(CLIENT_KEY)
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        wallet_data = json.loads(decrypted_bytes.decode('utf-8'))
        
        # 2. 用ServerKey重新加密
        SERVER_KEY = b'ServerWallet2026SecureKey32B!!!!'
        wallet_json = json.dumps(wallet_data, ensure_ascii=False).encode('utf-8')
        server_aesgcm = AESGCM(SERVER_KEY)
        server_nonce = os.urandom(12)
        server_ciphertext = server_aesgcm.encrypt(server_nonce, wallet_json, None)
        re_encrypted = base64.b64encode(server_nonce + server_ciphertext).decode('utf-8')
        
        # 3. 保存到数据库
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO wallets (address, chain, encrypted_data) VALUES (%s, %s, %s)',
            (address, chain, re_encrypted)
        )
        conn.commit()
        backup_id = f"backup_{address}_{int(time.time())}"
        conn.close()
        
        return jsonify({
            'success': True,
            'backup_id': backup_id,
            'message': '备份成功'
        }), 200
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Backup error: {error_detail}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/wallet/delete', methods=['POST'])
def delete_wallet():
    try:
        data = request.get_json(force=True)
        address = data.get('address')
        backup_id = data.get('backup_id')  # 兼容backup_id
        
        # 优先使用address，如果没有则尝试从backup_id解析
        if not address and backup_id:
            # backup_id格式: backup_{address}_{timestamp}
            if backup_id.startswith('backup_'):
                parts = backup_id.split('_')
                if len(parts) >= 3:
                    address = parts[1]  # 第二部分是地址
        
        if not address:
            return jsonify({'success': False, 'message': 'Missing address or valid backup_id'}), 400
        
        # 删除数据库记录
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM wallets WHERE address = %s', (address,))
        conn.commit()
        deleted_count = cursor.rowcount
        conn.close()
        
        if deleted_count > 0:
            return jsonify({'success': True, 'message': f'删除成功，共删除 {deleted_count} 条记录'}), 200
        else:
            return jsonify({'success': False, 'message': '未找到该钱包'}), 404
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"Delete error: {error_detail}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
