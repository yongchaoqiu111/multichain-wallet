"""
转账Tab - 发送交易
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QComboBox, QDoubleSpinBox,
                             QMessageBox, QGroupBox, QFormLayout, QGridLayout,
                             QSpacerItem, QSizePolicy, QToolButton, QDialog, QFrame)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from modules.wallet_core import MultiChainWallet
from modules.data_manager import DataManager


class TransferDialog(QDialog):
    """转账对话框"""
    
    def __init__(self, parent, wallet, token="", balance=0.0, pre_address="", pre_amount="", pre_memo=""):
        super().__init__(parent)
        self.wallet = wallet
        self.token = token if token else ("BNB" if wallet.chain == "BSC" else "ETH" if wallet.chain == "ETH" else "TRX")
        self.balance = balance
        self.gas_fee = 0.0
        self.pre_address = pre_address
        self.pre_amount = pre_amount
        self.pre_memo = pre_memo
        self.setModal(True)
        self.setMinimumSize(500, 650)
        self.init_ui()
        self.estimate_gas_fee()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"{self.token} 转账")
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title_layout = QHBoxLayout()
        title_label = QLabel(f"{self.token} 转账")
        title_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title_label)
        
        network_label = QLabel(self.wallet.chain)
        network_label.setFont(QFont("Microsoft YaHei", 12))
        network_label.setStyleSheet("color: #666;")
        network_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(network_label)
        
        layout.addLayout(title_layout)
        
        # 收款地址
        address_header = QHBoxLayout()
        address_label = QLabel("收款地址")
        address_label.setFont(QFont("Microsoft YaHei", 10))
        address_header.addWidget(address_label)
        address_header.addStretch()
        layout.addLayout(address_header)
        
        # 地址输入框 + 扫描按钮
        address_input_layout = QHBoxLayout()
        
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText(f"{self.wallet.chain} 地址")
        self.address_input.setFont(QFont("Microsoft YaHei", 11))
        self.address_input.setMinimumHeight(45)
        if self.pre_address:
            self.address_input.setText(self.pre_address)
        self.address_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 0 12px;
                background-color: #fafafa;
            }
            QLineEdit:focus {
                border-color: #4A90E2;
                background-color: white;
            }
        """)
        address_input_layout.addWidget(self.address_input)
        
        # 扫描按钮
        scan_btn = QToolButton()
        scan_btn.setText("")
        scan_btn.setFont(QFont("Microsoft YaHei", 16))
        scan_btn.setFixedSize(45, 45)
        scan_btn.setStyleSheet("""
            QToolButton {
                background-color: #f5f5f5;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
            }
            QToolButton:hover {
                background-color: #e8e8e8;
            }
        """)
        address_input_layout.addWidget(scan_btn)
        
        layout.addLayout(address_input_layout)
        
        # 数量
        amount_header = QHBoxLayout()
        amount_label = QLabel("数量")
        amount_label.setFont(QFont("Microsoft YaHei", 10))
        amount_header.addWidget(amount_label)
        
        self.balance_label = QLabel(f"{self.balance} {self.token}")
        self.balance_label.setFont(QFont("Microsoft YaHei", 12))
        self.balance_label.setStyleSheet("color: #666;")
        amount_header.addWidget(self.balance_label)
        
        layout.addLayout(amount_header)
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0")
        self.amount_input.setFont(QFont("Microsoft YaHei", 32, QFont.Weight.Light))
        self.amount_input.setMinimumHeight(80)
        if self.pre_amount:
            self.amount_input.setText(self.pre_amount)
        self.amount_input.setStyleSheet("""
            QLineEdit {
                border: none;
                border-bottom: 2px solid #e0e0e0;
                padding: 0;
            }
            QLineEdit:focus {
                border-bottom-color: #4A90E2;
            }
        """)
        layout.addWidget(self.amount_input)
        
        # 备注
        layout.addWidget(QLabel("备注 (可选)"))
        
        self.memo_input = QLineEdit()
        self.memo_input.setPlaceholderText("添加备注")
        self.memo_input.setFont(QFont("Microsoft YaHei", 10))
        self.memo_input.setMinimumHeight(40)
        if self.pre_memo:
            self.memo_input.setText(self.pre_memo)
        self.memo_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 0 12px;
                background-color: #fafafa;
            }
            QLineEdit:focus {
                border-color: #4A90E2;
                background-color: white;
            }
        """)
        layout.addWidget(self.memo_input)
        
        # 矿工费
        layout.addWidget(QLabel("矿工费"))
        
        fee_frame = QFrame()
        fee_frame.setStyleSheet("""
            QFrame {
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        fee_layout = QHBoxLayout(fee_frame)
        
        self.fee_label = QLabel("计算中...")
        self.fee_label.setFont(QFont("Microsoft YaHei", 12))
        fee_layout.addWidget(self.fee_label)
        
        layout.addWidget(fee_frame)
        
        layout.addStretch()
        
        # 下一步按钮
        self.next_btn = QPushButton("下一步")
        self.next_btn.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        self.next_btn.setMinimumHeight(55)
        self.next_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2868A0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.next_btn.clicked.connect(self.accept)
        layout.addWidget(self.next_btn)
    
    def estimate_gas_fee(self):
        """计算矿工费"""
        try:
            if self.wallet.chain == "TRON":
                # TRON 动态计算：根据当前带宽价格
                try:
                    import requests
                    # 获取当前带宽价格
                    res = requests.get("https://api.trongrid.io/wallet/getbandwidthprices", timeout=5)
                    if res.status_code == 200:
                        data = res.json()
                        # TRX 转账消耗约 270 带宽点
                        bandwidth_cost = 270
                        # 计算费用（单位：sun，1 TRX = 1,000,000 sun）
                        if 'prices' in data and len(data['prices']) > 0:
                            latest_price = data['prices'][-1] / 1e6  # 转换为 TRX
                            self.gas_fee = round(bandwidth_cost * latest_price / 1e6, 6)
                        else:
                            self.gas_fee = 0.00345
                    else:
                        self.gas_fee = 0.00345
                except:
                    self.gas_fee = 0.00345
                self.fee_label.setText(f"~{self.gas_fee} TRX (估算)")
            else:
                gas_price = self.wallet.web3.eth.gas_price
                gas_limit = 21000
                fee_wei = gas_price * gas_limit
                fee_eth = self.wallet.web3.from_wei(fee_wei, 'ether')
                self.gas_fee = float(fee_eth)
                
                symbol = "ETH" if self.wallet.chain == "ETH" else "BNB"
                self.fee_label.setText(f"{self.gas_fee:.6f} {symbol}")
        except Exception as e:
            self.fee_label.setText(f"无法计算: {str(e)}")
    
    def get_transfer_data(self):
        """获取转账数据"""
        return {
            'address': self.address_input.text().strip(),
            'amount': float(self.amount_input.text() or "0"),
            'gas_fee': self.gas_fee
        }


class TransferTab(QWidget):
    """转账界面"""
    
    def __init__(self, data_dir="data", wallet_callback=None):
        super().__init__()
        self.data_manager = DataManager(data_dir)
        self.get_current_wallet = wallet_callback
        self.current_network = "BSC"
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 选择币种
        token_group = QGroupBox("选择币种")
        token_layout = QHBoxLayout()
        
        self.token_combo = QComboBox()
        self.token_combo.setFont(QFont("Microsoft YaHei", 10))
        self.token_combo.setMinimumHeight(40)
        self.update_token_list()
        
        token_layout.addWidget(QLabel("币种:"))
        token_layout.addWidget(self.token_combo)
        token_layout.addStretch()
        token_group.setLayout(token_layout)
        layout.addWidget(token_group)
        
        # 转账表单
        transfer_group = QGroupBox("转账")
        transfer_layout = QVBoxLayout()
        
        # 收款地址
        address_label = QLabel("收款地址")
        transfer_layout.addWidget(address_label)
        
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("请输入收款地址")
        self.address_input.setFont(QFont("Microsoft YaHei", 10))
        self.address_input.setMinimumHeight(40)
        transfer_layout.addWidget(self.address_input)
        
        # 转账金额
        amount_label = QLabel("转账金额")
        transfer_layout.addWidget(amount_label)
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0.00")
        self.amount_input.setFont(QFont("Microsoft YaHei", 10))
        self.amount_input.setMinimumHeight(40)
        transfer_layout.addWidget(self.amount_input)
        
        # 备注
        memo_label = QLabel("备注 (可选)")
        transfer_layout.addWidget(memo_label)
        
        self.memo_input = QLineEdit()
        self.memo_input.setPlaceholderText("添加备注")
        self.memo_input.setFont(QFont("Microsoft YaHei", 10))
        self.memo_input.setMinimumHeight(40)
        transfer_layout.addWidget(self.memo_input)
        
        # 矿工费显示
        fee_label = QLabel("矿工费")
        transfer_layout.addWidget(fee_label)
        
        self.fee_display = QLabel("自动计算")
        self.fee_display.setFont(QFont("Microsoft YaHei", 10))
        self.fee_display.setStyleSheet("color: #666;")
        transfer_layout.addWidget(self.fee_display)
        
        transfer_group.setLayout(transfer_layout)
        layout.addWidget(transfer_group)
        
        # 转账按钮
        self.transfer_btn = QPushButton("确认转账")
        self.transfer_btn.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.transfer_btn.setMinimumHeight(50)
        self.transfer_btn.setStyleSheet("""
            QPushButton {
                background-color: #4A90E2;
                color: white;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #357ABD;
            }
            QPushButton:pressed {
                background-color: #2868A0;
            }
        """)
        self.transfer_btn.clicked.connect(self.start_transfer)
        
        layout.addWidget(self.transfer_btn)
        
        layout.addStretch()
    
    def update_token_list(self):
        """更新币种列表"""
        chain = self.current_network
        self.token_combo.clear()
        
        token_map = {
            "ETH": ["ETH", "USDT", "USDC"],
            "BSC": ["BNB", "USDT", "BUSD"],
            "TRON": ["TRX", "USDT"],
            "POLYGON": ["MATIC", "USDT"],
            "AVALANCHE": ["AVAX", "USDT"]
        }
        
        tokens = token_map.get(chain, ["未知"])
        self.token_combo.addItems(tokens)
    
    def on_network_changed(self, network):
        """网络切换回调"""
        self.current_network = network
        self.update_token_list()
    
    def start_transfer(self):
        """开始转账"""
        if not self.get_current_wallet:
            QMessageBox.warning(self, "警告", "请先在钱包管理Tab创建或导入钱包")
            return
        
        wallet = self.get_current_wallet()
        if not wallet:
            QMessageBox.warning(self, "警告", "请先在钱包管理Tab创建或导入钱包")
            return
        
        # 打开转账对话框
        token = self.token_combo.currentText()
        try:
            balance = wallet.get_balance()
        except:
            balance = 0.0
        
        dialog = TransferDialog(self, wallet, token, balance, self.address_input.text(), self.amount_input.text(), self.memo_input.text())
        if dialog.exec() == 1:
            # 用户确认转账
            data = dialog.get_transfer_data()
            to_address = data['address']
            amount = data['amount']
            
            if not to_address:
                QMessageBox.warning(self, "警告", "请输入接收地址")
                return
            
            if amount <= 0:
                QMessageBox.warning(self, "警告", "请输入有效的转账金额")
                return
            
            # 确认转账
            token = self.token_combo.currentText()
            symbol = token
            
            # 检查余额是否足够（金额+手续费）
            try:
                balance = wallet.get_balance()
                total_needed = amount + dialog.gas_fee
                if balance < total_needed:
                    QMessageBox.warning(self, "余额不足", 
                                       f"余额不足！\n\n"
                                       f"当前余额: {balance} {symbol}\n"
                                       f"转账金额: {amount} {symbol}\n"
                                       f"矿工费: {dialog.gas_fee:.6f} {symbol}\n"
                                       f"需要总额: {total_needed:.6f} {symbol}")
                    return
            except:
                pass
            
            reply = QMessageBox.question(self, "确认转账",
                                        f"确认转账信息：\n\n"
                                        f"网络: {wallet.chain}\n"
                                        f"币种: {token}\n"
                                        f"接收地址: {to_address[:10]}...{to_address[-8:]}\n"
                                        f"转账金额: {amount} {symbol}\n"
                                        f"矿工费: {dialog.gas_fee:.6f} {symbol}\n\n"
                                        f"是否继续？",
                                        QMessageBox.StandardButton.Yes | 
                                        QMessageBox.StandardButton.No)
            
            if reply != QMessageBox.StandardButton.Yes:
                return
            
            try:
                # 执行转账
                tx_hash = wallet.transfer(to_address, amount)
                
                # 保存交易记录
                tx_record = DataManager.create_transaction_record(
                    address=wallet.address,
                    chain=wallet.chain,
                    tx_type="send",
                    amount=amount,
                    to_address=to_address,
                    tx_hash=tx_hash,
                    status="success"
                )
                self.data_manager.save_transaction(tx_record)
                
                # 显示结果
                QMessageBox.information(self, "成功", f"转账成功！\n\n交易哈希:\n{tx_hash}")
                
            except Exception as e:
                error_msg = f"转账失败: {str(e)}"
                QMessageBox.critical(self, "错误", error_msg)
