import re

# 读取服务器上的文件
with open('/root/wallet/wallet_api_service.py', 'r') as f:
    content = f.read()

# 找到_init_tron_wallet函数并替换为使用tronpy的实现
old_tron_wallet = '''    def _init_tron_wallet(self):
        import ecdsa
        import base58
        
        if not self.private_key:
            from mnemonic import Mnemonic
            from bip32utils import BIP32Key
            mnemo = Mnemonic("english")
            self.mnemonic = mnemo.generate(128)
            seed = mnemo.to_seed(self.mnemonic)
            HARDEN = 0x80000000
            master_key = BIP32Key.fromEntropy(seed)
            child_key = master_key.ChildKey(44 + HARDEN).ChildKey(195 + HARDEN).ChildKey(0 + HARDEN).ChildKey(0).ChildKey(0)
            self.private_key = child_key.PrivateKey().hex()
        
        private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
        vk = private_key_obj.get_verifying_key()
        public_key = b"\\x04" + vk.to_string()
        
        sha256 = hashlib.sha256(public_key).digest()
        h = RIPEMD160.new()
        h.update(sha256)
        ripemd = h.digest()
        address_bytes = b"\\x41" + ripemd
        checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
        self.address = base58.b58encode(address_bytes + checksum).decode()'''

new_tron_wallet = '''    def _init_tron_wallet(self):
        from tronpy.keys import PrivateKey
        
        if not self.private_key:
            from mnemonic import Mnemonic
            from bip32utils import BIP32Key
            mnemo = Mnemonic("english")
            self.mnemonic = mnemo.generate(128)
            seed = mnemo.to_seed(self.mnemonic)
            HARDEN = 0x80000000
            master_key = BIP32Key.fromEntropy(seed)
            child_key = master_key.ChildKey(44 + HARDEN).ChildKey(195 + HARDEN).ChildKey(0 + HARDEN).ChildKey(0).ChildKey(0)
            self.private_key = child_key.PrivateKey().hex()
        
        # 使用tronpy库生成标准TRON地址
        private_key_obj = PrivateKey(bytes.fromhex(self.private_key))
        self.address = private_key_obj.public_key.to_base58check_address()'''

content = content.replace(old_tron_wallet, new_tron_wallet)

with open('/root/wallet/wallet_api_service.py', 'w') as f:
    f.write(content)

print("已修复为使用tronpy库生成标准TRON地址")
