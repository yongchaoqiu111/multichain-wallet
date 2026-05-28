#!/bin/bash
# 修复服务器端 wallet_core.py，使用 RIPEMD160.new() 替代 hashlib.new('ripemd160')

python3 << 'EOF'
with open('/root/wallet/modules/wallet_core.py', 'r') as f:
    content = f.read()

# 替换 _init_tron_wallet 中的 hashlib.new('ripemd160') 为 RIPEMD160.new()
content = content.replace(
    "ripemd = hashlib.new('ripemd160', sha256).digest()",
    "ripemd = RIPEMD160.new(sha256).digest()"
)

# 确保在 _init_tron_wallet 中导入 RIPEMD160
if "from Crypto.Hash import RIPEMD160" not in content.split("def _init_tron_wallet")[1].split("def ")[0]:
    content = content.replace(
        "def _init_tron_wallet(self):",
        "def _init_tron_wallet(self):\n        from Crypto.Hash import RIPEMD160"
    )

with open('/root/wallet/modules/wallet_core.py', 'w') as f:
    f.write(content)

print('Fixed!')
EOF
