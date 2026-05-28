"""
钱包核心API服务 - 供Flutter移动端/Web调用
端口: 5001
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import sys

# 添加modules路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

try:
    from modules.wallet_core import MultiChainWallet, get_balance
    from modules.config import Config
except Exception as e:
    print(f"导入错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

app = Flask(__name__)
CORS(app)

# 存储活跃的钱包会话
wallet_sessions = {}

@app.route('/api/wallet/create', methods=['POST'])
def create_wallet():
    """创建新钱包"""
    try:
        data = request.get_json()
        chain = data.get('chain', 'TRON')
        
        wallet = MultiChainWallet(chain=chain)
        info = wallet.get_wallet_info()
        
        import hashlib
        import time
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
    """私钥导入"""
    try:
        data = request.get_json()
        chain = data.get('chain', 'TRON')
        private_key = data['private_key']
        
        wallet = MultiChainWallet(chain=chain, private_key=private_key)
        info = wallet.get_wallet_info()
        
        import hashlib
        import time
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
    """助记词导入"""
    try:
        data = request.get_json()
        chain = data.get('chain', 'TRON')
        mnemonic = data['mnemonic']
        
        wallet = MultiChainWallet(chain=chain, mnemonic=mnemonic)
        info = wallet.get_wallet_info()
        
        import hashlib
        import time
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

@app.route('/api/wallet/balance', methods=['POST'])
def query_balance():
    """查询余额"""
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
        
        return jsonify({
            'success': True,
            'balance': float(balance)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/wallet/transfer', methods=['POST'])
def transfer():
    """转账"""
    try:
        data = request.get_json()
        session_id = data['session_id']
        to_address = data['to_address']
        amount = float(data['amount'])
        
        if session_id not in wallet_sessions:
            return jsonify({'success': False, 'message': '无效的会话ID'}), 400
        
        wallet = wallet_sessions[session_id]
        tx_hash = wallet.transfer(to_address, amount)
        
        return jsonify({
            'success': True,
            'tx_hash': tx_hash
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/wallet/estimate_fee', methods=['POST'])
def estimate_fee():
    """估算矿工费"""
    try:
        data = request.get_json()
        session_id = data['session_id']
        
        if session_id not in wallet_sessions:
            return jsonify({'success': False, 'message': '无效的会话ID'}), 400
        
        wallet = wallet_sessions[session_id]
        
        if wallet.chain == 'TRON':
            fee_info = wallet.estimate_tron_fee()
            return jsonify({
                'success': True,
                'fee': fee_info.get('fee_trx', 0.00345),
                'symbol': 'TRX'
            }), 200
        else:
            gas_price = wallet.web3.eth.gas_price
            gas_limit = 21000
            fee_wei = gas_price * gas_limit
            fee = wallet.web3.from_wei(fee_wei, 'ether')
            symbol = 'BNB' if wallet.chain == 'BSC' else 'ETH'
            
            return jsonify({
                'success': True,
                'fee': float(fee),
                'symbol': symbol
            }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/wallet/derive_address', methods=['POST'])
def derive_address():
    """从助记词派生地址"""
    try:
        data = request.get_json()
        mnemonic = data['mnemonic']
        chain = data.get('chain', 'TRON')
        account_index = data.get('account_index', 0)
        
        wallet = MultiChainWallet(chain=chain, mnemonic=mnemonic)
        addr_info = wallet.derive_address(account_index)
        
        return jsonify({
            'success': True,
            'address': addr_info['address'],
            'index': addr_info['index']
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'running',
        'version': '1.0.0',
        'message': '钱包API服务运行中'
    }), 200

if __name__ == '__main__':
    print("="*50)
    print(" 钱包核心API服务启动")
    print(f"📡 服务地址: http://{Config.API_HOST}:{Config.API_PORT}")
    print(f"🌐 对外地址: {Config.get_api_base_url()}")
    print("="*50)
    app.run(host=Config.API_HOST, port=Config.API_PORT, debug=Config.DEBUG)
