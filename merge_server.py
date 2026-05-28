#!/usr/bin/env python3
# 合并生成完整的 server.py

# 读取houduan/server.py
with open('houduan/server.py', 'r', encoding='utf-8') as f:
    server_content = f.read()

# 读取mobile_app/backend/wallet_api_service.py
with open('mobile_app/backend/wallet_api_service.py', 'r', encoding='utf-8') as f:
    mobile_content = f.read()

# 分割行
server_lines = server_content.split('\n')
mobile_lines = mobile_content.split('\n')

# 找到if __name__的位置
main_idx = None
for i, line in enumerate(server_lines):
    if 'if __name__' in line:
        main_idx = i
        break

print(f"找到 if __name__ 在第 {main_idx + 1} 行")

# 提取mobile部分：MultiChainWallet类(87-227行) + 3个接口(234-323行)
# 注意：列表索引从0开始，所以87行对应索引86
wallet_class = mobile_lines[86:227]  # 第87-227行
mobile_routes = mobile_lines[233:323]  # 第234-323行

print(f"提取 MultiChainWallet 类: {len(wallet_class)} 行")
print(f"提取移动端接口: {len(mobile_routes)} 行")

# 构建新内容
# 第1部分：if __name__ 之前的所有内容
part1 = server_lines[:main_idx]

# 第2部分：添加 CHAIN_CONFIG 和钱包类
part2 = [
    '',
    '# ==================== Mobile Wallet APIs ====================',
    '',
    'CHAIN_CONFIG = {',
    '    "ETH": {"coin_type": 60, "decimals": 18, "nodes": ["https://eth.llamarpc.com"]},',
    '    "BSC": {"coin_type": 60, "decimals": 18, "nodes": ["https://bsc-rpc.publicnode.com"]},',
    '    "TRON": {"coin_type": 195, "decimals": 6, "nodes": ["https://api.trongrid.io"]}',
    '}',
    '',
    'wallet_sessions = {}',
    ''
]

# 第3部分：MultiChainWallet类
part3 = wallet_class

# 第4部分：3个移动端接口
part4 = mobile_routes

# 第5部分：if __name__ 及之后
part5 = server_lines[main_idx:]

# 合并
new_content = '\n'.join(part1 + part2 + part3 + part4 + part5)

# 写入文件
with open('server_complete.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"\n成功生成 server_complete.py")
print(f"总行数: {len(new_content.split(chr(10)))}")
