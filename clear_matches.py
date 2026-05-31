import pymysql

# 数据库配置
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',  # 需要从服务器配置读取
    'database': 'betting_system'
}

try:
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    
    # 清空matches表
    cursor.execute('DELETE FROM matches')
    conn.commit()
    
    print('已清空matches表')
    
    conn.close()
except Exception as e:
    print(f'Error: {e}')
