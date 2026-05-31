#!/usr/bin/env python3
file_path = '/root/wallet/server.py'
with open(file_path, 'r') as f:
    content = f.read()

old = "cursor.execute('SELECT backup_id, backup_time FROM wallet_backups ORDER BY backup_time DESC')"
new = "cursor.execute('SELECT id, backup_id, address, chain, encrypted_data, backup_time FROM wallet_backups ORDER BY id DESC')"
content = content.replace(old, new)

old2 = "wallets = [{'backup_id': row['backup_id'], 'backup_time': row['backup_time']} for row in rows]"
new2 = "wallets = [dict(row) for row in rows]"
content = content.replace(old2, new2)

with open(file_path, 'w') as f:
    f.write(content)
print('done')
