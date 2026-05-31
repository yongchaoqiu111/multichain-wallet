import requests

def create_api_file():
    api_code = """
from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import time
import requests

app = Flask(__name__)
CORS(app)

CHAIN_CONFIG = {
    "ETH": {"nodes": ["https://eth.llamarpc.com"], "decimals": 18},
    "BSC": {"nodes": ["https://bsc-rpc.publicnode.com"], "decimals": 18},
    "TRON": {"nodes": ["https://api.trongrid.io"], "decimals": 6}
}

wallet_sessions = {}

def get_balance(chain, address):
    if chain not in CHAIN_CONFIG:
        raise ValueError("Unsupported chain")
    cfg = CHAIN_CONFIG[chain]
    for node in cfg["nodes"]:
        try:
            if chain == "TRON":
                res = requests.post(f"{node}/wallet/getaccount", json={"address": address, "visible": True}, timeout=8)
                if res.status_code == 200:
                    return int(res.json().get("balance", 0)) / 10**6
            else:
                res = requests.post(node, json={"jsonrpc": "2.0", "method": "eth_getBalance", "params": [address, "latest"], "id": 1}, timeout=8)
                if res.status_code == 200:
                    return int(res.json()["result"], 16) / 10**cfg["decimals"]
        except:
            continue
    raise Exception(f"{chain} nodes failed")

@app.route('/api/wallet/create', methods=['POST'])
def create_wallet():
    try:
        data = request.get_json()
        chain = data.get('chain', 'TRON')
        from mnemonic import Mnemonic
        from bip32utils import BIP32Key
        import ecdsa
        import base58
        
        mnemo = Mnemonic("english")
        mnemonic = mnemo.generate(128)
        seed = mnemo.to_seed(mnemonic)
        HARDEN = 0x80000000
        coin_type = 195 if chain == "TRON" else 60
        
        master = BIP32Key.fromEntropy(seed)
        child = master.ChildKey(44 + HARDEN).ChildKey(coin_type + HARDEN).ChildKey(0 + HARDEN).ChildKey(0).ChildKey(0)
        pk = child.PrivateKey().hex()
        
        if chain == "TRON":
            pk_obj = ecdsa.SigningKey.from_string(bytes.fromhex(pk), curve=ecdsa.SECP256k1)
            vk = pk_obj.get_verifying_key()
            pub = b"\\x04" + vk.to_string()
            sha = hashlib.sha256(pub).digest()
            ripemd = hashlib.new('ripemd160', sha).digest()
            addr = b"\\x41" + ripemd
            checksum = hashlib.sha256(hashlib.sha256(addr).digest()).digest()[:4]
            address = base58.b58encode(addr + checksum).decode()
        else:
            from web3 import Web3
            address = Web3().eth.account.from_key(pk).address
        
        sid = hashlib.md5(f"{address}_{time.time()}".encode()).hexdigest()
        wallet_sessions[sid] = {"pk": pk, "addr": address, "chain": chain, "mnemonic": mnemonic}
        return jsonify({"success": True, "session_id": sid, "address": address, "mnemonic": mnemonic, "chain": chain})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/wallet/import/private_key', methods=['POST'])
def import_pk():
    try:
        data = request.get_json()
        chain = data.get('chain', 'TRON')
        pk = data['private_key']
        import ecdsa
        import base58
        
        if chain == "TRON":
            pk_obj = ecdsa.SigningKey.from_string(bytes.fromhex(pk), curve=ecdsa.SECP256k1)
            vk = pk_obj.get_verifying_key()
            pub = b"\\x04" + vk.to_string()
            sha = hashlib.sha256(pub).digest()
            ripemd = hashlib.new('ripemd160', sha).digest()
            addr = b"\\x41" + ripemd
            checksum = hashlib.sha256(hashlib.sha256(addr).digest()).digest()[:4]
            address = base58.b58encode(addr + checksum).decode()
        else:
            from web3 import Web3
            address = Web3().eth.account.from_key(pk).address
        
        sid = hashlib.md5(f"{address}_{time.time()}".encode()).hexdigest()
        wallet_sessions[sid] = {"pk": pk, "addr": address, "chain": chain}
        return jsonify({"success": True, "session_id": sid, "address": address, "chain": chain})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/api/wallet/import/mnemonic', methods=['POST'])
def import_mnemonic():
    try:
        data = request.get_json()
        chain = data.get('chain', 'TRON')
        mnemonic = data['mnemonic']
        from mnemonic import Mnemonic
        from bip32utils import BIP32Key
        import ecdsa
        import base58
        
        seed = Mnemonic("english").to_seed(mnemonic)
        HARDEN = 0x80000000
        coin_type = 195 if chain == "TRON" else 60
        
        master = BIP32Key.fromEntropy(seed)
        child = master.ChildKey(44 + HARDEN).ChildKey(coin_type + HARDEN).ChildKey(0 + HARDEN).ChildKey(0).ChildKey(0)
        pk = child.PrivateKey().hex()
        
        if chain == "TRON":
            pk