#!/usr/bin/env python3

file_path = '/root/wallet/modules/wallet_core.py'

with open(file_path, 'r') as f:
    content = f.read()

# 替换新建钱包的地址生成
content = content.replace(
    '''            # 生成公钥
            private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
            vk = private_key_obj.get_verifying_key()
            public_key = b"\\x04" + vk.to_string()
            
            # 生成地址
            sha256 = hashlib.sha256(public_key).digest()
            ripemd = RIPEMD160.new(sha256).digest()
            address_bytes = b"\\x41" + ripemd
            
            # 双哈希校验
            checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
            self.address = base58.b58encode(address_bytes + checksum).decode()
        else:
            # 导入已有钱包 - 使用和新建钱包相同的地址生成方法
            private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
            vk = private_key_obj.get_verifying_key()
            public_key = b"\\x04" + vk.to_string()
            
            sha256 = hashlib.sha256(public_key).digest()
            ripemd = RIPEMD160.new(sha256).digest()
            address_bytes = b"\\x41" + ripemd
            checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
            self.address = base58.b58encode(address_bytes + checksum).decode()''',
    '''            # 使用 tronpy 官方方法生成地址
            from tronpy.keys import PrivateKey
            private_key_obj = PrivateKey(bytes.fromhex(self.private_key))
            self.address = private_key_obj.public_key.to_base58check_address()
        else:
            # 导入已有钱包 - 使用 tronpy 官方方法生成地址
            from tronpy.keys import PrivateKey
            private_key_obj = PrivateKey(bytes.fromhex(self.private_key))
            self.address = private_key_obj.public_key.to_base58check_address()'''
)

with open(file_path, 'w') as f:
    f.write(content)

print('服务器端 wallet_core.py 已修复为使用 tronpy 官方方法生成地址')
