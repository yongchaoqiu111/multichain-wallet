"""
大模型 API 配置 Tab
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QGroupBox, QMessageBox,
                             QTextEdit)
from PyQt6.QtGui import QFont
import os
import json
import secrets
import string


class AIAPITab(QWidget):
    """大模型 API 配置界面"""
    
    def __init__(self, data_dir="data"):
        super().__init__()
        self.data_dir = data_dir
        self.config_file = os.path.join(data_dir, "api_config.json")
        self.init_ui()
        self.load_config()
    
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # API Key 显示区域
        key_group = QGroupBox("大模型 API Key")
        key_layout = QVBoxLayout()
        
        # API Key 显示
        key_display_layout = QHBoxLayout()
        self.api_key_display = QLineEdit()
        self.api_key_display.setReadOnly(True)
        self.api_key_display.setFont(QFont("Consolas", 11))
        self.api_key_display.setMinimumHeight(40)
        self.api_key_display.setEchoMode(QLineEdit.EchoMode.Password)
        key_display_layout.addWidget(self.api_key_display)
        
        # 显示/隐藏按钮
        self.toggle_btn = QPushButton("显示")
        self.toggle_btn.setFixedWidth(60)
        self.toggle_btn.clicked.connect(self.toggle_key_visibility)
        key_display_layout.addWidget(self.toggle_btn)
        
        # 复制按钮
        self.copy_btn = QPushButton("复制")
        self.copy_btn.setFixedWidth(60)
        self.copy_btn.clicked.connect(self.copy_key)
        key_display_layout.addWidget(self.copy_btn)
        
        key_layout.addLayout(key_display_layout)
        
        # 重新生成按钮
        self.regenerate_btn = QPushButton("重新生成 API Key")
        self.regenerate_btn.setFont(QFont("Microsoft YaHei", 10))
        self.regenerate_btn.setMinimumHeight(40)
        self.regenerate_btn.setStyleSheet("background-color: #E74C3C; color: white; border-radius: 5px;")
        self.regenerate_btn.clicked.connect(self.regenerate_key)
        key_layout.addWidget(self.regenerate_btn)
        
        # 说明文字
        note_label = QLabel("⚠️ 重新生成后，旧的 API Key 将失效，需要更新大模型的配置")
        note_label.setStyleSheet("color: #E74C3C; padding: 10px;")
        note_label.setWordWrap(True)
        key_layout.addWidget(note_label)
        
        key_group.setLayout(key_layout)
        layout.addWidget(key_group)
        
        # 接口文档链接
        doc_group = QGroupBox("API 接口文档（供大模型调用）")
        doc_layout = QVBoxLayout()
        
        # 文档链接显示
        link_layout = QHBoxLayout()
        self.doc_link_display = QLineEdit()
        self.doc_link_display.setReadOnly(True)
        self.doc_link_display.setFont(QFont("Consolas", 10))
        self.doc_link_display.setMinimumHeight(40)
        self.doc_link_display.setText("http://127.0.0.1:5000/openapi.json")
        link_layout.addWidget(self.doc_link_display)
        
        # 复制文档链接按钮
        self.copy_doc_btn = QPushButton("复制文档链接")
        self.copy_doc_btn.setFixedWidth(120)
        self.copy_doc_btn.clicked.connect(self.copy_doc_link)
        link_layout.addWidget(self.copy_doc_btn)
        
        doc_layout.addLayout(link_layout)
        
        # 说明文字
        doc_note = QLabel("💡 将此链接复制给大模型，大模型可自动读取接口文档并调用")
        doc_note.setStyleSheet("color: #666; padding: 10px;")
        doc_note.setWordWrap(True)
        doc_layout.addWidget(doc_note)
        
        doc_group.setLayout(doc_layout)
        layout.addWidget(doc_group)
        
        layout.addStretch()
    
    def toggle_key_visibility(self):
        """切换 API Key 显示/隐藏"""
        if self.api_key_display.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_display.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_btn.setText("隐藏")
        else:
            self.api_key_display.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_btn.setText("显示")
    
    def copy_key(self):
        """复制 API Key"""
        from PyQt6.QtWidgets import QApplication
        key = self.api_key_display.text()
        clipboard = QApplication.clipboard()
        clipboard.setText(key)
        QMessageBox.information(self, "成功", "API Key 已复制！")
    
    def copy_doc_link(self):
        """复制文档链接"""
        from PyQt6.QtWidgets import QApplication
        link = self.doc_link_display.text()
        clipboard = QApplication.clipboard()
        clipboard.setText(link)
        QMessageBox.information(self, "成功", "文档链接已复制！")
    
    def generate_key(self):
        """生成新的 API Key"""
        characters = string.ascii_letters + string.digits
        return 'ai-' + ''.join(secrets.choice(characters) for _ in range(32))
    
    def load_config(self):
        """加载配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.api_key_display.setText(config.get('api_key', ''))
            except:
                # 如果加载失败，生成新的
                self.api_key_display.setText(self.generate_key())
        else:
            # 首次使用，生成新的
            self.api_key_display.setText(self.generate_key())
    
    def regenerate_key(self):
        """重新生成 API Key"""
        reply = QMessageBox.question(
            self,
            "确认",
            "重新生成 API Key 后，旧的 Key 将失效。\n是否继续？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            new_key = self.generate_key()
            self.api_key_display.setText(new_key)
            self.save_config(new_key)
            QMessageBox.information(self, "成功", "✅ API Key 已重新生成！")
    
    def save_config(self, api_key):
        """保存配置"""
        config = {
            'api_key': api_key
        }
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
