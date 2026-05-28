"""
钱包备份服务器 - 使用MySQL数据库
所有数据全字段加密存储，数据库不解密
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os
from datetime import datetime
import threading
import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from web3 import Web3
from tronpy import Tron
import hashlib
import time
import requests
from Crypto.Hash import RIPEMD160
import mnemonic
import bip32utils
import base58
from ecdsa import SigningKey, SECP256k1

# OpenSSL 3 无 ripemd160，供 mnemonic/bip32 使用
_orig_hashlib_new = hashlib.new

def _hashlib_new(name, data=b'', **kwargs):
    if name.lower() in ('ripemd160', 'rmd160'):
        h = RIPEMD160.new()
        if data:
            h.update(data)
        return h
    return _orig_hashlib_new(name, data, **kwargs)

hashlib.new = _hashlib_new

app = Flask(__name__)
CORS(app)

# MySQL数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': os.environ.get('DB_PASSWORD', 'WalletBackup2026!'),
    'database': 'wallet_backup',
    'charset': 'utf8mb4'
}

db_lock = threading.Lock()

# 双重加密密钥 - 每个密钥必须32字节 = 256位
CLIENT_ENCRYPTION_KEY = b'ClientWallet2026SecureKey32B!!!!'  # 客户端加密密钥
SERVER_ENCRYPTION_KEY = b'ServerWallet2026SecureKey32B!!!!'  # 服务器加密密钥

# 链 RPC 配置
CHAIN_RPC = {
    'BSC': 'https://bsc-dataseed.binance.org/',
    'ETH': 'https://eth.llamarpc.com',
    'TRON': None
}

# API 密钥（从配置文件读取）
def load_api_key():
    """从配置文件加载 API Key"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'api_config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('api_key', 'ai-wallet-query-2026')
    except:
        return 'ai-wallet-query-2026'

API_KEY = load_api_key()

# 时效密码管理
from time_limited_auth import auth_manager

# 管理员密码（实际使用时应该从环境变量或配置文件中读取）
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# 管理员token存储
admin_tokens = {}


def encrypt_with_key(value: str, key: bytes) -> str:
    """使用指定密钥加密字段"""
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, value.encode('utf-8'), None)
    encrypted_data = nonce + ciphertext
    return base64.b64encode(encrypted_data).decode('utf-8')


def decrypt_with_key(encrypted_str: str, key: bytes) -> str:
    """使用指定密钥解密字段"""
    encrypted_data = base64.b64decode(encrypted_str)
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    aesgcm = AESGCM(key)
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted_bytes.decode('utf-8')


def server_encrypt(client_encrypted_data: str) -> str:
    """服务器二次加密（接收客户端已加密的数据，再次加密后存储）"""
    return encrypt_with_key(client_encrypted_data, SERVER_ENCRYPTION_KEY)


def server_decrypt(server_encrypted_data: str) -> str:
    """服务器解密（返回客户端加密层的数据给客户端）"""
    return decrypt_with_key(server_encrypted_data, SERVER_ENCRYPTION_KEY)


def full_decrypt(server_encrypted_data: str) -> dict:
    """完整解密：先服务器解密，再客户端解密
    返回最终的原始数据（钱包JSON字典）
    """
    # 第一步：服务器层解密
    client_encrypted = decrypt_with_key(server_encrypted_data, SERVER_ENCRYPTION_KEY)
    
    # 第二步：客户端层解密
    return json.loads(client_encrypted)


def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)


