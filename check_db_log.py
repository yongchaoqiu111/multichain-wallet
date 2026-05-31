#!/usr/bin/env python3
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='WalletBackup2026!',
    database='wallet_backup'
)

cursor = conn.cursor()

# 检查general_log状态
cursor.execute("SHOW VARIABLES LIKE 'general_log%'")
print("General Log配置:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# 检查binlog状态
cursor.execute("SHOW VARIABLES LIKE 'log_bin%'")
print("\nBinlog配置:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# 查询最近的记录时间
cursor.execute("SELECT MIN(created_at), MAX(created_at), COUNT(*) FROM wallet_backups")
row = cursor.fetchone()
print(f"\n钱包备份记录:")
print(f"  最早: {row[0]}")
print(f"  最晚: {row[1]}")
print(f"  总数: {row[2]}")

# 按日期统计
cursor.execute("""
    SELECT DATE(created_at) as date, COUNT(*) as count 
    FROM wallet_backups 
    GROUP BY DATE(created_at) 
    ORDER BY date DESC
""")
print("\n每日备份数量:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}条")

cursor.close()
conn.close()
