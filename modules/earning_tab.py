"""
收益预估 Tab
纯展示 · 不操作资金
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QLineEdit, QPushButton, QFormLayout,
                             QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont


class EarningEstimationTab(QWidget):
    """收益预估页面"""
    
    # 年化利率配置
    ANNUAL_RATE = 0.03  # 3%
    DAILY_RATE = (1 + ANNUAL_RATE) ** (1 / 365) - 1
    
    def __init__(self, wallet_callback=None):
        super().__init__()
        self.wallet_callback = wallet_callback
        self.init_ui()
        self.load_current_wallet()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题
        title = QLabel("💰 收益预估")
        title.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 合规说明
        notice = QLabel("⚠️ 资金在用户钱包，无需转账，无需质押，纯收益计算")
        notice.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(notice)
        
        # 输入区域
        input_group = QGroupBox("输入参数")
        input_layout = QFormLayout()
        
        # 链选择
        self.chain_combo = QComboBox()
        self.chain_combo.addItems(["BSC", "ETH", "TRON"])
        self.chain_combo.currentTextChanged.connect(self.on_chain_changed)
        input_layout.addRow("选择链:", self.chain_combo)
        
        # 钱包地址（只读，自动联动）
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("自动显示当前钱包地址")
        self.address_input.setMinimumHeight(30)
        self.address_input.setReadOnly(True)
        input_layout.addRow("钱包地址:", self.address_input)
        
        # 余额
        self.balance_input = QLineEdit()
        self.balance_input.setPlaceholderText("自动获取或手动输入")
        self.balance_input.setMinimumHeight(30)
        input_layout.addRow("钱包余额:", self.balance_input)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 计算按钮
        self.calc_btn = QPushButton("计算收益")
        self.calc_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.calc_btn.setMinimumHeight(40)
        self.calc_btn.clicked.connect(self.calculate_earning)
        layout.addWidget(self.calc_btn)
        
        # 收益结果展示
        self.result_group = QGroupBox("收益预估（纯展示）")
        result_layout = QFormLayout()
        
        self.daily_label = QLabel("--")
        self.daily_label.setFont(QFont("Microsoft YaHei", 10))
        result_layout.addRow("每日预估收益:", self.daily_label)
        
        self.monthly_label = QLabel("--")
        self.monthly_label.setFont(QFont("Microsoft YaHei", 10))
        result_layout.addRow("每月预估收益:", self.monthly_label)
        
        self.yearly_label = QLabel("--")
        self.yearly_label.setFont(QFont("Microsoft YaHei", 10))
        result_layout.addRow("每年预估收益:", self.yearly_label)
        
        self.rate_label = QLabel("3.00%")
        self.rate_label.setFont(QFont("Microsoft YaHei", 10))
        result_layout.addRow("年化利率:", self.rate_label)
        
        self.result_group.setLayout(result_layout)
        layout.addWidget(self.result_group)
        
        layout.addStretch()
        self.setLayout(layout)
    
    def on_chain_changed(self, chain):
        """链切换时更新地址"""
        self.load_current_wallet()
    
    def load_current_wallet(self):
        """加载当前钱包地址"""
        if self.wallet_callback:
            wallet = self.wallet_callback()
            if wallet and hasattr(wallet, 'address'):
                self.address_input.setText(wallet.address)
    
    def get_current_wallet(self):
        """获取当前钱包地址（已废弃，保留兼容）"""
        self.load_current_wallet()
    
    def calculate_earning(self):
        """计算收益"""
        try:
            balance_str = self.balance_input.text().strip()
            if not balance_str:
                QMessageBox.warning(self, "提示", "请输入钱包余额")
                return
            
            balance = float(balance_str)
            
            # 计算收益
            daily_earn = balance * self.DAILY_RATE
            monthly_earn = daily_earn * 30
            yearly_earn = balance * self.ANNUAL_RATE
            
            # 更新显示
            self.daily_label.setText(f"{daily_earn:.6f}")
            self.monthly_label.setText(f"{monthly_earn:.4f}")
            self.yearly_label.setText(f"{yearly_earn:.4f}")
            
            # 显示成功提示
            QMessageBox.information(
                self, 
                "计算完成", 
                f"基于余额 {balance} 的收益预估：\n"
                f"每日: {daily_earn:.6f}\n"
                f"每月: {monthly_earn:.4f}\n"
                f"每年: {yearly_earn:.4f}\n"
                f"\n注：此为理论预估，仅供参考"
            )
            
        except ValueError:
            QMessageBox.warning(self, "错误", "余额格式不正确，请输入数字")
