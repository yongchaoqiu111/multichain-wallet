#!/usr/bin/env python3
"""简单版本：读取移动端接口添加到server.py"""

# 读取移动端接口代码
with open('/root/wallet/mobile_wallet_api.py', 'r') as f:
    mobile_lines = f.readlines()

# 提取create、import接口
routes_code = []
current_route = []
in_route = False

for line in mobile_lines:
    if line.startswith('@app.route') and ('/wallet/create' in line or '/wallet/import/' in line):
        in_route = True
        current_route = [line]
    elif in_route:
        current_route.append(line)
        if line.strip() == '' or (line.startswith('@app.route') and not ('/wallet/create' in line or '/wallet/import/' in line)):
            routes_code.append(''.join(current_route[:-1] if line.startswith('@app.route') else current_route))
            current_route = []
            in_route = False
            if line.startswith('@app.route'):
                in_route = True
                current_route = [line]

# 如果没有检测到空行分隔，添加最后一个
if current_route:
    routes_code.append(''.join(current_route))

# 读取server.py
with open('/root/wallet/server.py', 'r') as f:
    server_content = f.read()

# 在if __name__前插入
insert_pos = server_content.find("if __name__")
if insert_pos == -1:
    insert_pos = len(server_content)

mobile_section = "\n\n# Mobile APIs\nwallet_sessions = {}\n\n" + '\n\n'.join(routes_code)

new_content = server_content[:insert_pos] + mobile_section + "\n\n" + server_content[insert_pos:]

with open('/root/wallet/server.py', 'w') as f:
    f.write(new_content)

print(f'Added {len(routes_code)} routes')
