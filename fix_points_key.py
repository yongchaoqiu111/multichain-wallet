#!/usr/bin/env python3
with open('/root/qianbao/houduan/points_panel.py', 'r') as f:
    content = f.read()

content = content.replace(
    "SERVER_KEY = b'ServerWallet2026SecureKey32B!!!!'",
    "CLIENT_KEY = b'ClientWallet2026SecureKey32B!!!!'"
)
content = content.replace(
    "aesgcm = AESGCM(SERVER_KEY)",
    "aesgcm = AESGCM(CLIENT_KEY)"
)

with open('/root/qianbao/houduan/points_panel.py', 'w') as f:
    f.write(content)

print('✅ 修改完成：密钥改为CLIENT_KEY')
