import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('47.83.0.101', username='root', key_filename='C:/Users/Administrator/.ssh/id_rsa_personal_website')

# 读取移动端接口
stdin, stdout, stderr = ssh.exec_command('cat /root/wallet/mobile_wallet_api.py')
mobile_code = stdout.read().decode()

# 提取@app.route部分
routes = []
lines = mobile_code.split('\n')
i = 0
while i < len(lines):
    if lines[i].startswith('@app.route') and ('/wallet/create' in lines[i] or '/wallet/import/' in lines[i]):
        start = i
        i += 1
        while i < len(lines) and not (lines[i].startswith('@app.route') or lines[i].startswith('if __name__')):
            i += 1
        routes.append('\n'.join(lines[start:i]))
    else:
        i += 1

# 读取server.py
stdin, stdout, stderr = ssh.exec_command('cat /root/wallet/server.py')
server_code = stdout.read().decode()

# 在if __name__前插入
insert_pos = server_code.find("if __name__")
if insert_pos == -1:
    insert_pos = len(server_code)

new_code = server_code[:insert_pos] + '\n\n# Mobile APIs\nwallet_sessions = {}\n\n' + '\n\n'.join(routes) + '\n\n' + server_code[insert_pos:]

# 写回
stdin, stdout, stderr = ssh.exec_command(f'cat > /root/wallet/server.py << ENDOFFILE\n{new_code}\nENDOFFILE')
print(stdout.read().decode())
print(stderr.read().decode())

# 重启服务
ssh.exec_command('cd /root/wallet && pkill -f server.py && sleep 2 && nohup python3.13 server.py > server.log 2>&1 &')
print('Done!')
ssh.close()
