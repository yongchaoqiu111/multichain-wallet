#!/usr/bin/env python3

file_path = '/root/wallet/wallet_api_service.py'

with open(file_path, 'r') as f:
    lines = f.readlines()

# 找到 balance 路由并修改
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # 在 get_balance 调用前添加 token 处理
    if 'balance = get_balance(chain, address)' in line:
        indent = len(line) - len(line.lstrip())
        indent_str = ' ' * indent
        
        # 添加 token 参数处理
        new_lines.append(indent_str + 'token = data.get("token", "")  # 默认空字符串表示查询主币\n')
        new_lines.append(indent_str + 'balance = get_balance(chain, address, token=token if token else None)\n')
        i += 1
        continue
    
    new_lines.append(line)
    i += 1

with open(file_path, 'w') as f:
    f.writelines(new_lines)

print('已修改服务器 API 支持 token 参数')
