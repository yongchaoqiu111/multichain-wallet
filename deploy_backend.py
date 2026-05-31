import paramiko
import os

def deploy_to_server():
    host = '47.83.0.101'
    username = 'root'
    
    local_backend_dir = r'f:\qianbao\移动端\mobile_backend'
    remote_dir = '/root/wallet'
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username)
        
        sftp = ssh.open_sftp()
        
        print("创建远程目录...")
        stdin, stdout, stderr = ssh.exec_command(f'mkdir -p {remote_dir}/modules')
        stdout.read()
        
        files_to_copy = [
            ('wallet_api_service.py', remote_dir),
            ('modules/config.py', f'{remote_dir}/modules'),
            ('modules/wallet_core.py', f'{remote_dir}/modules'),
            ('.env', remote_dir),
            ('requirements.txt', remote_dir),
            ('start.sh', remote_dir),
        ]
        
        for local_file, remote_path in files_to_copy:
            local_path = os.path.join(local_backend_dir, local_file)
            remote_file = os.path.join(remote_path, os.path.basename(local_file))
            
            print(f"上传 {local_path} -> {remote_file}")
            sftp.put(local_path, remote_file)
        
        sftp.close()
        
        print("重启服务...")
        stdin, stdout, stderr = ssh.exec_command(f'pkill -f "python3 wallet_api_service.py" || true')
        stdout.read()
        
        stdin, stdout, stderr = ssh.exec_command(f'cd {remote_dir} && pip3 install -r requirements.txt -q && nohup python3 wallet_api_service.py > api.log 2>&1 &')
        stdout.read()
        
        import time
        time.sleep(2)
        
        stdin, stdout, stderr = ssh.exec_command(f'curl -s http://localhost:5001/api/health')
        result = stdout.read().decode()
        print(f"服务状态: {result}")
        
        ssh.close()
        print("部署完成！")
        
    except Exception as e:
        print(f"部署失败: {e}")

if __name__ == '__main__':
    deploy_to_server()
