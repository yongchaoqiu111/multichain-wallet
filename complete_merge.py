#!/usr/bin/env python3
# 完整合并脚本：houduan/server.py + mobile_wallet_api.py的MultiChainWallet类和3个移动端接口

with open('/root/wallet/server_final.py', 'r') as f:
    server_lines = f.readlines()

with open('/root/wallet/mobile_wallet_api.py', 'r') as f:
    mobile_lines = f.readlines()

# 找到if __name__在server_backup.py中的位置
main_pos = None
for i, line in enumerate(server_lines):
    if "if __name__" in line:
        main_pos = i
        break

if not main_pos:
    print("Error: if __name__ not found")
    exit(1)

# 从mobile_wallet_api.py提取：
# 1. MultiChainWallet类 (87-227行)
# 2. 3个移动端接口 (234-323行)
wallet_class = mobile_lines[86:227]  # line 87-227 (0-indexed)
mobile_routes = mobile_lines[233:323]  # line 234-323

# 插入顺序：先MultiChainWallet类（在文件开头附近），再移动端接口（在if __name__之前）
# 找到load_api_key函数结束的位置（return 'ai-wallet-query-2026'之后）
insert_class_pos = None
for i, line in enumerate(server_lines[:100]):
    if "return 'ai-wallet-query-2026'" in line:
        insert_class_pos = i + 1  # 在这一行之后插入
        break

if not insert_class_pos:
    print("Error: Could not find insertion point for MultiChainWallet class")
    exit(1)

# 构建新文件
new_lines = (
    server_lines[:insert_class_pos] + 
    ['\n'] + 
    wallet_class + 
    ['\n'] +
    server_lines[insert_class_pos:main_pos] +
    ['\n# Mobile Wallet APIs\n'] +
    mobile_routes +
    ['\n'] +
    server_lines[main_pos:]
)

with open('/root/wallet/server.py', 'w') as f:
    f.writelines(new_lines)

print(f"Done! Merged {len(wallet_class)} lines (MultiChainWallet) + {len(mobile_routes)} lines (mobile routes)")
