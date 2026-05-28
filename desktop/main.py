"""
多链钱包工具 - 主程序入口
技术栈: PyQt6 + Web3 + TronPy
"""
import sys
import os
import threading
from flask import Flask, request, jsonify
from web3 import Web3
from tronpy import Tron

# 禁用 jaraco 模块，避免 pkg_resources 报错
if 'jaraco' in sys.modules:
    del sys.modules['jaraco']
sys.modules['jaraco'] = type(sys)('jaraco')

# 打包后添加modules到路径
if getattr(sys, 'frozen', False):
    # 打包后的EXE环境
    application_path = os.path.dirname(sys.executable)
else:
    # 开发环境
    application_path = os.path.dirname(os.path.abspath(__file__))

# 添加modules目录到sys.path
modules_path = os.path.join(application_path, 'modules')
if os.path.exists(modules_path) and modules_path not in sys.path:
    sys.path.insert(0, application_path)
    sys.path.insert(0, modules_path)

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt6.QtGui import QFont

# 导入业务模块
from modules.wallet_tab import WalletManagementTab
from modules.transfer_tab import TransferTab
from modules.transaction_tab import TransactionHistoryTab
from modules.asset_query_tab import AssetQueryTab
from modules.ai_api_tab import AIAPITab
from modules.earning_tab import EarningEstimationTab


