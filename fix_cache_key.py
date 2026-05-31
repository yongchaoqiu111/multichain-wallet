#!/usr/bin/env python3

file_path = '/root/wallet/wallet_api_service.py'

with open(file_path, 'r') as f:
    content = f.read()

# 清除缓存逻辑：修改 cache_key 包含 token
old_cache_key = 'cache_key = f"{chain}:{address}"'
new_cache_key = 'cache_key = f"{chain}:{address}:{token}"'

content = content.replace(old_cache_key, new_cache_key)

with open(file_path, 'w') as f:
    f.write(content)

print('✅ 已修改缓存 key 包含 token')
