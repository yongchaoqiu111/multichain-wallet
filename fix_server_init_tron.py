#!/usr/bin/env python3
with open('/root/wallet/modules/wallet_core.py', 'r') as f:
    content = f.read()

# 替换 else 分支，使用和新建钱包一样的地址生成方法
old_code = '''        else:
            # 导入已有钱包
            try:
                from tronpy.keys import PrivateKey
                private_key_obj = PrivateKey(bytes.fromhex(self.private_key))
                self.address = private_key_obj.public_key.to_base58check_address()
            except Exception as e:
                raise ValueError(f"私钥格式错误: {str(e)}")'''

new_code = '''        else:
            # 导入已有钱包 - 使用和新建钱包相同的地址生成方法
            private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
            vk = private_key_obj.get_verifying_key()
            public_key = b"\\x04" + vk.to_string()
            
            sha256 = hashlib.sha256(public_key).digest()
            ripemd = RIPEMD160.new(sha256).digest()
            address_bytes = b"\\x41" + ripemd
            checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
            self.address = base58.b58encode(address_bytes + checksum).decode()'''

content = content.replace(old_code, new_code)

with open('/root/wallet/modules/wallet_core.py', 'w') as f:
    f.write(content)

print('Fixed!')