class MultiChainWalletApp(QMainWindow):
    """多链钱包主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("演示钱包版本 此钱包仅作样品演示  作者telegram: @ca666g")
        self.setGeometry(100, 100, 1000, 700)
        self.showMaximized()
        self.raise_()
        self.activateWindow()
        
        # 设置数据目录（打包兼容）
        if getattr(sys, 'frozen', False):
            # 打包后的EXE环境
            self.data_dir = os.path.join(os.path.dirname(sys.executable), 'data')
        else:
            # 开发环境
            self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
        
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 当前钱包引用
        self.current_wallet = None
        
        # 初始化UI
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # 顶部网络选择栏
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("当前网络:"))
        
        self.network_combo = QComboBox()
        self.network_combo.setFont(QFont("Microsoft YaHei", 10))
        self.network_combo.setMinimumWidth(120)
        self.network_combo.addItems(["TRON", "BSC", "ETH"])
        self.network_combo.currentTextChanged.connect(self.on_network_changed)
        
        top_bar.addWidget(self.network_combo)
        top_bar.addStretch()
        
        main_layout.addLayout(top_bar)
        
        # 创建Tab控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont("Microsoft YaHei", 10))
        
        # 添加各个功能Tab
        self.wallet_tab = WalletManagementTab(self.data_dir)
        self.asset_query_tab = AssetQueryTab(
            self.data_dir,
            wallet_callback=self.get_current_wallet
        )
        self.transfer_tab = TransferTab(
            self.data_dir, 
            wallet_callback=self.get_current_wallet
        )
        self.transaction_tab = TransactionHistoryTab(self.data_dir)
        self.earning_tab = EarningEstimationTab(
            wallet_callback=self.get_current_wallet
        )
        self.ai_api_tab = AIAPITab(self.data_dir)
        
        self.tab_widget.addTab(self.wallet_tab, "钱包管理")
        self.tab_widget.addTab(self.asset_query_tab, "资产查询")
        self.tab_widget.addTab(self.transfer_tab, "转账")
        self.tab_widget.addTab(self.transaction_tab, "交易记录")
        self.tab_widget.addTab(self.earning_tab, "收益预估")
        self.tab_widget.addTab(self.ai_api_tab, "大模型API")
        
        # 默认显示钱包管理Tab
        self.tab_widget.setCurrentIndex(0)
        
        main_layout.addWidget(self.tab_widget)
        
        # 启动内置 API 服务器
        # self.start_api_server()  # 暂时禁用
    
    def on_network_changed(self, network):
        """网络切换"""
        # 通知所有Tab网络已切换
        if hasattr(self.wallet_tab, 'on_network_changed'):
            self.wallet_tab.on_network_changed(network)
        if hasattr(self.transfer_tab, 'on_network_changed'):
            self.transfer_tab.on_network_changed(network)
        if hasattr(self.asset_query_tab, 'on_network_changed'):
            self.asset_query_tab.on_network_changed(network)
    
    def get_current_wallet(self):
        """获取当前钱包实例"""
        return self.wallet_tab.current_wallet
    
    def start_api_server(self):
        """启动内置 API 服务器（供大模型调用）"""
        from modules.data_manager import DataManager
        
        app = Flask(__name__)
        data_manager = DataManager(self.data_dir)
        
        # 加载 API Key
        import json
        config_path = os.path.join(self.data_dir, 'api_config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            api_key = config.get('api_key', 'ai-wallet-query-2026')
        except:
            api_key = 'ai-wallet-query-2026'
        
        # RPC 配置
        CHAIN_RPC = {
            'BSC': 'https://bsc-dataseed.binance.org/',
            'ETH': 'https://eth.llamarpc.com',
            'TRON': None
        }
        
        @app.before_request
        def check_api_key():
            """验证 API Key"""
            if request.path.startswith('/api/'):
                key = request.headers.get('X-API-Key', '')
                if key != api_key:
                    return jsonify({'success': False, 'message': 'Invalid API Key'}), 403
        
        @app.route('/api/wallet/balance', methods=['POST'])
        def query_balance():
            """查询主币余额"""
            try:
                data = request.get_json()
                address = data.get('address')
                chain = data.get('chain', 'BSC')
                
                if not address:
                    return jsonify({'success': False, 'message': 'Missing address'}), 400
                
                if chain == 'TRON':
                    # TRON 查询
                    tron = Tron(network='mainnet')
                    balance = tron.get_account_balance(address)
                    return jsonify({
                        'success': True,
                        'balance': float(balance),
                        'symbol': 'TRX',
                        'chain': chain,
                        'address': address
                    })
                else:
                    # BSC/ETH 查询
                    rpc_url = CHAIN_RPC.get(chain)
                    if not rpc_url:
                        return jsonify({'success': False, 'message': f'Unsupported chain: {chain}'}), 400
                    
                    w3 = Web3(Web3.HTTPProvider(rpc_url))
                    if not w3.is_connected():
                        return jsonify({'success': False, 'message': 'RPC connection failed'}), 500
                    
                    balance_wei = w3.eth.get_balance(address)
                    balance_eth = w3.from_wei(balance_wei, 'ether')
                    symbol = 'BNB' if chain == 'BSC' else 'ETH'
                    
                    return jsonify({
                        'success': True,
                        'balance': float(balance_eth),
                        'symbol': symbol,
                        'chain': chain,
                        'address': address
                    })
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500
        
        @app.route('/api/wallet/token_balance', methods=['POST'])
        def query_token_balance():
            """查询代币余额"""
            try:
                data = request.get_json()
                address = data.get('address')
                token_address = data.get('token_address')
                chain = data.get('chain', 'BSC')
                
                if not address or not token_address:
                    return jsonify({'success': False, 'message': 'Missing address or token_address'}), 400
                
                if chain == 'TRON':
                    return jsonify({'success': False, 'message': 'TRON token balance not supported yet'}), 400
                
                rpc_url = CHAIN_RPC.get(chain)
                w3 = Web3(Web3.HTTPProvider(rpc_url))
                
                # ERC20 ABI (简化版)
                erc20_abi = [{
                    'constant': True,
                    'inputs': [{'name': '_owner', 'type': 'address'}],
                    'name': 'balanceOf',
                    'outputs': [{'name': 'balance', 'type': 'uint256'}],
                    'type': 'function'
                }, {
                    'constant': True,
                    'inputs': [],
                    'name': 'decimals',
                    'outputs': [{'name': '', 'type': 'uint8'}],
                    'type': 'function'
                }]
                
                contract = w3.eth.contract(address=token_address, abi=erc20_abi)
                balance = contract.functions.balanceOf(address).call()
                decimals = contract.functions.decimals().call()
                
                balance_formatted = balance / (10 ** decimals)
                
                return jsonify({
                    'success': True,
                    'balance': balance_formatted,
                    'token_address': token_address,
                    'chain': chain,
                    'address': address
                })
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500
        
        @app.route('/openapi.json', methods=['GET'])
        def openapi_spec():
            """OpenAPI 文档（供大模型自动发现接口）"""
            return jsonify({
                "openapi": "3.0.0",
                "info": {
                    "title": "多链钱包 API",
                    "version": "1.0.0",
                    "description": "本地钱包查询接口，仅供本机大模型调用"
                },
                "servers": [
                    {"url": "http://127.0.0.1:5000"}
                ],
                "paths": {
                    "/api/wallet/balance": {
                        "post": {
                            "summary": "查询主币余额",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "address": {"type": "string", "description": "钱包地址"},
                                                "chain": {"type": "string", "enum": ["BSC", "ETH", "TRON"], "default": "TRON"}
                                            },
                                            "required": ["address"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "成功",
                                    "content": {
                                        "application/json": {
                                            "schema": {
                                                "type": "object",
                                                "properties": {
                                                    "success": {"type": "boolean"},
                                                    "balance": {"type": "number"},
                                                    "symbol": {"type": "string"},
                                                    "chain": {"type": "string"},
                                                    "address": {"type": "string"}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "/api/wallet/token_balance": {
                        "post": {
                            "summary": "查询代币余额",
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "type": "object",
                                            "properties": {
                                                "address": {"type": "string", "description": "钱包地址"},
                                                "token_address": {"type": "string", "description": "代币合约地址"},
                                                "chain": {"type": "string", "enum": ["BSC", "ETH"], "default": "BSC"}
                                            },
                                            "required": ["address", "token_address"]
                                        }
                                    }
                                }
                            },
                            "responses": {
                                "200": {
                                    "description": "成功"
                                }
                            }
                        }
                    }
                },
                "components": {
                    "securitySchemes": {
                        "ApiKeyAuth": {
                            "type": "apiKey",
                            "in": "header",
                            "name": "X-API-Key"
                        }
                    }
                },
                "security": [
                    {"ApiKeyAuth": []}
                ]
            })
        
        def run_server():
            """在后台线程运行 Flask 服务器"""
            app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
        
        # 启动服务器线程
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        print("API server started: http://127.0.0.1:5000")
        print(f"API Key: {api_key}")
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        event.accept()


def main():
    try:
        print("[START] 正在启动应用...")
        print("[DEBUG] Before QApplication")
        app = QApplication(sys.argv)
        print("[INFO] QApplication 创建成功")
        app.setStyle('Fusion')
        
        print("[DEBUG] Before MultiChainWalletApp")
        window = MultiChainWalletApp()
        print("[INFO] 主窗口创建成功")
        window.show()
        window.raise_()
        window.activateWindow()
        print("[INFO] 窗口已显示")
        
        sys.exit(app.exec())
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        with open('error.log', 'w', encoding='utf-8') as f:
            f.write(error_msg)
        print(f"[ERROR] 启动失败: {e}")
        print(error_msg)
        input("Press Enter to exit...")


if __name__ == '__main__':
    main()
