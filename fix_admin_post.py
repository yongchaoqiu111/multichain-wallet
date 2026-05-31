#!/usr/bin/env python3
with open('/root/qianbao/houduan/admin_page.py', 'r') as f:
    content = f.read()

content = content.replace(
    "list_response = requests.get(f'{SERVER_API}/api/wallet/list')",
    "list_response = requests.post(f'{SERVER_API}/api/wallet/list', json={})"
)

with open('/root/qianbao/houduan/admin_page.py', 'w') as f:
    f.write(content)

print('修改完成：admin_page现在使用POST请求调用API')
