"""
资产查询Tab - 查询所有链的余额和自定义代币
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTextEdit, QGroupBox, QLineEdit,
                             QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QComboBox, QFormLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from modules.wallet_core import MultiChainWallet
from modules.data_manager import DataManager


class BalanceWorker(QThread):
    """余额查询后台线程"""
    finished = pyqtSignal(float)
    error = pyqtSignal(str)
    
    def __init__(self, chain, private_key, token_info=None):
        super().__init__()
        self.chain = chain
        self.private_key = private_key
        self.token_info = token_info
    
    def run(self):
        try:
            if self.token_info and self.token_info['type'] == 'token':
                # 查询代币余额
                if self.chain == 'TRON':
                    # TRC20 代币查询
                    import requests
                    from modules.wallet_core import CHAIN_CONFIG
                    
                    contract_address = self.token_info['contract']
                    # 从私钥获取地址
                    from tronpy.keys import PrivateKey
                    from tronpy import Tron
                    address = PrivateKey(bytes.fromhex(self.private_key)).public_key.to_base58check_address()
                    
                    # Base58 地址转 Hex（去掉 0x 前缀）
                    client = Tron()
                    address_hex = client.to_hex_address(address).lower().replace('0x', '')
                    
                    # 调用 TronGrid API 查询 TRC20 余额（正确方式，parameter 补 64 位）
                    nodes = CHAIN_CONFIG['TRON']['nodes']
                    balance = 0.0
                    
                    for node in nodes:
                        try:
                            url = f"{node.rstrip('/')}/wallet/triggerconstantcontract"
                            data = {
                                "contract_address": contract_address,
                                "function_selector": "balanceOf(address)",
                                "parameter": address_hex.zfill(64),
                                "owner_address": address,
                                "visible": True
                            }
                            resp = requests.post(url, json=data, timeout=8)
                            
                            if resp.status_code == 200:
                                result = resp.json()
                                if "constant_result" in result and len(result["constant_result"]) > 0:
                                    hex_balance = result["constant_result"][0]
                                    balance = int(hex_balance, 16) / 10**6
                                    print(f"[TRC20] {address[:8]}... 余额: {balance}")
                                    break
                        except Exception as e:
                            continue
                    
                    self.finished.emit(balance)
                elif self.chain in ['BSC', 'ETH', 'POLYGON', 'AVALANCHE']:
                    # ERC20/BEP20 代币查询
                    from web3 import Web3
                    from modules.wallet_core import CHAIN_CONFIG
                    
                    rpc = CHAIN_CONFIG[self.chain]['nodes'][0]
                    w3 = Web3(Web3.HTTPProvider(rpc))
                    contract_address = self.token_info['contract']
                    
                    abi = [{
                        "constant": True,
                        "inputs": [{"name": "_owner", "type": "address"}],
                        "name": "balanceOf",
                        "outputs": [{"name": "balance", "type": "uint256"}],
                        "type": "function"
                    }]
                    
                    # 从私钥获取地址
                    account = w3.eth.account.from_key(self.private_key)
                    contract = w3.eth.contract(address=contract_address, abi=abi)
                    balance_raw = contract.functions.balanceOf(account.address).call()
                    
                    symbol = self.token_info['symbol']
                    decimals = 6 if symbol == 'USDT' else 18
                    balance = balance_raw / (10 ** decimals)
                    self.finished.emit(balance)
                else:
                    self.finished.emit(0.0)
            else:
                # 查询主币余额
                temp_wallet = MultiChainWallet(chain=self.chain, private_key=self.private_key)
                balance = temp_wallet.get_balance()
                self.finished.emit(balance)
        except Exception as e:
            print(f"BalanceWorker error: {e}")
            self.error.emit(str(e))


class AssetQueryTab(QWidget):
    """资产查询界面"""
    
    # 主流币种默认列表（链 -> 币种信息）
    DEFAULT_TOKENS = {
        'BTC': {
            'name': '比特币',
            'symbol': 'BTC',
            'type': 'native'  # 主币
        },
        'ETH': {
            'name': '以太坊',
            'symbol': 'ETH',
            'type': 'native'
        },
        'TRX': {
            'name': '波场',
            'symbol': 'TRX',
            'type': 'native'
        },
        'BNB': {
            'name': '币安币',
            'symbol': 'BNB',
            'type': 'native'
        },
        'MATIC': {
            'name': 'Polygon',
            'symbol': 'MATIC',
            'type': 'native'
        },
        'AVAX': {
            'name': '雪崩',
            'symbol': 'AVAX',
            'type': 'native'
        },
        'ETH-USDT': {
            'name': 'Tether USD (ETH)',
            'symbol': 'USDT',
            'type': 'token',
            'chain': 'ETH',
            'contract': '0xdAC17F958D2ee523a2206206994597C13D831ec7'
        },
        'BSC-USDT': {
            'name': 'Tether USD (BSC)',
            'symbol': 'USDT',
            'type': 'token',
            'chain': 'BSC',
            'contract': '0x55d398326f99059fF775485246999027B3197955'
        },
        'TRON-USDT': {
            'name': 'Tether USD (TRON)',
            'symbol': 'USDT',
            'type': 'token',
            'chain': 'TRON',
            'contract': 'TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t'
        }
    }
    
    def __init__(self, data_dir="data", wallet_callback=None):
        super().__init__()
        self.data_manager = DataManager(data_dir)
        self.get_current_wallet = wallet_callback
        self.custom_tokens = {}  # 用户自定义代币
        self.current_network = "BSC"
        self.init_ui()
        self.load_default_tokens()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 2级选项：选择币种
        token_group = QGroupBox("选择币种")
        token_layout = QHBoxLayout()
        
        self.token_combo = QComboBox()
        self.token_combo.setFont(QFont("Microsoft YaHei", 10))
        self.token_combo.setMinimumWidth(300)
        self.token_combo.currentTextChanged.connect(self.on_token_changed)
        
        token_layout.addWidget(QLabel("币种:"))
        token_layout.addWidget(self.token_combo)
        token_layout.addStretch()
        
        token_group.setLayout(token_layout)
        layout.addWidget(token_group)
        
        # 余额显示区域
        balance_group = QGroupBox("余额信息")
        balance_layout = QFormLayout()
        
        self.balance_label = QLabel("0.000000")
        self.balance_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        
        self.refresh_btn = QPushButton("刷新余额")
        self.refresh_btn.setFont(QFont("Microsoft YaHei", 10))
        self.refresh_btn.setMinimumHeight(35)
        self.refresh_btn.clicked.connect(self.refresh_balance)
        
        balance_layout.addRow("当前余额:", self.balance_label)
        balance_layout.addRow("", self.refresh_btn)
        
        balance_group.setLayout(balance_layout)
        layout.addWidget(balance_group)
        
        layout.addStretch()
        
        # 初始化币种列表
        self.update_token_list("BSC")
    
    def load_default_tokens(self):
        """加载默认主流币种（已废弃，改用动态加载）"""
        pass
    
    def on_network_changed(self, network):
        """网络切换回调"""
        self.current_network = network
        self.update_token_list(network)
    
    def update_token_list(self, chain):
        """更新币种列表"""
        # 临时断开信号，避免触发on_token_changed
        self.token_combo.currentTextChanged.disconnect(self.on_token_changed)
        
        self.token_combo.clear()
        
        # 根据链添加对应的币种
        chain = chain.upper()
        
        if chain == "BSC":
            self.token_combo.addItem("BNB (主币)", {"type": "native", "symbol": "BNB"})
            self.token_combo.addItem("USDT (BEP20)", {"type": "token", "symbol": "USDT", "contract": "0x55d398326f99059fF775485246999027B3197955"})
        elif chain == "ETH":
            self.token_combo.addItem("ETH (主币)", {"type": "native", "symbol": "ETH"})
            self.token_combo.addItem("USDT (ERC20)", {"type": "token", "symbol": "USDT", "contract": "0xdAC17F958D2ee523a2206206994597C13D831ec7"})
        elif chain == "TRON":
            self.token_combo.addItem("TRX (主币)", {"type": "native", "symbol": "TRX"})
            self.token_combo.addItem("USDT (TRC20)", {"type": "token", "symbol": "USDT", "contract": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t"})
        elif chain == "POLYGON":
            self.token_combo.addItem("MATIC (主币)", {"type": "native", "symbol": "MATIC"})
            self.token_combo.addItem("USDT (Polygon)", {"type": "token", "symbol": "USDT", "contract": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"})
        elif chain == "AVALANCHE":
            self.token_combo.addItem("AVAX (主币)", {"type": "native", "symbol": "AVAX"})
            self.token_combo.addItem("USDT (Avalanche)", {"type": "token", "symbol": "USDT", "contract": "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7"})
        
        # 重新连接信号
        self.token_combo.currentTextChanged.connect(self.on_token_changed)
    
    def on_token_changed(self, token_name):
        """币种切换时不自动查询，等待用户点击刷新"""
        pass
    
    def refresh_balance(self):
        """刷新当前选中币种的余额（异步）"""
        if not self.get_current_wallet:
            QMessageBox.warning(self, "警告", "请先在钱包管理Tab创建或导入钱包")
            return
        
        wallet = self.get_current_wallet()
        if not wallet:
            QMessageBox.warning(self, "警告", "请先在钱包管理Tab创建或导入钱包")
            return
        
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("查询中...")
        self.balance_label.setText("查询中...")
        
        # 启动后台线程查询
        chain = self.current_network
        token_info = self.token_combo.currentData()
        
        self.worker = BalanceWorker(chain, wallet.private_key, token_info)
        self.worker.finished.connect(self.on_balance_loaded)
        self.worker.error.connect(self.on_balance_error)
        self.worker.start()
    
    def on_balance_loaded(self, balance):
        """余额查询成功"""
        self.balance_label.setText(f"{balance:.6f}")
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("刷新余额")
    
    def on_balance_error(self, error_msg):
        """余额查询失败"""
        QMessageBox.critical(self, "错误", f"查询失败: {error_msg}")
        self.balance_label.setText("查询失败")
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("刷新余额")
    

    
    def _get_chain_symbol(self, chain):
        """获取链的币种符号"""
        symbols = {
            'TRON': 'TRX',
            'BSC': 'BNB',
            'ETH': 'ETH',
            'POLYGON': 'MATIC',
            'AVALANCHE': 'AVAX'
        }
        return symbols.get(chain, 'UNKNOWN')
