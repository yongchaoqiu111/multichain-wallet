import subprocess
import base64

api_code = """
from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import time
import requests

app = Flask(__name__)
CORS(app)

CHAIN_CONFIG = {
    "ETH": {"coin_type": 60, "decimals": 18, "nodes": ["https://eth.llamarpc.com"]},
    "BSC": {"coin_type": 60, "decimals": 18, "nodes": ["https://bsc-rpc.publicnode.com"]},
    "TRON": {"coin_type": 195, "decimals": 6, "nodes": ["https://api.trongrid.io"]}
}

wallet_sessions = {}

def get_balance(chain, address):
    if chain not in CHAIN_CONFIG:
        raise ValueError("Unsupported chain")
    config = CHAIN_CONFIG[chain]
    nodes = config["nodes"]
    decimals = config["decimals"]
    
    if chain == "TRON":
        for node in nodes:
            try:
                url = node.rstrip("/") + "/wallet/getaccount"
                data = {"address": address, "visible": True}
                res = requests.post(url, json=data, timeout=8)
                if res.status_code == 200:
                    result = res.json()
                    sun = result.get("balance", 0)
                    return int(sun) / 10**6
            except:
                continue
        raise Exception("TRON nodes failed")
    else:
        for node in nodes:
            try:
                data = {"jsonrpc": "2.0", "method": "eth_getBalance", "params": [address, "latest"], "id": 1}
                res = requests.post(node, json=data, timeout=8)
                if res.status_code == 200:
                    result = res.json()
                    wei = int(result["result"], 16)
                    return wei / 10**decimals
            except:
                continue
        raise Exception(chain + " nodes failed")

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
        
        master_key = BIP32Key.fromEntropy(seed)
        child_key = master_key.ChildKey(44 + HARDEN).ChildKey(coin_type + HARDEN).ChildKey(0 + HARDEN).ChildKey(0).ChildKey(0)
        private_key = child_key.PrivateKey().hex()
        
        if chain == "TRON":
            pk_obj = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
            vk = pk_obj.get_verifying_key()
            pub_key = b"\\x04" + vk.to_string()
            sha256_val = hashlib.sha256(pub_key).digest()
            ripemd_val = hashlib.new('ripemd160', sha256_val).digest()
            addr_bytes = b"\\x41" + ripemd_val
            checksum = hashlib.sha256(hashlib.sha256(addr_bytes).digest()).digest()[:4]
            address = base58.b58encode(addr_bytes + checksum).decode()
        else:
            from web3 import Web3
            w3 = Web3()
            account = w3.eth.account.from_key(private_key)
            address = account.address
        
        session_id = hashlib.md5((address + "_" + str(time.time())).encode()).hexdigest()
        wallet_sessions[session_id] = {"private_key": private_key, "address": address, "chain": chain, "mnemonic": mnemonic}
        
        return jsonify({"success": True, "session_id": session_id, "address": address, "mnemonic": mnemonic, "chain": chain}), 200
    except Exception as e:
