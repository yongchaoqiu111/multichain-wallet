"""
多链钱包核心模块 - 移动端后端专�?支持 BSC / ETH / TRON
"""
from web3 import Web3
from tronpy import Tron
from tronpy.providers import HTTPProvider
from mnemonic import Mnemonic
from bip32utils import BIP32Key
import hashlib
import time
import requests

class WalletError(Exception):
    pass

class InvalidChainError(WalletError):
    pass

class InvalidAddressError(WalletError):
    pass

class NodeRequestError(WalletError):
    pass

CHAIN_CONFIG = {
    "ETH": {
        "coin_type": 60,
        "decimals": 18,
        "nodes": [
            "https://rpc.ankr.com/eth/393b30f5d81b27795cea770a7780eb73fcfbef61b19bbbfa4e676f601485f2db",
            "https://ethereum-rpc.publicnode.com",
            "https://eth.llamarpc.com"
        ]
    },
    "BSC": {
        "coin_type": 60,
        "decimals": 18,
        "nodes": [
            "https://rpc.ankr.com/bsc/393b30f5d81b27795cea770a7780eb73fcfbef61b19bbbfa4e676f601485f2db",
            "https://bsc-rpc.publicnode.com",
            "https://bsc-dataseed.bnbchain.org"
        ]
    },
    "TRON": {
        "coin_type": 195,
        "decimals": 6,
        "nodes": [
            "https://api.trongrid.io",
            "https://tron.api.onfinality.io/public",
            "https://rpc.trongrid.io"
        ],
        "api_key": "4858ecc5-60f2-4e06-a1a1-2aa35be108ac"
    }
}

_balance_cache = {}
_CACHE_TTL = 5

def _get_cached_balance(chain: str, address: str) -> tuple:
    cache_key = f"{chain}:{address}"
    if cache_key in _balance_cache:
        cached = _balance_cache[cache_key]
        if time.time() - cached['timestamp'] < _CACHE_TTL:
            return cached['balance'], True
        else:
            del _balance_cache[cache_key]
    return None, False

def _set_cached_balance(chain: str, address: str, balance: float):
    cache_key = f"{chain}:{address}"
    _balance_cache[cache_key] = {
        'balance': balance,
        'timestamp': time.time()
    }

def _get_trx_balance(nodes, address):
    if not address.startswith("T"):
        raise InvalidAddressError(f"TRON 地址必须 T 开�? {address}")
    for node in nodes:
        try:
            url = f"{node.rstrip('/')}/wallet/getaccount"
            data = {"address": address, "visible": True}
            res = requests.post(url, json=data, timeout=8)
            if res.status_code == 200:
                result = res.json()
                sun = result.get("balance", 0)
                trx = int(sun) / 10**6
                return trx
        except Exception as e:
            continue
    raise NodeRequestError("所�?TRON 节点查询失败")

def _get_evm_balance(chain, nodes, address, decimals):
    if not address.startswith("0x"):
        raise InvalidAddressError(f"{chain} 地址必须 0x 开�? {address}")
    for node in nodes:
        try:
            data = {
                "jsonrpc": "2.0",
                "method": "eth_getBalance",
                "params": [address, "latest"],
                "id": 1
            }
            res = requests.post(node, json=data, timeout=8)
            if res.status_code == 200:
                result = res.json()
                wei = int(result["result"], 16)
                balance = wei / 10**decimals
                return balance
        except Exception as e:
            continue
    raise NodeRequestError(f"所�?{chain} 节点查询失败")

def get_balance(chain: str, address: str):
    cached_balance, is_cached = _get_cached_balance(chain, address)
    if is_cached:
        return cached_balance
    
    if chain not in CHAIN_CONFIG:
        raise InvalidChainError(f"不支持的�? {chain}")

    config = CHAIN_CONFIG[chain]
    nodes = config["nodes"]
    decimals = config["decimals"]

    if chain == "TRON":
        balance = _get_trx_balance(nodes, address)
    else:
        balance = _get_evm_balance(chain, nodes, address, decimals)
    
    _set_cached_balance(chain, address, balance)
    return balance

