"""
转账对话框 - 参考专业钱包设计
"""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QTextEdit, QComboBox,
                             QMessageBox, QFrame, QToolButton)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QIcon


class TransferDialog(QDialog):
    """转账对话框"""
    
    def __init__(self, parent, wallet, token="", balance=0.0):
        super().__init__(parent, Qt.WindowType.Dialog)
        self.wallet = wallet
        self.token = token if token else ("BNB" if wallet.chain == "BSC" else "ETH" if wallet.chain == "ETH" else "TRX")
        self.balance = balance
        self.gas_fee = 0.0
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
        scan_btn.setText("👤")
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
        self.next_btn.clicked.connect(self.on_next)
        layout.addWidget(self.next_btn)
    
    def estimate_gas_fee(self):
        """计算矿工费"""
        try:
            if self.wallet.chain == "TRON":
                self.gas_fee = 0.3
                self.fee_label.setText(f"0.3 TRX (固定)")
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
    
    def on_next(self):
        """下一步"""
        address = self.address_input.text().strip()
        if not address:
            QMessageBox.warning(self, "提示", "请输入收款地址")
            return
        
        try:
            amount = float(self.amount_input.text() or "0")
        except:
            QMessageBox.warning(self, "提示", "请输入有效数量")
            return
        
        if amount <= 0:
            QMessageBox.warning(self, "提示", "数量必须大于0")
            return
        
        # 返回数据
        self.accept()
    
    def get_transfer_data(self):
        """获取转账数据"""
        return {
            'address': self.address_input.text().strip(),
            'amount': float(self.amount_input.text() or "0"),
            'gas_fee': self.gas_fee
        }
