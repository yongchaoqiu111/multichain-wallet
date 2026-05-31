#!/usr/bin/env python3
with open('/root/qianbao/houduan/admin_page.py', 'r') as f:
    content = f.read()

content = content.replace(
    "requests.get(f'{SERVER_API}/api/wallet/list')",
    "requests.post(f'{SERVER_API}/api/wallet/list', json={}, headers={'Content-Type': 'application/json'})"
)

with open('/root/qianbao/houduan/admin_page.py', 'w') as f:
    f.write(content)

print('修改完成')
