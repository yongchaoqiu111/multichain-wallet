"""
客服解密工具 - 纯Python脚本
本地运行，请求服务器数据，本地解密
"""
import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import os

# 从GitHub获取密钥
def get_keys_from_github():
    url = 'https://api.github.com/repos/yongchaoqiu111/plaint/contents/'
    response = requests.get(url)
    files = response.json()
    
    client_key = None
    server_key = None
    
    for file in files:
        name = file['name']
        key = os.path.splitext(name)[0]
        if name.endswith('.ico'):
            client_key = key.encode('utf-8')
        elif name.endswith('.png'):
            server_key = key.encode('utf-8')
    
    return client_key, server_key

# 双重解密
def decrypt_double(encrypted_str, client_key, server_key):
    # 第1层：服务器密钥
    encrypted_data = base64.b64decode(encrypted_str)
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    aesgcm = AESGCM(server_key)
    client_encrypted = aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
    
    # 第2层：客户端密钥
    client_data = base64.b64decode(client_encrypted)
    nonce2 = client_data[:12]
    ciphertext2 = client_data[12:]
    aesgcm2 = AESGCM(client_key)
    original_data = aesgcm2.decrypt(nonce2, ciphertext2, None).decode('utf-8')
    
    return original_data

# 主程序
def main():
    print("客服解密工具")
    print("="*50)
    
    # 验证密码
    password = input("输入密码: ")
    if password != 'customer_service_2026':
        print("密码错误！")
        return
    
    print("密码正确，正在获取数据...")
    
    # 获取密钥
    client_key, server_key = get_keys_from_github()
    
    # 请求服务器API
    response = requests.get('http://api.ai656.top/api/admin/list_all')
    data = response.json()
    
    if not data.get('success'):
        print(f"获取失败: {data.get('message')}")
        return
    
    wallets = data['data']['wallets']
    print(f"\n共 {len(wallets)} 条记录\n")
    
    # 解密并显示
    for wallet in wallets:
        try:
            address = decrypt_double(wallet['address'], client_key, server_key)
            chain = decrypt_double(wallet['chain'], client_key, server_key)
            print(f"地址: {address}")
            print(f"链: {chain}")
            print(f"时间: {wallet['backup_time']}")
            print("-" * 50)
        except Exception as e:
            print(f"解密失败: {e}")
    
    print("\n完成！")

if __name__ == '__main__':
    main()
