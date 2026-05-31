#!/usr/bin/env python3

file_path = '/root/wallet/wallet_api_service.py'

with open(file_path, 'r') as f:
    content = f.read()

# 替换错误的 API 调用
content = content.replace(
    '/wallet/triggersmartcontract',
    '/wallet/triggerconstantcontract'
)

with open(file_path, 'w') as f:
    f.write(content)

print('✅ 已修正 API 调用为 triggerconstantcontract')