class MultiChainWallet:
    def __init__(self, chain="BSC", private_key=None, mnemonic=None):
        if chain not in CHAIN_CONFIG:
            raise InvalidChainError(f"不支持的�? {chain}")
        
        self.chain = chain
        self.rpc = CHAIN_CONFIG[chain]["nodes"][0]
        self.private_key = private_key
        self.mnemonic = mnemonic
        self.address = None
        self.web3 = None
        self.tron_client = None
        
        self._load_or_create_wallet()
    
    def _load_or_create_wallet(self):
        if self.mnemonic:
            self.private_key = self._mnemonic_to_private_key(self.mnemonic)
        
        if self.chain == "TRON":
            self._init_tron_wallet()
        else:
            self._init_evm_wallet()
    
    def _mnemonic_to_private_key(self, mnemonic_words, account_index=0):
        mnemo = Mnemonic("english")
        seed = mnemo.to_seed(mnemonic_words)
        HARDEN = 0x80000000
        
        if self.chain == "TRON":
            coin_type = 195
        elif self.chain in ["ETH", "BSC"]:
            coin_type = 60
        else:
            coin_type = 60
        
        master_key = BIP32Key.fromEntropy(seed)
        child_key = master_key.ChildKey(44 + HARDEN).ChildKey(coin_type + HARDEN).ChildKey(account_index + HARDEN).ChildKey(0).ChildKey(0)
        return child_key.PrivateKey().hex()
    
    def derive_address(self, account_index=0):
        if not self.mnemonic:
            raise ValueError("没有助记词，无法派生地址")
        
        private_key = self._mnemonic_to_private_key(self.mnemonic, account_index)
        
        if self.chain == "TRON":
            import ecdsa
            import base58
            
            private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
            vk = private_key_obj.get_verifying_key()
            public_key = b"\x04" + vk.to_string()
            
            sha256 = hashlib.sha256(public_key).digest()
            ripemd = hashlib.new('ripemd160', sha256).digest()
            address_bytes = b"\x41" + ripemd
            checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
            address = base58.b58encode(address_bytes + checksum).decode()
        else:
            account = self.web3.eth.account.from_key(private_key)
            address = account.address
        
        return {
            'index': account_index,
            'address': address,
            'private_key': private_key
        }
    
    def _init_evm_wallet(self):
        self.web3 = Web3(Web3.HTTPProvider(self.rpc))
        
        if not self.private_key:
            mnemo = Mnemonic("english")
            self.mnemonic = mnemo.generate(128)
            
            seed = mnemo.to_seed(self.mnemonic)
            HARDEN = 0x80000000
            master_key = BIP32Key.fromEntropy(seed)
            child_key = master_key.ChildKey(44 + HARDEN).ChildKey(60 + HARDEN).ChildKey(0 + HARDEN).ChildKey(0).ChildKey(0)
            self.private_key = child_key.PrivateKey().hex()
            
            account = self.web3.eth.account.from_key(self.private_key)
            self.address = account.address
        else:
            account = self.web3.eth.account.from_key(self.private_key)
            self.address = account.address
    
    def _init_tron_wallet(self):
        import ecdsa
        import base58
        
        config = CHAIN_CONFIG.get(self.chain, {})
        api_key = config.get("api_key")
        
        if api_key and api_key != "TRON-PRO-API-KEY":
            self.tron_client = Tron(HTTPProvider(api_key=api_key))
        else:
            self.tron_client = Tron(HTTPProvider(self.rpc))
        
        if not self.private_key:
            mnemo = Mnemonic("english")
            self.mnemonic = mnemo.generate(128)
            
            seed = mnemo.to_seed(self.mnemonic)
            HARDEN = 0x80000000
            master_key = BIP32Key.fromEntropy(seed)
            child_key = master_key.ChildKey(44 + HARDEN).ChildKey(195 + HARDEN).ChildKey(0 + HARDEN).ChildKey(0).ChildKey(0)
            self.private_key = child_key.PrivateKey().hex()
            
            private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
            vk = private_key_obj.get_verifying_key()
            public_key = b"\x04" + vk.to_string()
            
            sha256 = hashlib.sha256(public_key).digest()
            ripemd = hashlib.new('ripemd160', sha256).digest()
            address_bytes = b"\x41" + ripemd
            checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
            self.address = base58.b58encode(address_bytes + checksum).decode()
        else:
            try:
                private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
                vk = private_key_obj.get_verifying_key()
                public_key = b"\x04" + vk.to_string()
                
                sha256 = hashlib.sha256(public_key).digest()
                ripemd = hashlib.new('ripemd160', sha256).digest()
                address_bytes = b"\x41" + ripemd
                checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
                self.address = base58.b58encode(address_bytes + checksum).decode()
            except Exception as e:
                raise ValueError(f"私钥格式错误: {str(e)}")
    
    def get_balance(self):
        return get_balance(self.chain, self.address)
    
    def transfer(self, to_address, amount):
        try:
            if self.chain == "TRON":
                return self._transfer_tron(to_address, amount)
            else:
                return self._transfer_evm(to_address, amount)
        except Exception as e:
            raise Exception(f"转账失败: {str(e)}")
    
    def _transfer_evm(self, to_address, amount):
        nonce = self.web3.eth.get_transaction_count(self.address)
        gas_price = self.web3.eth.gas_price
        chain_id = self.web3.eth.chain_id

        tx = {
            'nonce': nonce,
            'to': to_address,
            'value': self.web3.to_wei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': gas_price,
            'chainId': chain_id
        }

        try:
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            return tx_hash.hex()
        except Exception as e:
            raise Exception(f"EVM 转账失败: {str(e)}")
    
    def estimate_tron_fee(self):
        try:
            tx = self.tron_client.trx.transfer(
                self.address, 
                self.address, 
                10**6
            ).build()

            fee_sun = tx.fee
            fee_trx = fee_sun / 1_000_000

            return {
                "success": True,
                "fee_sun": fee_sun,
                "fee_trx": round(fee_trx, 6),
                "bandwidth": 270,
                "note": "tronpy official estimate"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _transfer_tron(self, to_address, amount):
        try:
            from tronpy.keys import PrivateKey
            
            amount_sun = int(amount * 10**6)
            
            private_key_obj = PrivateKey(bytes.fromhex(self.private_key.strip()))
            
            txn = (
                self.tron_client.trx.transfer(self.address, to_address, amount_sun)
                .build()
                .sign(private_key_obj)
            )
            result = txn.broadcast()
            if result.get('result'):
                return result.get('txid')
            else:
                raise Exception(result.get('message', '广播失败'))
        except Exception as e:
            raise Exception(f"TRX 转账失败: {str(e)}")
    
    def get_wallet_info(self):
        return {
            'chain': self.chain,
            'address': self.address,
            'private_key': self.private_key,
            'mnemonic': self.mnemonic,
            'rpc': self.rpc
        }
    
    @staticmethod
    def get_supported_chains():
        return list(CHAIN_CONFIG.keys())
