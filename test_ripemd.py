import hashlib
import base58
import ecdsa
from Crypto.Hash import RIPEMD160

private_key = 'e361ecc51ac8801eb4af90ba668f8a62bc1ef1b5af00248eb3ea4adb7bd9df88'
private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
vk = private_key_obj.get_verifying_key()
public_key = b'\x04' + vk.to_string()

sha256 = hashlib.sha256(public_key).digest()

ripemd1 = hashlib.new('ripemd160', sha256).digest()
addr1 = base58.b58encode(b'\x41' + ripemd1 + hashlib.sha256(hashlib.sha256(b'\x41' + ripemd1).digest()).digest()[:4]).decode()

ripemd2 = RIPEMD160.new(sha256).digest()
addr2 = base58.b58encode(b'\x41' + ripemd2 + hashlib.sha256(hashlib.sha256(b'\x41' + ripemd2).digest()).digest()[:4]).decode()

print(f'hashlib ripemd: {ripemd1.hex()}')
print(f'Crypto ripemd:  {ripemd2.hex()}')
print(f'hashlib 地址: {addr1}')
print(f'Crypto 地址:  {addr2}')
