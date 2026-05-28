#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/wallet')
from modules.wallet_core import MultiChainWallet
import inspect

# 打印实际加载的文件路径
print(f"MultiChainWallet 文件路径: {inspect.getfile(MultiChainWallet)}")

# 打印 _init_tron_wallet 方法的源代码
print("\n=== _init_tron_wallet 源码（前50行）===")
source = inspect.getsource(MultiChainWallet._init_tron_wallet)
lines = source.split('\n')[:50]
for i, line in enumerate(lines, 1):
    print(f"{i:3d}: {line}")
