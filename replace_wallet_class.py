#!/usr/bin/env python3
# 用标准HD钱包替换server.py中的MultiChainWallet类

with open('/root/wallet/server.py', 'r') as f:
    server_lines = f.readlines()

with open('/root/wallet/wallet_core.py', 'r') as f:
    wallet_core_lines = f.readlines()

# 找到MultiChainWallet类的开始和结束位置
class_start = None
class_end = None
for i, line in enumerate(server_lines):
    if 'class MultiChainWallet:' in line:
        class_start = i
    if class_start is not None and class_end is None:
        # 找到下一个class定义或if __name__
        if (line.startswith('class ') and i > class_start) or line.strip().startswith('if __name__'):
            class_end = i
            break

if class_start is None:
    print("Error: MultiChainWallet class not found")
    exit(1)

if class_end is None:
    class_end = len(server_lines)

print(f"Found MultiChainWallet from line {class_start+1} to {class_end}")

# 提取wallet_core.py中的MultiChainWallet类（从第180行开始）
new_class_lines = []
in_class = False
for line in wallet_core_lines:
    if 'class MultiChainWallet:' in line:
        in_class = True
    if in_class:
        new_class_lines.append(line)

print(f"Extracted {len(new_class_lines)} lines from wallet_core.py")

# 替换：保留MultiChainWallet之前的内容 + 新类 + MultiChainWallet之后的内容
new_server_lines = server_lines[:class_start] + new_class_lines + server_lines[class_end:]

with open('/root/wallet/server.py', 'w') as f:
    f.writelines(new_server_lines)

print("Done! Replaced MultiChainWallet with standard HD wallet implementation")
