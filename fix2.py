with open('/root/wallet/modules/wallet_core.py', 'r') as f:
    content = f.read()

content = content.replace(
    'ripemd = RIPEMD160.new(sha256).digest()',
    'h = RIPEMD160.new()\nh.update(sha256)\nripemd = h.digest()'
)

with open('/root/wallet/modules/wallet_core.py', 'w') as f:
    f.write(content)

print('Fixed!')
