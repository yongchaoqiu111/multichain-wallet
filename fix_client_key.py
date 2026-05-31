#!/usr/bin/env python3

# 读取文件
with open(r'F:\houduan\points_panel.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换密钥
old_key = "SERVER_KEY = b'ServerWallet2026SecureKey32B!!!!'"
new_key = "CLIENT_KEY = b'ClientWallet2026SecureKey32B!!!!'"

if old_key in content:
    content = content.replace(old_key, new_key)
    
    # 同时修改变量名引用
    content = content.replace("aesgcm = AESGCM(SERVER_KEY)", "aesgcm = AESGCM(CLIENT_KEY)")
    
    with open(r'F:\houduan\points_panel.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('✅ 修改完成：密钥改为CLIENT_KEY')
else:
    print('❌ 未找到需要替换的代码')
    print('当前代码可能已经是CLIENT_KEY或其他格式')
