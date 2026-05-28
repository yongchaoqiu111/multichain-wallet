"""
数据管理模块 - 钱包和交易记录持久化
"""
import json
import os
import base64
from datetime import datetime
from cryptography.fernet import Fernet


class DataManager:
    """数据管理类"""
    
    # 固定加密密钥
    _key = b'roIxknl_IVXKuGcLDFculnzibdbGBsvF5IxB2TTxsGY='
    
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.wallets_file = os.path.join(data_dir, "wallets.json")
        self.transactions_file = os.path.join(data_dir, "transactions.json")
        self.settings_file = os.path.join(data_dir, "settings.json")
    
    def save_wallet(self, wallet_info):
        """
        保存钱包信息
        :param wallet_info: 钱包信息字典
        """
        wallets = self.load_wallets()
        
        # 检查是否已存在相同地址和网络的钱包
        for i, wallet in enumerate(wallets):
            if wallet.get('address') == wallet_info['address'] and wallet.get('chain') == wallet_info['chain']:
                wallets[i] = wallet_info
                self._save_json(self.wallets_file, wallets)
                return
        
        # 添加新钱包
        wallets.append(wallet_info)
        self._save_json(self.wallets_file, wallets)
    
    def load_wallets(self):
        """加载所有钱包"""
        return self._load_json(self.wallets_file, [])
    
    def delete_wallet(self, address, chain=None):
        """删除钱包"""
        wallets = self.load_wallets()
        if chain:
            # 按地址 + 网络组合删除
            wallets = [w for w in wallets if not (w.get('address') == address and w.get('chain') == chain)]
        else:
            # 只按地址删除（兼容旧逻辑）
            wallets = [w for w in wallets if w.get('address') != address]
        print(f"删除钱包: {address} ({chain}), 剩余钱包数: {len(wallets)}")
        self._save_json(self.wallets_file, wallets)
    
    def save_transaction(self, tx_record):
        """
        保存交易记录
        :param tx_record: 交易记录字典
        """
        transactions = self.load_transactions()
        transactions.append(tx_record)
        self._save_json(self.transactions_file, transactions)
    
    def load_transactions(self):
        """加载交易记录"""
        return self._load_json(self.transactions_file, [])
    
    def get_transactions_by_address(self, address):
        """根据地址获取交易记录"""
        transactions = self.load_transactions()
        return [tx for tx in transactions if tx.get('address') == address]
    
    def save_settings(self, settings):
        """保存设置"""
        self._save_json(self.settings_file, settings)
    
    def load_settings(self):
        """加载设置"""
        default_settings = {
            'default_chain': 'BSC',
            'language': 'zh'
        }
        return self._load_json(self.settings_file, default_settings)
    
    def _load_json(self, filepath, default=None):
        """加载JSON文件(自动解密)"""
        if default is None:
            default = {}
            
        if not os.path.exists(filepath):
            return default
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                encrypted_data = f.read()
                
            # 解密
            fernet = Fernet(self._key)
            decrypted_data = fernet.decrypt(encrypted_data.encode())
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception:
            # 如果是旧版本明文文件,尝试直接读取
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return default
    
    def _save_json(self, filepath, data):
        """保存JSON文件(自动加密)"""
        try:
            # 加密
            fernet = Fernet(self._key)
            json_data = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
            encrypted_data = fernet.encrypt(json_data).decode('utf-8')
                
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(encrypted_data)
        except Exception as e:
            raise Exception(f"保存文件失败: {str(e)}")
    
    @staticmethod
    def create_transaction_record(address, chain, tx_type, amount, to_address, tx_hash, status="pending"):
        """
        创建交易记录
        :param address: 钱包地址
        :param chain: 链名称
        :param tx_type: 交易类型 (send/receive)
        :param amount: 金额
        :param to_address: 接收地址
        :param tx_hash: 交易哈希
        :param status: 状态
        :return: 交易记录字典
        """
        return {
            'address': address,
            'chain': chain,
            'type': tx_type,
            'amount': amount,
            'to_address': to_address,
            'tx_hash': tx_hash,
            'status': status,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
