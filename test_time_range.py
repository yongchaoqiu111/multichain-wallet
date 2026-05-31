import requests
from datetime import datetime, timedelta

# 测试1: 查询所有比赛（不限时间）
r = requests.post('http://localhost:5004/matches/list', json={'game': 'all'})
result = r.json()
print(f"当前时间查询结果:")
print(f"成功: {result.get('success')}")
print(f"总数: {result.get('total')}\n")

# 测试2: 手动检查数据库
import pymysql
conn = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    password='WalletBackup2026!',
    database='wallet_backup',
    charset='utf8mb4'
)
cursor = conn.cursor()
now = datetime.now()
two_hours_later = now + timedelta(hours=2)

cursor.execute('''
    SELECT COUNT(*) FROM virtual_matches 
    WHERE match_time >= %s AND match_time <= %s
''', (now, two_hours_later))
count = cursor.fetchone()[0]
print(f"数据库中未来2小时的比赛数: {count}")

cursor.execute('SELECT MIN(match_time), MAX(match_time) FROM virtual_matches WHERE DATE(match_time) = CURDATE()')
min_time, max_time = cursor.fetchone()
print(f"今日最早比赛: {min_time}")
print(f"今日最晚比赛: {max_time}")
print(f"当前时间: {now}")

conn.close()
