import pymysql

conn = pymysql.connect(
    host='localhost',
    port=3306,
    user='root',
    password='WalletBackup2026!',
    database='wallet_backup',
    charset='utf8mb4'
)
cur = conn.cursor()
cur.execute('SELECT id, game, match_time, status FROM virtual_matches LIMIT 5')
rows = cur.fetchall()
print(f"查询到 {len(rows)} 场比赛")
for row in rows:
    print(row)
conn.close()
