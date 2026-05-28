#!/usr/bin/env python3
"""将mobile_wallet_api.py的移动端接口合并到server.py"""

# 读取mobile_wallet_api.py
with open('/root/wallet/mobile_wallet_api.py', 'r') as f:
    mobile_content = f.read()

# 读取server.py
with open('/root/wallet/server.py', 'r') as f:
    server_content = f.read()

# 提取mobile_wallet_api.py中所有@app.route装饰器和函数
# 找到所有移动端特有的接口
mobile_routes = []
lines = mobile_content.split('\n')
i = 0
while i < len(lines):
    line = lines[i]
    if "@app.route('/api/wallet/create'" in line or \
       "@app.route('/api/wallet/import/" in line or \
       "@app.route('/api/wallet/transfer'" in line or \
       "@app.route('/api/wallet/estimate_fee'" in line or \
       "@app.route('/api/wallet/backup'" in line:
        # 找到这个route对应的完整函数
        route_start = i
        # 找到函数定义行
        while i < len(lines) and 'def ' not in lines[i]:
            i += 1
        if i < len(lines):
            func_start = i
            # 找到函数结束（下一个@app.route或文件末尾）
            i += 1
            while i < len(lines) and not lines[i].startswith('@app.route'):
                i += 1
            func_end = i
            # 提取这段代码
            route_code = '\n'.join(lines[route_start:func_end])
            mobile_routes.append(route_code)

# 将移动端接口添加到server.py的if __name__之前
insert_pos = server_content.find("if __name__ == '__main__':")
if insert_pos == -1:
    insert_pos = len(server_content)

# 添加移动端接口
new_content = server_content[:insert_pos] + '\n\n# ===== 移动端钱包接口 =====\n\n'
for route in mobile_routes:
    new_content += route + '\n\n'
new_content += server_content[insert_pos:]

# 检查是否需要导入MultiChainWallet
if 'MultiChainWallet' in new_content and 'from modules.wallet_core import MultiChainWallet' not in new_content:
    # 在导入部分添加
    import_pos = new_content.find('from flask import')
    if import_pos != -1:
        # 找到最后一个import
        last_import = new_content.rfind('\n', 0, import_pos + 200)
        new_content = new_content[:last_import] + '\nfrom modules.wallet_core import MultiChainWallet' + new_content[last_import:]

with open('/root/wallet/server.py', 'w') as f:
    f.write(new_content)

print(f'✅ 成功添加 {len(mobile_routes)} 个移动端接口到 server.py')
