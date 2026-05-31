import re
with open('/root/wallet/modules/wallet_core.py', 'r') as f:
    content = f.read()
if 'from Crypto.Hash import RIPEMD160' not in content:
    content = content.replace('import hashlib', 'import hashlib\nfrom Crypto.Hash import RIPEMD160')
content = content.replace(
    \"ripemd = hashlib.new('ripemd160', sha256).digest()\",
    \"h = RIPEMD160.new()\\n            h.update(sha256)\\n            ripemd = h.digest()\"
)
with open('/root/wallet/modules/wallet_core.py', 'w') as f:
    f.write(content)
print('Fixed!')
