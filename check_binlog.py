#!/usr/bin/env python3
import subprocess

# 查看binlog文件列表
result = subprocess.run(
    ["ssh", "-i", "C:\\Users\\Administrator\\.ssh\\id_rsa_personal_website", 
     "root@47.83.0.101", 
     "mysql -u root -p'WalletBackup2026!' -e 'SHOW BINARY LOGS;'"],
    capture_output=True, text=True
)
print("Binlog文件列表:")
print(result.stdout)

# 查看最近的binlog事件
result = subprocess.run(
    ["ssh", "-i", "C:\\Users\\Administrator\\.ssh\\id_rsa_personal_website", 
     "root@47.83.0.101", 
     "mysql -u root -p'WalletBackup2026!' -e 'SHOW BINLOG EVENTS LIMIT 50;'"],
    capture_output=True, text=True
)
print("\n最近的Binlog事件:")
print(result.stdout)
