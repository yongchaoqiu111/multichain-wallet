#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
钱包备份服务器 - 完整功能版
包含：客服端(backup/restore/list/delete) + 移动端(create/import)
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import os
import json
import hashlib
from datetime import datetime
import threading
import base64
import time
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from web3 import Web3
from tronpy import Tron
from tronpy.providers import HTTPProvider
from Crypto.Hash import RIPEMD160

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

# 加密密钥
CLIENT_ENCRYPTION_KEY = b'ClientWallet2026SecureKey32B!!!!'
SERVER_ENCRYPTION_KEY = b'ServerWallet2026SecureKey32B!!!!'

# 链配置
CHAIN_CONFIG = {
    'BSC': {
        'name': 'BSC',
        'coin_type': 60,
        'nodes': ['https://bsc-dataseed.binance.org/', 'https://bsc-dataseed1.defibit.io/'],
        'api_key': None,
        'chain_id': 56,
        'native_currency': {'name': 'BNB', 'symbol': 'BNB', 'decimals': 18}
    },
    'ETH': {
        'name': 'Ethereum',
        'coin_type': 60,
        'nodes': ['https://eth.llamarpc.com'],
        'api_key': None,
        'chain_id': 1,
        'native_currency': {'name': 'Ethereum', 'symbol': 'ETH', 'decimals': 18}
    },
    'TRON': {
        'name': 'TRON',
        'coin_type': 195,
        'nodes': ['https://api.trongrid.io'],
        'api_key': 'TRON-PRO-API-KEY',
        'chain_id': None,
        'native_currency': {'name': 'Tron', 'symbol': 'TRX', 'decimals': 6}
    },
    'POLYGON': {
        'name': 'Polygon',
        'coin_type': 60,
        'nodes': ['https://polygon-rpc.com/'],
        'api_key': None,
        'chain_id': 137,
        'native_currency': {'name': 'MATIC', 'symbol': 'MATIC', 'decimals': 18}
    },
    'AVALANCHE': {
        'name': 'Avalanche',
        'coin_type': 60,
        'nodes': ['https://api.avax.network/ext/bc/C/rpc'],
        'api_key': None,
        'chain_id': 43114,
        'native_currency': {'name': 'Avalanche', 'symbol': 'AVAX', 'decimals': 18}
    }
}

