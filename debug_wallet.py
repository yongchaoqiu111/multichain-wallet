#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/wallet')
from modules.wallet_core import MultiChainWallet
import inspect

mnemonic = "aisle define upon property force sentence country tonight wife autumn normal entry"
wallet = MultiChainWallet(chain="TRON", mnemonic=mnemonic)

print("=== 钱包信息 ===")
print(f"地址: {wallet.address}")
print(f"私钥: {wallet.private_key}")

print("\n=== _init_tron_wallet 代码 ===")
try:
    source = inspect.getsource(wallet._init_tron_wallet)
    print(source[:800])
except Exception as e:
    print(f"Error: {e}")
