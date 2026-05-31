#!/usr/bin/env python3

# 读取server.py
with open('/root/wallet/server.py', 'r') as f:
    content = f.read()

# 找到if __name__位置
insert_pos = content.find("if __name__")
if insert_pos == -1:
    insert_pos = len(content)

# 读取mobile_wallet_api.py完整内容
with open('/root/wallet/mobile_wallet_api.py', 'r') as f:
    mobile = f.read()

# 提取3个完整函数（从@app.route到下一个@app.route或文件结束）
import re

# create_wallet函数
create_match = re.search(r"(@app\.route\('/api/wallet/create'.*?)(?=\n@app\.route|\nif __name__|$)", mobile, re.DOTALL)
# import_private_key函数
import_pk_match = re.search(r"(@app\.route\('/api/wallet/import/private_key'.*?)(?=\n@app\.route|\nif __name__|$)", mobile, re.DOTALL)
# import_mnemonic函数
import_mn_match = re.search(r"(@app\.route\('/api/wallet/import/mnemonic'.*?)(?=\n@app\.route|\nif __name__|$)", mobile, re.DOTALL)

if create_match and import_pk_match and import_mn_match:
    mobile_apis = "\n\n# Mobile Wallet APIs\nwallet_sessions = {}\n\n"
    mobile_apis += create_match.group(1).strip() + "\n\n"
    mobile_apis += import_pk_match.group(1).strip() + "\n\n"
    mobile_apis += import_mn_match.group(1).strip() + "\n"
    
    # 插入到server.py
    new_content = content[:insert_pos] + mobile_apis + "\n" + content[insert_pos:]
    
    with open('/root/wallet/server.py', 'w') as f:
        f.write(new_content)
    
    print("Success: Added 3 mobile APIs")
else:
    print("Error: Could not extract all functions")