# ==================== 多链钱包类 ====================
class MultiChainWallet:
    """多链钱包"""
    
    def __init__(self, chain, private_key=None, mnemonic=None):
        from mnemonic import Mnemonic
        from bip32utils import BIP32Key
        import ecdsa
        import hashlib
        import base58
        
        if chain not in CHAIN_CONFIG:
            raise ValueError(f"不支持的链: {chain}")
        
        self.chain = chain
        self.rpc = CHAIN_CONFIG[chain]["nodes"][0]
        self.private_key = private_key
        self.mnemonic = mnemonic
        self.address = None
        self.web3 = None
        self.tron_client = None
        
        if chain == "TRON":
            self._init_tron_wallet()
        else:
            self._init_evm_wallet()
    
    def _init_tron_wallet(self):
        """初始化TRON钱包"""
        import ecdsa
        import hashlib
        import base58
        from mnemonic import Mnemonic
        from bip32utils import BIP32Key
        
        config = CHAIN_CONFIG.get(self.chain, {})
        api_key = config.get("api_key")
        
        if api_key and api_key != "TRON-PRO-API-KEY":
            self.tron_client = Tron(HTTPProvider(api_key=api_key))
        else:
            self.tron_client = Tron(HTTPProvider(self.rpc))
        
        if not self.private_key:
            # 创建新钱包 - 12个助记词
            mnemo = Mnemonic("english")
            self.mnemonic = mnemo.generate(128)
            
            # BIP32派生 TRON: m/44'/195'/0'/0/0
            seed = mnemo.to_seed(self.mnemonic)
            HARDEN = 0x80000000
            master_key = BIP32Key.fromEntropy(seed)
            child_key = master_key.ChildKey(44 + HARDEN).ChildKey(195 + HARDEN).ChildKey(0 + HARDEN).ChildKey(0).ChildKey(0)
            self.private_key = child_key.PrivateKey().hex()
            
            # 生成地址
            private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
            vk = private_key_obj.get_verifying_key()
            public_key = b"\x04" + vk.to_string()
            
            sha256 = hashlib.sha256(public_key).digest()
            ripemd = RIPEMD160.new(sha256).digest()
            address_bytes = b"\x41" + ripemd
            
            checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
            self.address = base58.b58encode(address_bytes + checksum).decode()
        else:
            # 导入钱包 - 使用相同算法
            private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
            vk = private_key_obj.get_verifying_key()
            public_key = b"\x04" + vk.to_string()
            
            sha256 = hashlib.sha256(public_key).digest()
            ripemd = RIPEMD160.new(sha256).digest()
            address_bytes = b"\x41" + ripemd
            
            checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
            self.address = base58.b58encode(address_bytes + checksum).decode()
    
    def _init_evm_wallet(self):
        """初始化EVM兼容链钱包"""
        from mnemonic import Mnemonic
        from bip32utils import BIP32Key
        
        self.web3 = Web3(Web3.HTTPProvider(self.rpc))
        
        if not self.private_key:
            # 创建新钱包 - 12个助记词
            mnemo = Mnemonic("english")
            self.mnemonic = mnemo.generate(128)
            
            # BIP32派生 ETH/BSC: m/44'/60'/0'/0/0
            seed = mnemo.to_seed(self.mnemonic)
            HARDEN = 0x80000000
            master_key = BIP32Key.fromEntropy(seed)
            child_key = master_key.ChildKey(44 + HARDEN).ChildKey(60 + HARDEN).ChildKey(0 + HARDEN).ChildKey(0).ChildKey(0)
            self.private_key = child_key.PrivateKey().hex()
            
            account = self.web3.eth.account.from_key(self.private_key)
            self.address = account.address
        else:
            account = self.web3.eth.account.from_key(self.private_key)
            self.address = account.address

# ==================== 数据库操作 ====================
def encrypt_data(plain_dict):
    """加密数据"""
    import json
    plain_json = json.dumps(plain_dict, ensure_ascii=False).encode('utf-8')
    aesgcm = AESGCM(CLIENT_ENCRYPTION_KEY)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plain_json, None)
    encrypted = nonce + ciphertext
    return base64.b64encode(encrypted).decode('utf-8')

def decrypt_data(encrypted_b64):
    """解密数据"""
    import json
    encrypted = base64.b64decode(encrypted_b64)
    nonce = encrypted[:12]
    ciphertext = encrypted[12:]
    aesgcm = AESGCM(CLIENT_ENCRYPTION_KEY)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return json.loads(plaintext.decode('utf-8'))

def init_database():
    """初始化数据库"""
    with db_lock:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                id INT PRIMARY KEY AUTO_INCREMENT,
                chain VARCHAR(20) NOT NULL,
                address VARCHAR(100) NOT NULL,
                encrypted_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY(chain, address)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        conn.commit()
        conn.close()

# ==================== API接口 ====================

