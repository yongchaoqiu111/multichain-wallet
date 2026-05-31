#!/usr/bin/env python3
# 正确替换：只替换MultiChainWallet类，保留后面所有接口

with open('/root/wallet/server.py', 'r') as f:
    server_lines = f.readlines()

with open('/root/wallet/wallet_core.py', 'r') as f:
    wallet_core_lines = f.readlines()

# 找到MultiChainWallet类的开始位置
class_start = None
for i, line in enumerate(server_lines):
    if 'class MultiChainWallet:' in line:
        class_start = i
        break

if class_start is None:
    print("Error: MultiChainWallet class not found")
    exit(1)

# 找到wallet_sessions = {}的位置（这是mobile APIs开始的标志）
wallet_sessions_pos = None
for i, line in enumerate(server_lines):
    if 'wallet_sessions = {}' in line:
        wallet_sessions_pos = i
        break

if wallet_sessions_pos is None:
    print("Error: wallet_sessions not found")
    exit(1)

print(f"Found MultiChainWallet at line {class_start+1}")
print(f"Found wallet_sessions at line {wallet_sessions_pos+1}")

# 提取wallet_core.py中的MultiChainWallet类
new_class_lines = []
in_class = False
for line in wallet_core_lines:
    if 'class MultiChainWallet:' in line:
        in_class = True
    if in_class:
        new_class_lines.append(line)

print(f"Extracted {len(new_class_lines)} lines from wallet_core.py")

# 组合：MultiChainWallet之前 + 新类 + wallet_sessions及之后
new_server_lines = server_lines[:class_start] + new_class_lines + ['\n'] + server_lines[wallet_sessions_pos:]

with open('/root/wallet/server.py', 'w') as f:
    f.writelines(new_server_lines)

print("Done! Replaced only MultiChainWallet class, kept all API routes")
