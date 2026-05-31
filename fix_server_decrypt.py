import sys

# 读取服务器文件
with open('/root/qianbao/houduan/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到 decrypt_with_key 函数并修改为兼容明文
old_code = """def decrypt_with_key(encrypted_str: str, key: bytes) -> str:
    \"\"\"使用指定密钥解密字段\"\"\"
    encrypted_data = base64.b64decode(encrypted_str)
    nonce = encrypted_data[:12]
    ciphertext = encrypted_data[12:]
    aesgcm = AESGCM(key)
    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
    return decrypted_bytes.decode('utf-8')"""

new_code = """def decrypt_with_key(encrypted_str: str, key: bytes) -> str:
    \"\"\"使用指定密钥解密字段，兼容明文数据\"\"\"
    try:
        encrypted_data = base64.b64decode(encrypted_str)
        nonce = encrypted_data[:12]
        ciphertext = encrypted_data[12:]
        aesgcm = AESGCM(key)
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode('utf-8')
    except:
        # 解密失败说明是明文数据（测试阶段旧数据）
        return encrypted_str"""

content = content.replace(old_code, new_code)

with open('/root/qianbao/houduan/server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('修复完成！')
