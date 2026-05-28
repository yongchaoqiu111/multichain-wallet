"""
多链钱包核心模块
支持 BSC / ETH / TRON / Polygon / Avalanche
"""
from web3 import Web3
from tronpy import Tron
from tronpy.providers import HTTPProvider
from mnemonic import Mnemonic
from bip32utils import BIP32Key
import hashlib
import time
import requests


# ==============================================================================
# 1. 自定义异常类（规范错误处理）
# ==============================================================================
class WalletError(Exception):
    """钱包基础异常"""
    pass

class InvalidChainError(WalletError):
    """不支持的链"""
    pass

class InvalidAddressError(WalletError):
    """地址格式错误"""
    pass

class NodeRequestError(WalletError):
    """节点请求失败"""
    pass


# ==============================================================================
# 2. 全局唯一链配置（消除重复）
# ==============================================================================
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

# ==============================================================================
# 3. 余额缓存（5秒有效期，避免重复 RPC 请求）
# ==============================================================================
_balance_cache = {}
_CACHE_TTL = 5  # 缓存有效期（秒）


def _get_cached_balance(chain: str, address: str) -> tuple:
    """
    获取缓存余额
    :return: (balance, is_cached)
    """
    cache_key = f"{chain}:{address}"
    if cache_key in _balance_cache:
        cached = _balance_cache[cache_key]
        if time.time() - cached['timestamp'] < _CACHE_TTL:
            return cached['balance'], True
        else:
            del _balance_cache[cache_key]
    return None, False


def _set_cached_balance(chain: str, address: str, balance: float):
    """设置缓存余额"""
    cache_key = f"{chain}:{address}"
    _balance_cache[cache_key] = {
        'balance': balance,
        'timestamp': time.time()
    }


def _get_trx_balance(nodes, address):
    """TRON 独立查询，不串任何链"""
    if not address.startswith("T"):
        raise InvalidAddressError(f"TRON 地址必须 T 开头: {address}")

    for node in nodes:
        try:
            url = f"{node.rstrip('/')}/wallet/getaccount"
            data = {
                "address": address,
                "visible": True
            }
            res = requests.post(url, json=data, timeout=8)
            if res.status_code == 200:
                result = res.json()
                sun = result.get("balance", 0)
                trx = int(sun) / 10**6
                return trx
        except Exception as e:
            print(f"[DEBUG] TRON 节点 {node} 失败: {e}")
            continue
    raise NodeRequestError("所有 TRON 节点查询失败")


def _get_evm_balance(chain, nodes, address, decimals):
    """ETH/BSC 独立查询，不串任何链"""
    if not address.startswith("0x"):
        raise InvalidAddressError(f"{chain} 地址必须 0x 开头: {address}")
    
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
            print(f"[DEBUG] {chain} 节点 {node} 失败: {e}")
            continue
    raise NodeRequestError(f"所有 {chain} 节点查询失败")


def get_balance(chain: str, address: str):
    """
    多链 + 多节点 + 不串钱包 + 缓存
    安全标准接口
    """
    # 1. 先查缓存
    cached_balance, is_cached = _get_cached_balance(chain, address)
    if is_cached:
        print(f"[缓存] {chain} {address[:8]}... 余额: {cached_balance}")
        return cached_balance
    
    # 2. 缓存失效，查询链配置
    if chain not in CHAIN_CONFIG:
        raise InvalidChainError(f"不支持的链: {chain}")

    config = CHAIN_CONFIG[chain]
    nodes = config["nodes"]
    decimals = config["decimals"]

    # 3. 执行查询
    if chain == "TRON":
        balance = _get_trx_balance(nodes, address)
    else:
        balance = _get_evm_balance(chain, nodes, address, decimals)
    
    # 4. 写入缓存
    _set_cached_balance(chain, address, balance)
    print(f"[RPC] {chain} {address[:8]}... 余额: {balance}")
    return balance


