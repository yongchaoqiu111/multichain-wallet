import sys

with open('wallet_api_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 在 backup_wallet_mobile 路由之前插入 list_wallets 接口
new_api = '''
@app.route('/api/wallet/list', methods=['POST'])
def list_wallets():
    """客服查询所有备份钱包列表"""
    try:
        with db_lock:
            conn = pymysql.connect(**DB_CONFIG)
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            cursor.execute("USE wallet_backup")
            cursor.execute('SELECT * FROM wallet_backups ORDER BY id DESC')
            rows = cursor.fetchall()
            cursor.close()
            conn.close()
        
        return jsonify({
            'success': True,
            'count': len(rows),
            'wallets': rows
        }), 200
        
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500


'''

# 找到 backup_wallet_mobile 的位置并插入
insert_pos = content.find("@app.route('/api/wallet/backup/mobile'")
if insert_pos != -1:
    content = content[:insert_pos] + new_api + content[insert_pos:]
    with open('wallet_api_service.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ 接口添加成功')
else:
    print('❌ 未找到插入位置')
    sys.exit(1)
