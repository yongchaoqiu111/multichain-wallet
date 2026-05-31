import base64
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

# 模拟移动端加密
CLIENT_KEY = b'ClientWallet2026SecureKey32B!!!!'
wallet_data = {
    'private_key': 'test_private_key_123',
    'mnemonic': 'test mnemonic words here',
    'address': 'TTestBackup123'
}

# 加密
wallet_json = json.dumps(wallet_data, ensure_ascii=False).encode('utf-8')
aesgcm = AESGCM(CLIENT_KEY)
nonce = os.urandom(12)
ciphertext = aesgcm.encrypt(nonce, wallet_json, None)
encrypted_data = base64.b64encode(nonce + ciphertext).decode('utf-8')

print(f"Encrypted data: {encrypted_data}")
