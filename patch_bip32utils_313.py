#!/usr/bin/env python3
import sys

bip32utils_path = '/opt/python3.13/lib/python3.13/site-packages/bip32utils/BIP32Key.py'

with open(bip32utils_path, 'r') as f:
    content = f.read()

if 'from Crypto.Hash import RIPEMD160' not in content:
    content = content.replace(
        'import hashlib',
        'import hashlib\nfrom Crypto.Hash import RIPEMD160'
    )

content = content.replace(
    "hashlib.new('ripemd160', sha256(cK).digest()).digest()",
    "RIPEMD160.new(sha256(cK).digest()).digest()"
)

content = content.replace(
    "hashlib.new('ripemd160', sha256(pk_bytes).digest()).digest()",
    "RIPEMD160.new(sha256(pk_bytes).digest()).digest()"
)

content = content.replace(
    "hashlib.new('ripemd160', sha256(script_sig).digest()).digest()",
    "RIPEMD160.new(sha256(script_sig).digest()).digest()"
)

with open(bip32utils_path, 'w') as f:
    f.write(content)

print('Python 3.13 bip32utils patched successfully!')
