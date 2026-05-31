#!/usr/bin/env python3
with open('/root/wallet/server_merged.py', 'r') as f:
    lines = f.readlines()

# 找到if __name__和create_wallet的位置
main_idx = None
create_idx = None
for i, line in enumerate(lines):
    if 'if __name__' in line and main_idx is None:
        main_idx = i
    if 'def create_wallet' in line:
        create_idx = i

if not main_idx or not create_idx:
    print("Error")
    exit(1)

print(f"if __name__ at line {main_idx+1}, create_wallet at line {create_idx+1}")

# 提取mobile APIs部分（从create_wallet到if __name__之前）
mobile_part = lines[create_idx:main_idx]

# 重新组合：if __name__之前的内容 + mobile APIs + if __name__及之后
new_lines = lines[:create_idx] + mobile_part + lines[main_idx:]

with open('/root/wallet/server_merged.py', 'w') as f:
    f.writelines(new_lines)

print("Fixed!")
