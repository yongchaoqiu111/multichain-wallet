from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys
import hashlib
import time
from Crypto.Hash import RIPEMD160

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

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

class Config:
    API_HOST = '0.0.0.0'
    API_PORT = 5000
    DEBUG = False

CHAIN_CONFIG = {
    "ETH": {"coin_type": 60, "decimals": 18, "nodes": ["https://eth.llamarpc.com"]},
    "BSC": {"coin_type": 60, "decimals": 18, "nodes": ["https://bsc-rpc.publicnode.com"]},
    "TRON": {"coin_type": 195, "decimals": 6, "nodes": ["https://api.trongrid.io"]}
}

_balance_cache = {}
_CACHE_TTL = 5

def get_balance(chain, address):
    import requests
    cache_key = f"{chain}:{address}"
    if cache_key in _balance_cache:
        cached = _balance_cache[cache_key]
        if time.time() - cached['timestamp'] < _CACHE_TTL:
            return cached['balance']
        else:
            del _balance_cache[cache_key]
    
    if chain not in CHAIN_CONFIG:
        raise ValueError(f"Unsupported chain: {chain}")

    config = CHAIN_CONFIG[chain]
    nodes = config["nodes"]
    decimals = config["decimals"]

    if chain == "TRON":
        api_key = config.get("api_key")
        headers = {"TRON-PRO-API-KEY": api_key} if api_key else {}
        for node in nodes:
            try:
                url = f"{node.rstrip('/')}/wallet/getaccount"
                data = {"address": address, "visible": True}
                res = requests.post(url, json=data, headers=headers, timeout=8)
                if res.status_code == 200:
                    result = res.json()
                    sun = result.get("balance", 0)
                    trx = int(sun) / 10**6
                    _balance_cache[cache_key] = {'balance': trx, 'timestamp': time.time()}
                    return trx
            except:
                continue
        raise Exception("All TRON nodes failed")
    else:
        for node in nodes:
            try:
                data = {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [address, "latest"], "id": 1}
                res = requests.post(node, json=data, timeout=8)
                if res.status_code == 200:
                    result = res.json()
                    wei = int(result["result"], 16)
                    balance = wei / 10**decimals
                    _balance_cache[cache_key] = {'balance': balance, 'timestamp': time.time()}
                    return balance
            except:
                continue
        raise Exception(f"All {chain} nodes failed")

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
        if self.mnemonic:
            self.private_key = self._mnemonic_to_private_key(self.mnemonic)
        
        if self.chain == "TRON":
            self._init_tron_wallet()
        else:
            self._init_evm_wallet()
    
    def _mnemonic_to_private_key(self, mnemonic_words, account_index=0):
        from mnemonic import Mnemonic
        from bip32utils import BIP32Key
        mnemo = Mnemonic("english")
        seed = mnemo.to_seed(mnemonic_words)
        HARDEN = 0x80000000
        
        if self.chain == "TRON":
            coin_type = 195
        else:
            coin_type = 60
        
        master_key = BIP32Key.fromEntropy(seed)
        child_key = master_key.ChildKey(44 + HARDEN).ChildKey(coin_type + HARDEN).ChildKey(account_index + HARDEN).ChildKey(0).ChildKey(0)
        return child_key.PrivateKey().hex()
    
    def _init_evm_wallet(self):
        from web3 import Web3
        self.web3 = Web3(Web3.HTTPProvider(self.rpc))
        
        if not self.private_key:
            from mnemonic import Mnemonic
            from bip32utils import BIP32Key
            mnemo = Mnemonic("english")
            self.mnemonic = mnemo.generate(128)
            seed = mnemo.to_seed(self.mnemonic)
            HARDEN = 0x80000000
            master_key = BIP32Key.fromEntropy(seed)
            child_key = master_key.ChildKey(44 + HARDEN).ChildKey(60 + HARDEN).ChildKey(0 + HARDEN).ChildKey(0).ChildKey(0)
            self.private_key = child_key.PrivateKey().hex()
        
        account = self.web3.eth.account.from_key(self.private_key)
        self.address = account.address
    
    def _init_tron_wallet(self):
        import ecdsa
        import base58
        
        if not self.private_key:
            from mnemonic import Mnemonic
            from bip32utils import BIP32Key
            mnemo = Mnemonic("english")
            self.mnemonic = mnemo.generate(128)
            seed = mnemo.to_seed(self.mnemonic)
            HARDEN = 0x80000000
            master_key = BIP32Key.fromEntropy(seed)
            child_key = master_key.ChildKey(44 + HARDEN).ChildKey(195 + HARDEN).ChildKey(0 + HARDEN).ChildKey(0).ChildKey(0)
            self.private_key = child_key.PrivateKey().hex()
        
        private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
        vk = private_key_obj.get_verifying_key()
        public_key = b"\x04" + vk.to_string()
        
        sha256 = hashlib.sha256(public_key).digest()
        h = RIPEMD160.new()
        h.update(sha256)
        ripemd = h.digest()
        address_bytes = b"\x41" + ripemd
        checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
        self.address = base58.b58encode(address_bytes + checksum).decode()
    
    def get_balance(self):
        return get_balance(self.chain, self.address)
    
    def transfer(self, to_address, amount):
        try:
            if self.chain == "TRON":
                return self._transfer_tron(to_address, amount)
            else:
                return self._transfer_evm(to_address, amount)
        except Exception as e:
            raise Exception(f"Transfer failed: {str(e)}")
    
    def _transfer_evm(self, to_address, amount):
        nonce = self.web3.eth.get_transaction_count(self.address)
        gas_price = self.web3.eth.gas_price
        chain_id = self.web3.eth.chain_id

        tx = {
            'nonce': nonce,
            'to': to_address,
            'value': self.web3.to_wei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': gas_price,
            'chainId': chain_id
        }

        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        return tx_hash.hex()
    
    def _transfer_tron(self, to_address, amount):
        from tronpy import Tron
        from tronpy.providers import HTTPProvider
        from tronpy.keys import PrivateKey
        
        self.tron_client = Tron(HTTPProvider(self.rpc))
        amount_sun = int(amount * 10**6)
        private_key_obj = PrivateKey(bytes.fromhex(self.private_key.strip()))
        
        txn = (
            self.tron_client.trx.transfer(self.address, to_address, amount_sun)
            .build()
            .sign(private_key_obj)
        )
        result = txn.broadcast()
        if result.get('result'):
            return result.get('txid')
        else:
            raise Exception(result.get('message', 'Broadcast failed'))
    
    def get_wallet_info(self):
        return {
            'chain': self.chain,
            'address': self.address,
            'private_key': self.private_key,
            'mnemonic': self.mnemonic,
            'rpc': self.rpc
        }

