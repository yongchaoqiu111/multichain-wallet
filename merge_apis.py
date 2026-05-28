#!/usr/bin/env python3
# 读取两个文件
with open('/root/wallet/server_backup.py', 'r') as f:
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

# 从mobile_wallet_api.py提取3个函数（234-323行）
mobile_routes = mobile_lines[233:323]  # 0-indexed, so 233=line 234

# 插入到if __name__之前
new_lines = server_lines[:main_pos] + ['\n# Mobile Wallet APIs\n'] + mobile_routes + ['\n'] + server_lines[main_pos:]

with open('/root/wallet/server.py', 'w') as f:
    f.writelines(new_lines)

print(f"Done! Added {len(mobile_routes)} lines from mobile_wallet_api.py")
