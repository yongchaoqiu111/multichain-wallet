#!/usr/bin/env python3
"""
部署钱包后端到云端服务器
"""
import paramiko
import os

# 服务器配置
SERVER = "47.83.0.101"
USERNAME = "root"
# 免密登录，无需密码

# 本地文件
LOCAL_FILES = [
    "modules/wallet_core.py",
    "modules/wallet_api.py",
    "modules/data_manager.py",
    "requirements.txt"
]

# 远程路径
REMOTE_DIR = "/root/wallet"

def deploy():
    """部署到服务器"""
    print("连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    # 使用密钥文件免密登录
    ssh.connect(SERVER, username=USERNAME, key_filename=os.path.expanduser("~/.ssh/id_rsa"))
    
    # 创建远程目录
    stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {REMOTE_DIR}")
    print(f"远程目录已创建: {REMOTE_DIR}")
    
    # 上传文件
    sftp = ssh.open_sftp()
    for local_file in LOCAL_FILES:
        if os.path.exists(local_file):
            remote_file = f"{REMOTE_DIR}/{os.path.basename(local_file)}"
            sftp.put(local_file, remote_file)
            print(f"已上传: {local_file} -> {remote_file}")
        else:
            print(f"文件不存在: {local_file}")
    sftp.close()
    
    # 安装依赖
    print("安装 Python 依赖...")
    ssh.exec_command(f"cd {REMOTE_DIR} && pip3 install -r requirements.txt")
    
    # 启动服务
    print("启动后端服务...")
    ssh.exec_command(f"cd {REMOTE_DIR} && nohup python3 wallet_api.py > api.log 2>&1 &")
    
    ssh.close()
    print("部署完成！")
    print(f"API 地址: http://{SERVER}:5001")

if __name__ == "__main__":
    deploy()
