import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('47.108.198.44', username='root', key_filename='C:/Users/Administrator/.ssh/id_rsa')

# 检查 server.py 进程
stdin, stdout, stderr = ssh.exec_command('ps aux | grep server.py | grep -v grep')
print("进程状态:")
print(stdout.read().decode())

# 检查 nginx 配置
stdin, stdout, stderr = ssh.exec_command('cat /etc/nginx/sites-available/default | grep -A 10 location')
print("\nNginx 配置:")
print(stdout.read().decode())

# 检查端口监听
stdin, stdout, stderr = ssh.exec_command('netstat -tlnp | grep 5000')
print("\n端口监听:")
print(stdout.read().decode())

ssh.close()
