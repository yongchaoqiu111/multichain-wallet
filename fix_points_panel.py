#!/usr/bin/env python3
import os

# 修改本地文件
local_file = r'F:\houduan\points_panel.py'
if os.path.exists(local_file):
    with open(local_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = content.replace(
        "created_at = wallet.get('created_at', '')",
        "backup_time = wallet.get('backup_time', '')"
    )
    content = content.replace(
        "line = f\"{wallet_id:<6} {address:<40} {chain:<8} {created_at:<20}\\n\"",
        "line = f\"{wallet_id:<6} {address:<40} {chain:<8} {backup_time:<20}\\n\""
    )
    
    with open(local_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('✅ 本地文件已修改')

# 修改服务器文件
with open('/root/qianbao/houduan/points_panel.py', 'r') as f:
    content = f.read()

content = content.replace(
    "created_at = wallet.get('created_at', '')",
    "backup_time = wallet.get('backup_time', '')"
)
content = content.replace(
    'line = f"{wallet_id:<6} {address:<40} {chain:<8} {created_at:<20}\\n"',
    'line = f"{wallet_id:<6} {address:<40} {chain:<8} {backup_time:<20}\\n"'
)

with open('/root/qianbao/houduan/points_panel.py', 'w') as f:
    f.write(content)

print('✅ 服务器文件已修改')