class MultiChainWallet:
    """多链钱包核心类"""
    
    def __init__(self, chain="BSC", private_key=None, mnemonic=None):
        """
        初始化钱包
        :param chain: 区块链网络 (BSC/ETH/TRON/POLYGON/AVALANCHE)
        :param private_key: 私钥（留空则创建新钱包）
        :param mnemonic: 助记词（12个单词，可选）
        """
        if chain not in CHAIN_CONFIG:
            raise InvalidChainError(f"不支持的链: {chain}")
        
        self.chain = chain
        self.rpc = CHAIN_CONFIG[chain]["nodes"][0]  # 使用主节点
        self.private_key = private_key
        self.mnemonic = mnemonic
        self.address = None
        self.web3 = None
        self.tron_client = None
        
        self._load_or_create_wallet()
    
    def _load_or_create_wallet(self):
        """加载或创建钱包"""
        # 如果有助记词，先从助记词生成私钥
        if self.mnemonic:
            self.private_key = self._mnemonic_to_private_key(self.mnemonic)
        
        if self.chain == "TRON":
            self._init_tron_wallet()
        else:
            self._init_evm_wallet()
    
    def _mnemonic_to_private_key(self, mnemonic_words, account_index=0):
        """助记词转私钥 - BIP32标准推导"""
        mnemo = Mnemonic("english")
        seed = mnemo.to_seed(mnemonic_words)
        
        # BIP44 HD路径: m/44'/coin_type'/account'/change/address_index
        HARDEN = 0x80000000
        
        # 根据链类型选择 coin_type
        if self.chain == "TRON":
            coin_type = 195
        elif self.chain in ["ETH", "BSC"]:
            coin_type = 60
        else:
            coin_type = 60  # 默认 ETH
        
        master_key = BIP32Key.fromEntropy(seed)
        child_key = master_key.ChildKey(44 + HARDEN).ChildKey(coin_type + HARDEN).ChildKey(account_index + HARDEN).ChildKey(0).ChildKey(0)
        
        return child_key.PrivateKey().hex()
    
    def derive_address(self, account_index=0):
        """从助记词派生指定索引的地址"""
        if not self.mnemonic:
            raise ValueError("没有助记词，无法派生地址")
        
        private_key = self._mnemonic_to_private_key(self.mnemonic, account_index)
        
        if self.chain == "TRON":
            import ecdsa
            import hashlib
            import base58
            from Crypto.Hash import RIPEMD160
            
            private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(private_key), curve=ecdsa.SECP256k1)
            vk = private_key_obj.get_verifying_key()
            public_key = b"\x04" + vk.to_string()
            
            sha256 = hashlib.sha256(public_key).digest()
            ripemd = RIPEMD160.new(sha256).digest()
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
        """初始化EVM兼容链钱包（BSC/ETH/Polygon/Avalanche）"""
        self.web3 = Web3(Web3.HTTPProvider(self.rpc))
        
        if not self.private_key:
            # 创建新钱包 - 先生成助记词
            mnemo = Mnemonic("english")
            self.mnemonic = mnemo.generate(128)  # 12个单词
            
            # 从助记词生成私钥 - BIP32标准推导 (ETH/BSC用44'/60'/0'/0/0)
            seed = mnemo.to_seed(self.mnemonic)
            HARDEN = 0x80000000
            master_key = BIP32Key.fromEntropy(seed)
            child_key = master_key.ChildKey(44 + HARDEN).ChildKey(60 + HARDEN).ChildKey(0 + HARDEN).ChildKey(0).ChildKey(0)
            self.private_key = child_key.PrivateKey().hex()
            
            # 生成地址
            account = self.web3.eth.account.from_key(self.private_key)
            self.address = account.address
        else:
            # 导入钱包
            account = self.web3.eth.account.from_key(self.private_key)
            self.address = account.address
    
    def _init_tron_wallet(self):
        """初始化TRON钱包"""
        import ecdsa
        import hashlib
        import base58
        
        config = CHAIN_CONFIG.get(self.chain, {})
        api_key = config.get("api_key")
        
        # tronpy 官方方式：HTTPProvider 直接传 api_key 参数
        if api_key and api_key != "TRON-PRO-API-KEY":
            self.tron_client = Tron(HTTPProvider(api_key=api_key))
        else:
            self.tron_client = Tron(HTTPProvider(self.rpc))
        
        if not self.private_key:
            # 创建新钱包 - 先生成助记词
            mnemo = Mnemonic("english")
            self.mnemonic = mnemo.generate(128)  # 12个单词
            
            # 从助记词生成私钥 - BIP32标准推导 (TRON用44'/195'/0'/0/0)
            seed = mnemo.to_seed(self.mnemonic)
            HARDEN = 0x80000000
            master_key = BIP32Key.fromEntropy(seed)
            child_key = master_key.ChildKey(44 + HARDEN).ChildKey(195 + HARDEN).ChildKey(0 + HARDEN).ChildKey(0).ChildKey(0)
            self.private_key = child_key.PrivateKey().hex()
            
            # 生成公钥
            private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
            vk = private_key_obj.get_verifying_key()
            public_key = b"\x04" + vk.to_string()
            
            # 生成地址
            sha256 = hashlib.sha256(public_key).digest()
            ripemd = hashlib.new('ripemd160', sha256).digest()
            address_bytes = b"\x41" + ripemd
            
            # 双哈希校验
            checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
            self.address = base58.b58encode(address_bytes + checksum).decode()
        else:
            # 导入已有钱包 - 使用和新建钱包相同的地址生成算法
            private_key_obj = ecdsa.SigningKey.from_string(bytes.fromhex(self.private_key), curve=ecdsa.SECP256k1)
            vk = private_key_obj.get_verifying_key()
            public_key = b"\x04" + vk.to_string()
            
            sha256 = hashlib.sha256(public_key).digest()
            ripemd = hashlib.new('ripemd160', sha256).digest()
            address_bytes = b"\x41" + ripemd
            
            checksum = hashlib.sha256(hashlib.sha256(address_bytes).digest()).digest()[:4]
            self.address = base58.b58encode(address_bytes + checksum).decode()
    
    def get_balance(self):
        """
        查询余额
        :return: 余额（单位：主币）
        """
        return get_balance(self.chain, self.address)
    
    def transfer(self, to_address, amount):
        """
        转账
        :param to_address: 接收地址
        :param amount: 金额（单位：主币）
        :return: 交易哈希
        """
        try:
            if self.chain == "TRON":
                return self._transfer_tron(to_address, amount)
            else:
                return self._transfer_evm(to_address, amount)
        except Exception as e:
            raise Exception(f"转账失败: {str(e)}")
    
    def _transfer_evm(self, to_address, amount):
        """EVM链转账（主流钱包标准版）"""
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
        """TRON 官方手续费预估（tronpy 原生）"""
        try:
            # 构建一笔假交易只用于预估费用，不广播
            tx = self.tron_client.trx.transfer(
                self.address, 
                self.address, 
                10**6
            ).build()

            # 官方获取手续费
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
        """TRON 主币转账 - 使用 tronpy 标准 API"""
        try:
            from tronpy.keys import PrivateKey
            
            amount_sun = int(amount * 10**6)
            
            # 私钥转成 tronpy 认可的 PrivateKey 对象
            private_key_obj = PrivateKey(bytes.fromhex(self.private_key.strip()))
            
            txn = (
                self.tron_client.trx.transfer(self.address, to_address, amount_sun)
                .build()
                .sign(private_key_obj)  # 传 PrivateKey 对象，不是字符串
            )
            result = txn.broadcast()
            if result.get('result'):
                return result.get('txid')
            else:
                raise Exception(result.get('message', '广播失败'))
        except Exception as e:
            raise Exception(f"TRX 转账失败: {str(e)}")
    
    def get_wallet_info(self):
        """
        获取钱包信息
        :return: 字典包含地址、私钥、链信息
        """
        return {
            'chain': self.chain,
            'address': self.address,
            'private_key': self.private_key,
            'mnemonic': self.mnemonic,
            'rpc': self.rpc
        }
    
    @staticmethod
    def get_supported_chains():
        """获取支持的链列表"""
        return list(CHAIN_CONFIG.keys())
