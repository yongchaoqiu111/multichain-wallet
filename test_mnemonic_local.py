from modules.wallet_core import MultiChainWallet

mnemonic = 'aisle define upon praise forest scene quality item season galaxy invest witness'
wallet = MultiChainWallet(chain='TRON', mnemonic=mnemonic)
info = wallet.get_wallet_info()

print(f'助记词: {mnemonic}')
print(f'地址: {info["address"]}')
print(f'私钥: {info["private_key"]}')
