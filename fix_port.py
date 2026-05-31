import re

with open('/root/wallet/wallet_api_service.py', 'r') as f:
    content = f.read()

content = re.sub(r"BACKUP_PORT',\s*\d+", "BACKUP_PORT', 5000", content)

with open('/root/wallet/wallet_api_service.py', 'w') as f:
    f.write(content)

print('端口已改为 5000')
