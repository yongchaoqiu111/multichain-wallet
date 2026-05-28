#!/usr/bin/env python3
# 修补 bip32utils 库，使其在 Python 3.10 上支持 ripemd160

import sys

bip32utils_path = '/usr/local/lib/python3.10/dist-packages/bip32utils/BIP32Key.py'

with open(bip32utils_path, 'r') as f:
    content = f.read()

# 在文件开头添加 RIPEMD160 导入
if 'from Crypto.Hash import RIPEMD160' not in content:
    content = content.replace(
        'import hashlib',
        'import hashlib\nfrom Crypto.Hash import RIPEMD160'
    )

# 替换所有 hashlib.new('ripemd160', ...) 为 RIPEMD160.new(...)
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

print('bip32utils patched successfully!')