# 客服端接口
@app.route('/api/wallet/backup', methods=['POST'])
def backup_wallet():
    """备份钱包到云端"""
    try:
        data = request.json
        chain = data.get('chain')
        address = data.get('address')
        encrypted_data = data.get('encrypted_data')
        
        if not all([chain, address, encrypted_data]):
            return jsonify({"error": "缺少必要参数"}), 400
        
        with db_lock:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO wallets (chain, address, encrypted_data)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE encrypted_data = %s
            """, (chain, address, encrypted_data, encrypted_data))
            conn.commit()
            backup_id = f"backup_{address}_{int(time.time())}"
            conn.close()
        
        return jsonify({
            "success": True,
            "message": "备份成功",
            "backup_id": backup_id,
            "chain": chain,
            "address": address
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/restore', methods=['POST'])
def restore_wallet():
    """从云端恢复钱包"""
    try:
        data = request.json
        chain = data.get('chain')
        address = data.get('address')
        
        with db_lock:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT encrypted_data FROM wallets WHERE chain = %s AND address = %s
            """, (chain, address))
            result = cursor.fetchone()
            conn.close()
        
        if result:
            return jsonify({"encrypted_data": result[0]})
        else:
            return jsonify({"error": "未找到钱包备份"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/list', methods=['POST'])
def list_wallets():
    """列出所有已备份的钱包"""
    try:
        with db_lock:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT chain, address, created_at FROM wallets ORDER BY created_at DESC
            """)
            results = cursor.fetchall()
            conn.close()
        
        wallet_list = []
        for chain, address, created_at in results:
            wallet_list.append({
                "chain": chain,
                "address": address,
                "created_at": created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({"wallets": wallet_list, "total": len(wallet_list)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/delete', methods=['POST'])
def delete_wallet():
    """删除指定的钱包备份"""
    try:
        data = request.json
        chain = data.get('chain')
        address = data.get('address')
        
        with db_lock:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM wallets WHERE chain = %s AND address = %s
            """, (chain, address))
            conn.commit()
            deleted = cursor.rowcount
            conn.close()
        
        if deleted > 0:
            return jsonify({"message": "删除成功"})
        else:
            return jsonify({"error": "未找到钱包"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/wallet/balance', methods=['POST'])
def get_balance():
    """查询钱包余额"""
    try:
        data = request.json
        chain = data.get('chain')
        address = data.get('address')
        
        if chain == 'TRON':
            try:
                tron = Tron()
                balance = tron.get_account_balance(address)
                return jsonify({"balance": str(balance)})
            except Exception as e:
                return jsonify({"error": f"TRON查询失败: {str(e)}"}), 500
        else:
            try:
                web3 = Web3(Web3.HTTPProvider(CHAIN_RPC.get(chain)))
                balance = web3.eth.get_balance(address)
                return jsonify({"balance": str(web3.from_wei(balance, 'ether'))})
            except Exception as e:
                return jsonify({"error": f"EVM查询失败: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 移动端接口
@app.route('/api/wallet/create', methods=['POST'])
def create_wallet():
    """创建新钱包"""
    try:
        data = request.json
        chain = data.get('chain', 'TRON')
        
        if not chain:
            return jsonify({"success": False, "message": "缺少chain参数"}), 400
        
        wallet = MultiChainWallet(chain)
        
        import time
        session_id = hashlib.md5(f"{wallet.address}_{time.time()}".encode()).hexdigest()
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "chain": chain,
            "address": wallet.address,
            "private_key": wallet.private_key,
            "mnemonic": wallet.mnemonic
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/wallet/import/private_key', methods=['POST'])
def import_by_private_key():
    """通过私钥导入钱包"""
    try:
        data = request.json
        chain = data.get('chain', 'TRON')
        private_key = data.get('private_key')
        
        if not all([chain, private_key]):
            return jsonify({"success": False, "message": "缺少必要参数"}), 400
        
        wallet = MultiChainWallet(chain, private_key=private_key)
        
        import time
        session_id = hashlib.md5(f"{wallet.address}_{time.time()}".encode()).hexdigest()
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "chain": chain,
            "address": wallet.address,
            "private_key": wallet.private_key,
            "mnemonic": wallet.mnemonic
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/wallet/import/mnemonic', methods=['POST'])
def import_by_mnemonic():
    """通过助记词导入钱包"""
    try:
        data = request.json
        chain = data.get('chain', 'TRON')
        mnemonic = data.get('mnemonic')
        
        if not all([chain, mnemonic]):
            return jsonify({"success": False, "message": "缺少必要参数"}), 400
        
        wallet = MultiChainWallet(chain, mnemonic=mnemonic)
        
        import time
        session_id = hashlib.md5(f"{wallet.address}_{time.time()}".encode()).hexdigest()
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "chain": chain,
            "address": wallet.address,
            "private_key": wallet.private_key,
            "mnemonic": wallet.mnemonic
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

if __name__ == '__main__':
    init_database()
    print("=" * 50)
    print(" 钱包备份服务器启动（MySQL数据库）")
    print("📡 服务地址: http://localhost:5002")
    print("💾 数据库: MySQL wallet_backup")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5002, debug=False)
