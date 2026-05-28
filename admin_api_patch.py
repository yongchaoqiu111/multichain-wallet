
# 在 server.py 末尾添加以下代码（在 if __name__ == '__main__': 之前）

@app.route('/api/admin/list_all', methods=['GET'])
def admin_list_all():
    """管理员接口 - 获取所有钱包备份"""
    try:
        import pymysql
        
        DB_CONFIG = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': 'WalletBackup2026!',
            'database': 'wallet_backup',
            'charset': 'utf8mb4'
        }
        
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute('SELECT id, backup_id, address, chain, encrypted_data, backup_time FROM wallets ORDER BY backup_time DESC')
        wallets = cursor.fetchall()
        conn.close()
        
        return jsonify({
            'success': True,
            'count': len(wallets),
            'wallets': wallets
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/decrypt', methods=['POST'])
def admin_decrypt():
    """管理员接口 - 解密钱包地址"""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import base64
        
        data = request.get_json()
        encrypted_data = data.get('encrypted_data')
        
        # 双重解密密钥
        CLIENT_ENCRYPTION_KEY = b'ClientWallet2026SecureKey32B!!!!'
        SERVER_ENCRYPTION_KEY = b'ServerWallet2026SecureKey32B!!!!'
        
        # 第1次解密：服务器层
        encrypted_bytes = base64.b64decode(encrypted_data)
        nonce = encrypted_bytes[:12]
        ciphertext = encrypted_bytes[12:]
        aesgcm = AESGCM(SERVER_ENCRYPTION_KEY)
        client_encrypted = aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
        
        # 第2次解密：客户端层
        client_bytes = base64.b64decode(client_encrypted)
        nonce2 = client_bytes[:12]
        ciphertext2 = client_bytes[12:]
        aesgcm2 = AESGCM(CLIENT_ENCRYPTION_KEY)
        decrypted = aesgcm2.decrypt(nonce2, ciphertext2, None).decode('utf-8')
        
        return jsonify({
            'success': True,
            'decrypted_data': decrypted
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
