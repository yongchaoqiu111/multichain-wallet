"""
交易记录Tab - 查看历史交易
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QTextEdit,
                             QPushButton, QHBoxLayout, QGroupBox, 
                             QComboBox, QMessageBox)
from PyQt6.QtGui import QFont
from modules.data_manager import DataManager


class TransactionHistoryTab(QWidget):
    """交易记录界面"""
    
    def __init__(self, data_dir="data"):
        super().__init__()
        self.data_manager = DataManager(data_dir)
        self.init_ui()
        self.load_transactions()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 筛选区域
        filter_group = QGroupBox("筛选条件")
        filter_layout = QHBoxLayout()
        
        self.address_filter = QComboBox()
        self.address_filter.setFont(QFont("Microsoft YaHei", 10))
        self.address_filter.setMinimumWidth(300)
        self.address_filter.addItem("全部地址")
        
        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.setFont(QFont("Microsoft YaHei", 10))
        self.refresh_btn.clicked.connect(self.load_transactions)
        
        filter_layout.addWidget(QLabel("钱包地址:"))
        filter_layout.addWidget(self.address_filter)
        filter_layout.addWidget(self.refresh_btn)
        filter_layout.addStretch()
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 交易记录显示
        record_group = QGroupBox("交易记录")
        record_layout = QVBoxLayout()
        
        self.tx_display = QTextEdit()
        self.tx_display.setReadOnly(True)
        self.tx_display.setFont(QFont("Consolas", 9))
        
        record_layout.addWidget(self.tx_display)
        record_group.setLayout(record_layout)
        layout.addWidget(record_group)
        
        # 导出按钮
        btn_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("导出为文本")
        self.export_btn.setFont(QFont("Microsoft YaHei", 10))
        self.export_btn.clicked.connect(self.export_transactions)
        
        self.clear_btn = QPushButton("清空记录")
        self.clear_btn.setFont(QFont("Microsoft YaHei", 10))
        self.clear_btn.clicked.connect(self.clear_transactions)
        
        btn_layout.addWidget(self.export_btn)
        btn_layout.addWidget(self.clear_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
    
    def load_transactions(self):
        """加载交易记录"""
        transactions = self.data_manager.load_transactions()
        
        if not transactions:
            self.tx_display.setPlainText("暂无交易记录")
            return
        
        # 更新地址筛选器
        addresses = set(tx.get('address', '') for tx in transactions)
        self.address_filter.clear()
        self.address_filter.addItem("全部地址")
        for addr in sorted(addresses):
            display_addr = f"{addr[:10]}...{addr[-8:]}"
            self.address_filter.addItem(display_addr, addr)
        
        # 获取筛选的地址
        selected_addr = self.address_filter.currentData()
        
        if selected_addr:
            filtered_txs = [tx for tx in transactions if tx.get('address') == selected_addr]
        else:
            filtered_txs = transactions
        
        # 格式化显示
        text = ""
        for i, tx in enumerate(reversed(filtered_txs), 1):
            symbol = self._get_symbol(tx.get('chain', ''))
            status_icon = "✅" if tx.get('status') == 'success' else "⏳"
            
            text += f"{status_icon} 交易 #{i}\n"
            text += f"时间: {tx.get('timestamp', 'N/A')}\n"
            text += f"网络: {tx.get('chain', 'N/A')}\n"
            text += f"类型: {'发送' if tx.get('type') == 'send' else '接收'}\n"
            text += f"金额: {tx.get('amount', 0)} {symbol}\n"
            text += f"地址: {tx.get('to_address', 'N/A')}\n"
            text += f"哈希: {tx.get('tx_hash', 'N/A')}\n"
            text += "-" * 60 + "\n\n"
        
        self.tx_display.setPlainText(text)
    
    def _get_symbol(self, chain):
        """获取链的币种符号"""
        symbols = {
            'TRON': 'TRX',
            'BSC': 'BNB',
            'ETH': 'ETH',
            'POLYGON': 'MATIC',
            'AVALANCHE': 'AVAX'
        }
        return symbols.get(chain, 'UNKNOWN')
    
    def export_transactions(self):
        """导出交易记录"""
        transactions = self.data_manager.load_transactions()
        
        if not transactions:
            QMessageBox.warning(self, "警告", "没有可导出的交易记录")
            return
        
        text = "交易记录导出\n"
        text += "=" * 80 + "\n\n"
        
        for i, tx in enumerate(transactions, 1):
            symbol = self._get_symbol(tx.get('chain', ''))
            text += f"交易 #{i}\n"
            text += f"时间: {tx.get('timestamp', 'N/A')}\n"
            text += f"网络: {tx.get('chain', 'N/A')}\n"
            text += f"类型: {'发送' if tx.get('type') == 'send' else '接收'}\n"
            text += f"金额: {tx.get('amount', 0)} {symbol}\n"
            text += f"地址: {tx.get('to_address', 'N/A')}\n"
            text += f"哈希: {tx.get('tx_hash', 'N/A')}\n"
            text += "-" * 80 + "\n\n"
        
        try:
            with open("transactions_export.txt", "w", encoding="utf-8") as f:
                f.write(text)
            
            QMessageBox.information(self, "成功", 
                                   "交易记录已导出到:\ntransactions_export.txt")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def clear_transactions(self):
        """清空交易记录"""
        reply = QMessageBox.question(self, "确认", 
                                    "确定要清空所有交易记录吗？\n此操作不可恢复！",
                                    QMessageBox.StandardButton.Yes | 
                                    QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            from modules.data_manager import DataManager
            dm = DataManager()
            dm._save_json(dm.transactions_file, [])
            self.load_transactions()
            QMessageBox.information(self, "成功", "交易记录已清空")
