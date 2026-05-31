with open('/root/wallet/modules/wallet_core.py', 'r', errors='ignore') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if line.strip() == 'h.update(sha256)':
        lines[i] = '            h.update(sha256)\n'
    elif line.strip() == 'ripemd = h.digest()':
        lines[i] = '            ripemd = h.digest()\n'

with open('/root/wallet/modules/wallet_core.py', 'w') as f:
    f.writelines(lines)

print('Fixed indentation!')