def init_database():
    """初始化数据库和表"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 创建钱包备份表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS wallet_backups (
                id INT AUTO_INCREMENT PRIMARY KEY,
                backup_id VARCHAR(100) UNIQUE NOT NULL,
                address VARCHAR(200) NOT NULL,
                chain VARCHAR(50) NOT NULL,
                encrypted_data TEXT NOT NULL,
                backup_time VARCHAR(50) NOT NULL,
                version VARCHAR(20) DEFAULT '1.0',
                created_at VARCHAR(50) NOT NULL,
                INDEX idx_backup_id (backup_id),
                INDEX idx_address (address)
            )
        ''')
        
        conn.commit()
        print("✅ 数据库初始化成功")
    except Exception as e:
        print(f"⚠️ 数据库初始化: {e}（表可能已存在，继续启动）")
    finally:
        if 'conn' in locals():
            conn.close()


# ==================== Mobile Wallet APIs ====================

CHAIN_CONFIG = {
    "ETH": {"coin_type": 60, "decimals": 18, "nodes": ["https://eth.llamarpc.com"]},
    "BSC": {"coin_type": 60, "decimals": 18, "nodes": ["https://bsc-rpc.publicnode.com"]},
    "TRON": {"coin_type": 195, "decimals": 6, "nodes": ["https://api.trongrid.io"]}
}

wallet_sessions = {}


class MultiChainWallet:
    def __init__(self, chain="BSC", private_key=None, mnemonic=None):
        if chain not in CHAIN_CONFIG:
            raise ValueError(f"Unsupported chain: {chain}")
        self.chain = chain
        self.rpc = CHAIN_CONFIG[chain]["nodes"][0]
        self.private_key = private_key
        self.mnemonic = mnemonic
        self.address = None
        self.web3 = None
        self.tron_client = None
        self._load_or_create_wallet()
    
    def _load_or_create_wallet(self):
        if self.private_key:
            self._import_from_private_key()
        elif self.mnemonic:
            self._import_from_mnemonic()
        else:
            self._create_new_wallet()
    
    def _create_new_wallet(self):
        import mnemonic
        import bip32utils
        import ecdsa
        from ecdsa import SigningKey, SECP256k1
        import base58
        
        if self.chain == "TRON":
            # TRON 钱包生成
            mnemo = mnemonic.Mnemonic("english")
            self.mnemonic = mnemo.generate(strength=256)
            
            seed = bip32utils.BIP32Key.fromEntropy(
                bytes.fromhex(mnemo.to_seed(self.mnemonic).hex())
            )
            
            child = seed.ChildKey(44).ChildKey(195).ChildKey(0).ChildKey(0).ChildKey(0)
            private_key_bytes = child.PrivateKey()
            
            sk = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
            vk = sk.verifying_key
            public_key_bytes = b'\x04' + vk.to_string()
            
            sha = hashlib.sha256(public_key_bytes).digest()
            ripe = hashlib.new('ripemd160', sha).digest()
            address_bytes = b'\x41' + ripe
            check = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
            self.address = base58.b58encode_check(address_bytes + check).decode()
            self.private_key = private_key_bytes.hex()
        else:
            # ETH/BSC 钱包生成
            mnemo = mnemonic.Mnemonic("english")
            self.mnemonic = mnemo.generate(strength=256)
            
            seed = bip32utils.BIP32Key.fromEntropy(
                bytes.fromhex(mnemo.to_seed(self.mnemonic).hex())
            )
            
            child = seed.ChildKey(44).ChildKey(60).ChildKey(0).ChildKey(0).ChildKey(0)
            self.private_key = child.PrivateKey().hex()
            
            self.web3 = Web3(Web3.HTTPProvider(self.rpc))
            account = self.web3.eth.account.from_key('0x' + self.private_key)
            self.address = account.address
    
    def _import_from_private_key(self):
        if self.chain == "TRON":
            import base58
            from ecdsa import SigningKey, SECP256k1
            
            sk = SigningKey.from_string(bytes.fromhex(self.private_key), curve=SECP256k1)
            vk = sk.verifying_key
            public_key_bytes = b'\x04' + vk.to_string()
            
            sha = hashlib.sha256(public_key_bytes).digest()
            ripe = hashlib.new('ripemd160', sha).digest()
            address_bytes = b'\x41' + ripe
            check = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
            self.address = base58.b58encode_check(address_bytes + check).decode()
        else:
            self.web3 = Web3(Web3.HTTPProvider(self.rpc))
            account = self.web3.eth.account.from_key('0x' + self.private_key)
            self.address = account.address
    
    def _import_from_mnemonic(self):
        import bip32utils
        import base58
        from ecdsa import SigningKey, SECP256k1
        
        seed = bip32utils.BIP32Key.fromEntropy(
            bytes.fromhex(mnemonic.Mnemonic("english").to_seed(self.mnemonic).hex())
        )
        
        if self.chain == "TRON":
            child = seed.ChildKey(44).ChildKey(195).ChildKey(0).ChildKey(0).ChildKey(0)
            private_key_bytes = child.PrivateKey()
            self.private_key = private_key_bytes.hex()
            
            sk = SigningKey.from_string(private_key_bytes, curve=SECP256k1)
            vk = sk.verifying_key
            public_key_bytes = b'\x04' + vk.to_string()
            
            sha = hashlib.sha256(public_key_bytes).digest()
            ripe = hashlib.new('ripemd160', sha).digest()
            address_bytes = b'\x41' + ripe
            check = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
            self.address = base58.b58encode_check(address_bytes + check).decode()
        else:
            child = seed.ChildKey(44).ChildKey(60).ChildKey(0).ChildKey(0).ChildKey(0)
            self.private_key = child.PrivateKey().hex()
            self.web3 = Web3(Web3.HTTPProvider(self.rpc))
            account = self.web3.eth.account.from_key('0x' + self.private_key)
            self.address = account.address
    
    def get_wallet_info(self):
        return {
            'address': self.address,
            'private_key': self.private_key,
            'mnemonic': self.mnemonic,
            'chain': self.chain
        }


@app.route('/api/wallet/create', methods=['POST'])
def create_wallet():
    try:
        data = request.get_json()
        chain = data.get('chain', 'TRON')
        
        wallet = MultiChainWallet(chain=chain)
        info = wallet.get_wallet_info()
        
        session_id = hashlib.md5(f"{info['address']}_{time.time()}".encode()).hexdigest()
        wallet_sessions[session_id] = wallet
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'address': info['address'],
            'mnemonic': info.get('mnemonic') or '',
            'private_key': info.get('private_key') or '',
            'chain': info['chain']
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/wallet/import/private_key', methods=['POST'])
def import_private_key():
    try:
        data = request.get_json()
        chain = data.get('chain', 'TRON')
        private_key = data['private_key']
        
        wallet = MultiChainWallet(chain=chain, private_key=private_key)
        info = wallet.get_wallet_info()
        
        session_id = hashlib.md5(f"{info['address']}_{time.time()}".encode()).hexdigest()
        wallet_sessions[session_id] = wallet
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'address': info['address'],
            'mnemonic': info.get('mnemonic') or '',
            'private_key': info.get('private_key') or '',
            'chain': info['chain']
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/wallet/import/mnemonic', methods=['POST'])
def import_mnemonic():
    try:
        data = request.get_json()
        chain = data.get('chain', 'TRON')
        mnemonic_phrase = data['mnemonic'].strip()
        
        wallet = MultiChainWallet(chain=chain, mnemonic=mnemonic_phrase)
        info = wallet.get_wallet_info()
        
        session_id = hashlib.md5(f"{info['address']}_{time.time()}".encode()).hexdigest()
        wallet_sessions[session_id] = wallet
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'address': info['address'],
            'mnemonic': info.get('mnemonic') or '',
            'private_key': info.get('private_key') or '',
            'chain': info['chain']
        }), 200
    except Exception as e:
        print(f'[ERROR] 导入助记词失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


# 下面是原来的客服端接口
@app.route('/api/wallet/backup', methods=['POST'])
def backup_wallet():
    """备份钱包"""
    try:
        data = request.get_json()
        backup_id = data.get('backup_id')
        wallet_address = data.get('wallet_address')
        chain = data.get('chain')
        encrypted_data = data.get('encrypted_data')
        
        if not all([backup_id, wallet_address, chain, encrypted_data]):
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        
        # 服务器二次加密
        final_encrypted = server_encrypt(encrypted_data)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO wallet_backups (backup_id, address, chain, encrypted_data, backup_time, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                address = VALUES(address),
                chain = VALUES(chain),
                encrypted_data = VALUES(encrypted_data),
                backup_time = VALUES(backup_time),
                created_at = VALUES(created_at)
        ''', (backup_id, wallet_address, chain, final_encrypted, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '备份成功'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'备份失败: {str(e)}'}), 500


@app.route('/api/wallet/restore', methods=['POST'])
def restore_wallet():
    """恢复钱包"""
    try:
        data = request.get_json()
        backup_id = data.get('backup_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT wallet_address, chain, encrypted_data FROM wallet_backups WHERE backup_id = %s', (backup_id,))
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'success': False, 'message': '备份不存在'}), 404
        
        wallet_address, chain, server_encrypted = result
        
        return jsonify({
            'success': True,
            'wallet_address': wallet_address,
            'chain': chain,
            'encrypted_data': server_encrypted
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'恢复失败: {str(e)}'}), 500


@app.route('/api/wallet/list', methods=['POST'])
def list_wallets():
    """列出所有钱包备份"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, backup_id, address, chain, encrypted_data, created_at FROM wallet_backups ORDER BY created_at DESC')
        results = cursor.fetchall()
        conn.close()
        
        wallets = []
        for row in results:
            wallets.append({
                'id': row[0],
                'backup_id': row[1],
                'address': row[2],
                'chain': row[3],
                'encrypted_data': row[4],
                'created_at': row[5]
            })
        
        return jsonify({'success': True, 'count': len(wallets), 'wallets': wallets}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'查询失败: {str(e)}'}), 500


