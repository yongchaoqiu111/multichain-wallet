from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import ecdsa
import base58
import hmac

from Crypto.Hash import RIPEMD160

app = Flask(__name__)
CORS(app)

def mnemonic_to_seed(mnemonic, passphrase=""):
    mnemonic = mnemonic.strip()
    salt = "mnemonic" + passphrase
    h = hashlib.pbkdf2_hmac("sha512", mnemonic.encode("utf-8"), salt.encode("utf-8"), 2048)
    return h[:64]

def derive_key(seed, path):
    parts = path.split('/')[1:]
    key = b'\x04\x88\xAD\xE4' + b'\x00' * 9 + seed
    chain_code = key[32:]
    key = key[:32]
    
    for part in parts:
        hardened = part.endswith("'")
        index = int(part[:-1]) if hardened else int(part)
        
        if hardened:
            data = b'\x00' + key + index.to_bytes(4, 'big')
        else:
            key_obj = ecdsa.SigningKey.from_string(key, curve=ecdsa.SECP256k1)
            vk = key_obj.get_verifying_key()
            data = b'\x04' + vk.to_string() + index.to_bytes(4, 'big')
        
        hmac_result = hmac.new(chain_code, data, hashlib.sha512).digest()
        key = (int.from_bytes(hmac_result[:32], 'big') + int.from_bytes(key, 'big')) % ecdsa.SECP256k1.order
        key = key.to_bytes(32, 'big')
        chain_code = hmac_result[32:]
    
    return key

def private_key_to_address(private_key):
    private_key_obj = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    vk = private_key_obj.get_verifying_key()
    public_key = b"\x04" + vk.to_string()
    
    sha256 = hashlib.sha256(public_key).digest()
    h = RIPEMD160.new()
    h.update(sha256)
    ripemd = h.digest()
    
    address_bytes = b"\x41" + ripemd
    checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
    address = base58.b58encode(address_bytes + checksum).decode()
    
    return address

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'success': True, 'message': 'Wallet API is running'})

@app.route('/api/wallet/create', methods=['POST'])
def create_wallet():
    try:
        from mnemonic import Mnemonic
        mnemo = Mnemonic("english")
        mnemonic = mnemo.generate(strength=128)
        
        seed = mnemonic_to_seed(mnemonic)
        private_key = derive_key(seed, "m/44'/195'/0'/0/0")
        address = private_key_to_address(private_key)
        
        return jsonify({
            'success': True,
            'data': {
                'mnemonic': mnemonic,
                'private_key': private_key.hex(),
                'address': address
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/wallet/import/mnemonic', methods=['POST'])
def import_mnemonic():
    try:
        data = request.json
        mnemonic = data.get('mnemonic')
        
        seed = mnemonic_to_seed(mnemonic)
        private_key = derive_key(seed, "m/44'/195'/0'/0/0")
        address = private_key_to_address(private_key)
        
        return jsonify({
            'success': True,
            'data': {
                'private_key': private_key.hex(),
                'address': address
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/wallet/import/private_key', methods=['POST'])
def import_private_key():
    try:
        data = request.json
        private_key_hex = data.get('private_key')
        private_key = bytes.fromhex(private_key_hex)
        
        address = private_key_to_address(private_key)
        
        return jsonify({
            'success': True,
            'data': {
                'address': address
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
