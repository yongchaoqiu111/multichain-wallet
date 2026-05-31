#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/wallet')
from modules.wallet_core import MultiChainWallet

mnemonic = "aisle define upon property force sentence country tonight wife autumn normal entry"

print("=== 创建钱包实例 ===")
wallet = MultiChainWallet(chain="TRON", mnemonic=mnemonic)

print(f"\n私钥: {wallet.private_key}")
print(f"地址: {wallet.address}")

# 直接测试 tronpy
print("\n=== 直接使用 tronpy 测试 ===")
from tronpy.keys import PrivateKey
pk = PrivateKey(bytes.fromhex(wallet.private_key))
print(f"tronpy 生成的地址: {pk.public_key.to_base58check_address()}")
