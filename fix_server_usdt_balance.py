#!/usr/bin/env python3
"""修复服务器 API 支持代币余额查询"""

file_path = '/root/wallet/wallet_api_service.py'

with open(file_path, 'r') as f:
    content = f.read()

# 1. 修改 get_balance 函数签名，添加 token 参数
old_func = '''def get_balance(chain, address):'''
new_func = '''def get_balance(chain, address, token=None):'''

content = content.replace(old_func, new_func)

# 2. 在 TRON 分支中添加 USDT 查询逻辑
old_tron_block = '''    if chain == "TRON":
        for node in nodes:
            try:
                url = f"{node.rstrip('/')}/wallet/getaccount"
                data = {"address": address, "visible": True}
                res = requests.post(url, json=data, timeout=8)
                if res.status_code == 200:
                    result = res.json()
                    sun = result.get("balance", 0)
                    trx = int(sun) / 10**6
                    _balance_cache[cache_key] = {'balance': trx, 'timestamp': time.time()}
                    return trx
            except:
                continue
        raise Exception("All TRON nodes failed")'''

new_tron_block = '''    if chain == "TRON":
        # 如果查询代币（如 USDT）
        if token and token.upper() == "USDT":
            usdt_contract = "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"  # TRC20 USDT
            for node in nodes:
                try:
                    url = f"{node.rstrip('/')}/wallet/triggerconstantcontract"
                    data = {
                        "contract_address": usdt_contract,
                        "function_selector": "balanceOf(address)",
                        "parameter": "000000000000000000000000" + address[2:],  # 去掉 0x 前缀
                        "owner_address": address,
                        "fee_limit": 100000000
                    }
                    res = requests.post(url, json=data, timeout=8)
                    if res.status_code == 200:
                        result = res.json()
                        if result.get('result', {}).get('result'):
                            hex_result = result['constant_result'][0]
                            balance_int = int(hex_result, 16)
                            usdt_balance = balance_int / 10**6  # USDT 是 6 位小数
                            _balance_cache[cache_key] = {'balance': usdt_balance, 'timestamp': time.time()}
                            return usdt_balance
                except:
                    continue
            raise Exception("Failed to query USDT balance")
        
        # 查询主币 TRX
        for node in nodes:
            try:
                url = f"{node.rstrip('/')}/wallet/getaccount"
                data = {"address": address, "visible": True}
                res = requests.post(url, json=data, timeout=8)
                if res.status_code == 200:
                    result = res.json()
                    sun = result.get("balance", 0)
                    trx = int(sun) / 10**6
                    _balance_cache[cache_key] = {'balance': trx, 'timestamp': time.time()}
                    return trx
            except:
                continue
        raise Exception("All TRON nodes failed")'''

content = content.replace(old_tron_block, new_tron_block)

with open(file_path, 'w') as f:
    f.write(content)

print('✅ 已修复服务器 API 支持 USDT 查询')
