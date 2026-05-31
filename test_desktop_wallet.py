#!/usr/bin/env python3
import sys
sys.path.insert(0, 'f:/qianbao')
from modules.wallet_core import MultiChainWallet

mnemonic = "aisle define upon property force sentence country tonight wife autumn normal entry"
wallet = MultiChainWallet(chain="TRON", mnemonic=mnemonic)
info = wallet.get_wallet_info()

print(f"地址: {info['address']}")
print(f"私钥: {info['private_key']}")
