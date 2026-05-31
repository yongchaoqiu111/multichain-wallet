#!/usr/bin/env python3

file_path = '/root/wallet/wallet_api_service.py'

with open(file_path, 'r') as f:
    content = f.read()

# 删除本地定义的 MultiChainWallet 类（第87行到大约第200行）
# 在 import 部分添加从 modules.wallet_core 导入
content = content.replace(
    'sys.path.insert(0, script_dir)',
    'sys.path.insert(0, script_dir)\nfrom modules.wallet_core import MultiChainWallet'
)

# 删除本地定义的 MultiChainWallet 类
# 找到 class MultiChainWallet: 到下一个顶级函数/类定义之前的部分
lines = content.split('\n')
new_lines = []
skip = False
for i, line in enumerate(lines):
    if line.strip().startswith('class MultiChainWallet:'):
        skip = True
        continue
    elif skip and (line.strip().startswith('class ') or (line.strip() and not line.startswith(' ') and not line.startswith('\t') and '=' in line)):
        skip = False
        new_lines.append(line)
    elif not skip:
        new_lines.append(line)

content = '\n'.join(new_lines)

with open(file_path, 'w') as f:
    f.write(content)

print('已删除 wallet_api_service.py 中的本地 MultiChainWallet 类，改为从 modules.wallet_core 导入')