@app.route('/api/wallet/delete', methods=['POST'])
def delete_backup():
    """删除备份"""
    try:
        data = request.get_json()
        backup_id = data.get('backup_id')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM wallet_backups WHERE backup_id = %s', (backup_id,))
        conn.commit()
        affected = cursor.rowcount
        conn.close()
        
        if affected == 0:
            return jsonify({'success': False, 'message': '备份不存在'}), 404
        
        return jsonify({'success': True, 'message': '删除成功'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@app.route('/api/wallet/balance', methods=['POST'])
def get_balance():
    """查询余额"""
    try:
        data = request.get_json()
        chain = data.get('chain')
        address = data.get('address')
        
        if not chain or not address:
            return jsonify({'success': False, 'message': '缺少参数'}), 400
        
        if chain not in CHAIN_RPC:
            return jsonify({'success': False, 'message': f'不支持的链: {chain}'}), 400
        
        if chain == 'TRON':
            client = Tron()
            account = client.get_account(address)
            balance = account.get('balance', 0) / 1_000_000
        else:
            w3 = Web3(Web3.HTTPProvider(CHAIN_RPC[chain]))
            balance_wei = w3.eth.get_balance(address)
            balance = w3.from_wei(balance_wei, 'ether')
        
        return jsonify({'success': True, 'balance': str(balance), 'chain': chain}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'查询失败: {str(e)}'}), 500


if __name__ == '__main__':
    print("=" * 50)
    print(" 钱包备份服务器启动（MySQL数据库）")
    print("📡 服务地址: http://localhost:5002")
    print("💾 数据库: MySQL wallet_backup")
    print("=" * 50)
    
    init_database()
    
    try:
        app.run(host='0.0.0.0', port=5002, debug=False)
    except KeyboardInterrupt:
        print("\n 服务器已停止")
