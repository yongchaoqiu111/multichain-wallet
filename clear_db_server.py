import pymysql
import sys
sys.path.insert(0, '/root/wallet/modules/betting_system')
from modules.config import MYSQL_CONFIG

conn = pymysql.connect(**MYSQL_CONFIG)
cursor = conn.cursor()
cursor.execute('DELETE FROM matches')
conn.commit()
print('已清空matches表')
conn.close()
