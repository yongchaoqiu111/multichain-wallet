import sys
sys.path.insert(0, '/root/wallet/modules/betting_system')
from modules.config import MYSQL_CONFIG
import pymysql

conn = pymysql.connect(**MYSQL_CONFIG)
cur = conn.cursor()
cur.execute('DELETE FROM matches')
conn.commit()
print('已清空旧数据')
conn.close()

import requests
r = requests.post('http://localhost:5004/matches/sync', json={'game': 'lol'}, timeout=30)
print(f"LOL同步: {r.json()}")

r2 = requests.post('http://localhost:5004/matches/sync', json={'game': 'dota2'}, timeout=30)
print(f"DOTA2同步: {r2.json()}")

r3 = requests.post('http://localhost:5004/matches/sync', json={'game': 'csgo'}, timeout=30)
print(f"CSGO同步: {r3.json()}")
