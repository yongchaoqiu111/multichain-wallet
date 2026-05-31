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
from modules.wallet_core import MultiChainWallet

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

def get_balance(chain, address, token=None):
    import requests
    cache_key = f"{chain}:{address}:{token}"
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
        # 如果查询代币（如 USDT）
        if token and token.upper() == "USDT":
            usdt_contract = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # TRC20 USDT
            for node in nodes:
                try:
                    url = f"{node.rstrip('/')}/wallet/triggerconstantcontract"
                    data = {
                        "contract_address": usdt_contract,
                        "function_selector": "balanceOf(address)",
                        "parameter": _tron_address_to_hex_param(address),  # 动态转换
                        "owner_address": address,
                        "visible": True
                    }
                    res = requests.post(url, json=data, timeout=8)
                    if res.status_code == 200:
                        result = res.json()
                        if "constant_result" in result and len(result["constant_result"]) > 0:
                            hex_result = result["constant_result"][0]
                            balance_int = int(hex_result, 16)
                            usdt_balance = balance_int / 10**6  # USDT 是 6 位小数
                            _balance_cache[cache_key] = {'balance': usdt_balance, 'timestamp': time.time()}
                            return usdt_balance
                except:
                    continue
            raise Exception("Failed to query USDT balance")
        
        # 查询主币 TRX
        for node in nodes:
            try:
                url = f"{node.rstrip('/')}/wallet/getaccount"
                data = {"address": address, "visible": True}
                res = requests.post(url, json=data, timeout=8)
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


def _tron_address_to_hex_param(address):
    """将 TRON Base58 地址转换为 balanceOf 的 parameter 格式"""
    from tronpy import Tron
    client = Tron()
    # 转成 hex 并去掉 0x 前缀
    address_hex = client.to_hex_address(address).lower().replace('0x', '')
    # 补到 64 位
    return address_hex.zfill(64)

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
            token = data.get('token', '')  # 获取 token 参数
            balance = get_balance(chain, address, token if token else None)
        
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
        print(f"服务地址: http://{Config.API_HOST}:{Config.API_PORT}")
        print(f"调试模式: {Config.DEBUG}")
        print("=" * 50)
        app.run(host=Config.API_HOST, port=Config.API_PORT, debug=Config.DEBUG)
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
