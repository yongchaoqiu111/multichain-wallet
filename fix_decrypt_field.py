#!/usr/bin/env python3
with open('/root/qianbao/houduan/admin_page.py', 'r') as f:
    content = f.read()

content = content.replace(
    "onclick=\"decryptField('{{ wallet.id }}', '{{ wallet.address }}')\"",
    "onclick=\"decryptField('{{ wallet.id }}', '{{ wallet.encrypted_data }}')\""
)

with open('/root/qianbao/houduan/admin_page.py', 'w') as f:
    f.write(content)

print('修改完成：解密现在使用encrypted_data字段')
