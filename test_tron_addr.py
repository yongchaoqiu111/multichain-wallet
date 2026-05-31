#!/usr/bin/env python3
import hashlib
import base58
import ecdsa
from Crypto.Hash import RIPEMD160

private_key = 'e361ecc51ac8801eb4af90ba668f8a62bc1ef1b5af00248eb3ea4adb7bd9df88'
private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
vk = private_key_obj.get_verifying_key()
public_key = b'\x04' + vk.to_string()

sha256 = hashlib.sha256(public_key).digest()
ripemd = RIPEMD160.new(sha256).digest()
address_bytes = b'\x41' + ripemd

checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
address = base58.b58encode(address_bytes + checksum).decode()

print(f'公钥 hex: {public_key.hex()}')
print(f'SHA256: {sha256.hex()}')
print(f'RIPEMD160: {ripemd.hex()}')
print(f'地址: {address}')
