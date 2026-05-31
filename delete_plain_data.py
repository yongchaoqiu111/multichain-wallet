#!/usr/bin/env python3
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='WalletBackup2026!',
    database='wallet_backup'
)

cursor = conn.cursor()

# 查询明文数据数量
cursor.execute("SELECT COUNT(*) FROM wallet_backups WHERE encrypted_data LIKE '{%'")
plain_count = cursor.fetchone()[0]
print(f"发现 {plain_count} 条明文数据")

# 删除明文数据
if plain_count > 0:
    cursor.execute("DELETE FROM wallet_backups WHERE encrypted_data LIKE '{%'")
    conn.commit()
    print(f"✅ 已删除 {plain_count} 条明文数据")
else:
    print("没有明文数据需要删除")

# 查询剩余数据
cursor.execute("SELECT COUNT(*) FROM wallet_backups")
total = cursor.fetchone()[0]
print(f"剩余 {total} 条加密数据")

cursor.close()
conn.close()
