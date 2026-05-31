import hashlib
import base58
import ecdsa
from Crypto.Hash import RIPEMD160

private_key = 'e361ecc51ac8801eb4af90ba668f8a62bc1ef1b5af00248eb3ea4adb7bd9df88'

# 方法1: ecdsa + hashlib
private_key_obj1 = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
vk1 = private_key_obj1.get_verifying_key()
public_key1 = b'\x04' + vk1.to_string()
sha256_1 = hashlib.sha256(public_key1).digest()
ripemd1 = hashlib.new('ripemd160', sha256_1).digest()
addr1 = base58.b58encode(b'\x41' + ripemd1 + hashlib.sha256(hashlib.sha256(b'\x41' + ripemd1).digest()).digest()[:4]).decode()

print(f'ecdsa 公钥 hex: {public_key1.hex()[:66]}')
print(f'ecdsa ripemd: {ripemd1.hex()}')
print(f'ecdsa 地址: {addr1}')

# 方法2: tronpy
try:
    from tronpy.keys import PrivateKey
    private_key_obj2 = PrivateKey(bytes.fromhex(private_key))
    addr2 = private_key_obj2.public_key.to_base58check_address()
    print(f'tronpy 公钥 hex: {private_key_obj2.public_key.to_bytes().hex()[:66]}')
    print(f'tronpy 地址: {addr2}')
except ImportError:
    print('tronpy not available')