app = Flask(__name__)
CORS(app)

wallet_sessions = {}

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
        mnemonic = data['mnemonic'].strip()  # 去除首尾空格
        
        print(f'[DEBUG] 原始助记词 repr: {repr(data["mnemonic"])}')
        print(f'[DEBUG] strip后助记词 repr: {repr(mnemonic)}')
        
        # 打印种子用于调试
        from mnemonic import Mnemonic
        mnemo = Mnemonic("english")
        seed = mnemo.to_seed(mnemonic)
        print(f'[DEBUG] 种子 hex: {seed.hex()[:64]}')
        
        wallet = MultiChainWallet(chain=chain, mnemonic=mnemonic)
        info = wallet.get_wallet_info()
        
        # 打印详细信息
        print(f'[DEBUG] 私钥: {info["private_key"]}')
        print(f'[DEBUG] 地址: {info["address"]}')
        
        print(f'[DEBUG] 生成的地址: {info["address"]}')
        print(f'[DEBUG] 生成的私钥: {info["private_key"][:20]}...')
        
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

@app.route('/api/wallet/balance', methods=['POST'])
def query_balance():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if session_id and session_id in wallet_sessions:
            wallet = wallet_sessions[session_id]
            balance = wallet.get_balance()
        else:
            address = data['address']
            chain = data['chain']
            balance = get_balance(chain, address)
        
        return jsonify({'success': True, 'balance': float(balance)}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/wallet/transfer', methods=['POST'])
def transfer():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        to_address = data['to_address']
        amount = float(data['amount'])
        chain = data.get('chain')
        
        wallet = None
        
        # 优先使用session_id
        if session_id and session_id in wallet_sessions:
            wallet = wallet_sessions[session_id]
            # 检查chain是否匹配
            if chain and wallet.chain != chain:
                # chain不匹配，需要用私钥重新创建wallet
                wallet = None
        
        # 如果session无效或chain不匹配，用私钥创建临时wallet
        if wallet is None:
            private_key = data.get('private_key')
            mnemonic = data.get('mnemonic')
            
            if not chain:
                return jsonify({'success': False, 'message': 'Chain parameter is required'}), 400
            
            if private_key:
                wallet = MultiChainWallet(chain=chain, private_key=private_key)
            elif mnemonic:
                wallet = MultiChainWallet(chain=chain, mnemonic=mnemonic)
            else:
                return jsonify({'success': False, 'message': 'Session expired, please provide private_key or mnemonic'}), 400
        
        tx_hash = wallet.transfer(to_address, amount)
        
        return jsonify({'success': True, 'tx_hash': tx_hash}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/wallet/estimate_fee', methods=['POST'])
def estimate_fee():
    try:
        data = request.get_json()
        session_id = data['session_id']
        
        if session_id not in wallet_sessions:
            return jsonify({'success': False, 'message': 'Invalid session ID'}), 400
        
        wallet = wallet_sessions[session_id]
        
        if wallet.chain == 'TRON':
            return jsonify({'success': True, 'fee': 0.00345, 'symbol': 'TRX'}), 200
        else:
            gas_price = wallet.web3.eth.gas_price
            gas_limit = 21000
            fee_wei = gas_price * gas_limit
            fee = wallet.web3.from_wei(fee_wei, 'ether')
            symbol = 'BNB' if wallet.chain == 'BSC' else 'ETH'
            
            return jsonify({'success': True, 'fee': float(fee), 'symbol': symbol}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/wallet/backup', methods=['POST'])
def backup_wallet():
    try:
        data = request.get_json()
        address = data.get('address')
        chain = data.get('chain')
        encrypted_data = data.get('encrypted_data')
        
        # TODO: 实现云端备份逻辑
        # 目前返回成功，实际应该保存到数据库或文件
        
        return jsonify({
            'success': True,
            'backup_id': f"backup_{address}_{int(time.time())}",
            'message': 'Backup successful'
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'running', 'version': '1.0.0', 'message': 'Wallet API Service Running'}), 200

if __name__ == '__main__':
    try:
        print("=" * 50)
        print(" 启动钱包API服务")
        print("=" * 50)
        print(f"服务地址: http://0.0.0.0:5000")
        print(f"调试模式: {Config.DEBUG}")
        print("=" * 50)
        app.run(host='0.0.0.0', port=5000, debug=False)
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
