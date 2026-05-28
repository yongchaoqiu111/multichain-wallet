#!/usr/bin/env python3
"""
在服务器上执行移动端多钱包测试
"""
import paramiko
import time

# SSH连接配置
ssh_host = '服务器IP'
ssh_user = 'root'
ssh_port = 22

print("="*70)
print("上传测试脚本到服务器...")
print("="*70)

# 读取测试脚本
with open('test_mobile_multiple_wallets.py', 'r', encoding='utf-8') as f:
    script_content = f.read()

# SSH连接
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    print(f"连接到 {ssh_host}...")
    ssh.connect(ssh_host, port=ssh_port, username=ssh_user, key_filename='~/.ssh/id_rsa')
    print("✅ SSH连接成功")
    
    # 上传脚本
    sftp = ssh.open_sftp()
    remote_path = '/tmp/test_mobile_multiple_wallets.py'
    print(f"上传脚本到 {remote_path}...")
    
    with sftp.open(remote_path, 'w') as f:
        f.write(script_content)
    print("✅ 脚本上传成功")
    sftp.close()
    
    # 执行脚本
    print("\n" + "="*70)
    print("在服务器上执行测试...")
    print("="*70)
    
    stdin, stdout, stderr = ssh.exec_command(f'python3 {remote_path}')
    
    # 实时输出
    for line in stdout:
        print(line, end='')
    
    error_output = stderr.read().decode('utf-8')
    if error_output:
        print("\n错误输出:")
        print(error_output)
    
    # 清理
    ssh.exec_command(f'rm {remote_path}')
    print("\n✅ 测试完成，临时文件已清理")
    
except Exception as e:
    print(f"❌ 执行失败: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    ssh.close()
    print("\nSSH连接已关闭")
