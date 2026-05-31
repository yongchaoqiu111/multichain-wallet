#!/usr/bin/env python3

file_path = '/root/wallet/wallet_api_service.py'

with open(file_path, 'r') as f:
    content = f.read()

# 修复 API 路由：添加 token 参数传递
old_call = '''            address = data['address']
            chain = data['chain']
            balance = get_balance(chain, address)'''

new_call = '''            address = data['address']
            chain = data['chain']
            token = data.get('token', '')  # 获取 token 参数
            balance = get_balance(chain, address, token if token else None)'''

content = content.replace(old_call, new_call)

with open(file_path, 'w') as f:
    f.write(content)

print('✅ 已修复 API 路由传递 token 参数')
