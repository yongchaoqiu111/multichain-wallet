#!/usr/bin/env python3

file_path = '/root/wallet/wallet_api_service.py'

with open(file_path, 'r') as f:
    content = f.read()

# 1. 添加 visible: True 参数
old_data = '''                    data = {
                        "contract_address": usdt_contract,
                        "function_selector": "balanceOf(address)",
                        "parameter": _tron_address_to_hex_param(address),  # 动态转换
                        "owner_address": address,
                        "fee_limit": 100000000
                    }'''

new_data = '''                    data = {
                        "contract_address": usdt_contract,
                        "function_selector": "balanceOf(address)",
                        "parameter": _tron_address_to_hex_param(address),  # 动态转换
                        "owner_address": address,
                        "visible": True
                    }'''

content = content.replace(old_data, new_data)

# 2. 修复返回结果解析逻辑（桌面版的方式）
old_parse = '''                    if res.status_code == 200:
                        result = res.json()
                        if result.get('result', {}).get('result'):
                            hex_result = result['constant_result'][0]'''

new_parse = '''                    if res.status_code == 200:
                        result = res.json()
                        if "constant_result" in result and len(result["constant_result"]) > 0:
                            hex_result = result["constant_result"][0]'''

content = content.replace(old_parse, new_parse)

with open(file_path, 'w') as f:
    f.write(content)

print('✅ 已修复为桌面版相同的查询逻辑')
