from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib
import ecdsa
import base58
import uuid
import binascii

from Crypto.Hash import RIPEMD160

app = Flask(__name__)
CORS(app)

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'success': True, 'message': 'Wallet API is running'})

@app.route('/api/wallet/create', methods=['POST'])
def create_wallet():
    try:
        private_key = binascii.hexlify(uuid.uuid4().bytes).decode()[:64]
        
        private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
        vk = private_key_obj.get_verifying_key()
        public_key = b"\x04" + vk.to_string()
        
        sha256 = hashlib.sha256(public_key).digest()
        h = RIPEMD160.new()
        h.update(sha256)
        ripemd = h.digest()
        
        address_bytes = b"\x41" + ripemd
        checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
        address = base58.b58encode(address_bytes + checksum).decode()
        
        return jsonify({
            'success': True,
            'data': {
                'private_key': private_key,
                'address': address
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
