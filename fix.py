with open('/root/wallet/modules/wallet_core.py', 'r') as f:
    content = f.read()
content = content.replace(
    \"hashlib.new('ripemd160', sha256).digest()\",
    \"h = RIPEMD160.new(); h.update(sha256); ripemd = h.digest()\"
)
with open('/root/wallet/modules/wallet_core.py', 'w') as f:
    f.write(content)
print('Fixed!')
