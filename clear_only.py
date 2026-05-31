import sys
import os
sys.path.insert(0, '/root/wallet/modules/betting_system')
os.chdir('/root/wallet/modules/betting_system')

from modules.config import MYSQL_CONFIG
import pymysql

conn = pymysql.connect(**MYSQL_CONFIG)
cur = conn.cursor()
cur.execute('DELETE FROM matches')
conn.commit()
print('已清空旧数据')
conn.close()
