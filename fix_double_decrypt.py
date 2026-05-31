#!/usr/bin/env python3

# 读取文件
with open(r'F:\houduan\points_panel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换解密逻辑
old_code = """            # 步骤2: 本地AES-GCM解密（单层，使用服务器密钥）
            import base64
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            
            # 服务器密钥（与server.py保持一致）
            SERVER_KEY = b'ServerWallet2026SecureKey32B!!!!'
            
            # Base64解码
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # 提取nonce和ciphertext
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]
            
            # 使用服务器密钥解密
            aesgcm = AESGCM(SERVER_KEY)
            decrypted_json = aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')"""

new_code = """            # 步骤2: 本地AES-GCM解密（双层解密）
            import base64
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            
            # 密钥（与server.py保持一致）
            SERVER_KEY = b'ServerWallet2026SecureKey32B!!!!'
            CLIENT_KEY = b'ClientWallet2026SecureKey32B!!!!'
            
            # 第一层：解服务器加密层
            encrypted_bytes = base64.b64decode(encrypted_data)
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]
            aesgcm = AESGCM(SERVER_KEY)
            client_encrypted_base64 = aesgcm.decrypt(nonce, ciphertext, None).decode('utf-8')
            
            # 第二层：解客户端加密层
            client_encrypted_bytes = base64.b64decode(client_encrypted_base64)
            nonce2 = client_encrypted_bytes[:12]
            ciphertext2 = client_encrypted_bytes[12:]
            aesgcm2 = AESGCM(CLIENT_KEY)
            decrypted_json = aesgcm2.decrypt(nonce2, ciphertext2, None).decode('utf-8')"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(r'F:\houduan\points_panel.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ 修改完成：已改为双层解密')
else:
    print('❌ 未找到需要替换的代码')
