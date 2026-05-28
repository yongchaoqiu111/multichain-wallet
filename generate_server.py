#!/usr/bin/env python3
# 合并houduan/server.py和mobile_wallet_api.py生成完整的server.py

with open('f:/qianbao/houduan/server.py', 'r', encoding='utf-8') as f:
    server_content = f.read()

with open('f:/qianbao/mobile_app/backend/wallet_api_service.py', 'r', encoding='utf-8') as f:
    mobile_content = f.read()

# 找到if __name__的位置
lines = server_content.split('\n')
main_idx = None
for i, line in enumerate(lines):
    if 'if __name__' in line:
        main_idx = i
        break

if not main_idx:
    print("Error: if __name__ not found")
    exit(1)

# 提取mobile部分
mobile_lines = mobile_content.split('\n')
wallet_class = '\n'.join(mobile_lines[86:227])  # MultiChainWallet类
mobile_routes = '\n'.join(mobile_lines[233:323])  # 3个接口

# 构建完整内容
new_content = (
    '\n'.join(lines[:main_idx]) +
    '\n\n# ==================== Mobile Wallet APIs ====================\n\n' +
    'CHAIN_CONFIG = {\n' +
    '    "BSC": {"nodes": ["https://bsc-dataseed.binance.org/"], "chain_id": 56},\n' +
    '    "ETH": {"nodes": ["https://eth.llamarpc.com"], "chain_id": 1},\n' +
    '    "TRON": {"nodes": ["https://api.trongrid.io"], "chain_id": None}\n' +
    '}\n\n' +
    wallet_class +
    '\n\nwallet_sessions = {}\n\n' +
    mobile_routes +
    '\n\n' +
    '\n'.join(lines[main_idx:])
)

with open('f:/qianbao/server_complete.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Done! Generated server_complete.py")
