#!/usr/bin/env python3
"""修改服务器wallet_api_service.py的list_wallets接口，返回完整数据"""

file_path = '/root/wallet/wallet_api_service.py'

with open(file_path, 'r') as f:
    content = f.read()

old_select = "cursor.execute('SELECT backup_id, backup_time FROM wallet_backups ORDER BY backup_time DESC')"
new_select = "cursor.execute('SELECT id, backup_id, address, chain, encrypted_data, backup_time FROM wallet_backups ORDER BY id DESC')"

old_wallets = "wallets = [{'backup_id': row['backup_id'], 'backup_time': row['backup_time']} for row in rows]"
new_wallets = "wallets = [dict(row) for row in rows]"

content = content.replace(old_select, new_select)
content = content.replace(old_wallets, new_wallets)

with open(file_path, 'w') as f:
    f.write(content)

print('✅ list_wallets接口已修改为返回完整数据')
