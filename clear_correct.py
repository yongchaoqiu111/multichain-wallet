import sys
sys.path.insert(0, '/root/wallet')

from modules.config import MYSQL_CONFIG
import pymysql

conn = pymysql.connect(**MYSQL_CONFIG)
cur = conn.cursor()
cur.execute('DELETE FROM matches')
conn.commit()
print('已清空旧数据')
conn.close()
