import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='WalletBackup2026!',
    database='wallet_backup'
)

cursor = conn.cursor()
cursor.execute("UPDATE user_points SET points=0, total_earned=0 WHERE address='TVAxmL3ofYT1WFN8PAq2LgV6yJxtxfb6o6'")
conn.commit()
print(f"Updated {cursor.rowcount} rows")
cursor.close()
conn.close()
