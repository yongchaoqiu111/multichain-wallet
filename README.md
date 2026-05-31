# 多链钱包 (Multi-Chain Wallet)

一个支持 TRON、Ethereum、BSC 等多链资产管理的加密货币钱包应用。

## 特性

- 🔐 **安全加密** - 助记词和私钥采用 AES-GCM 加密存储
- 🌐 **多链支持** - TRON、Ethereum、BSC 等多条区块链
- 📱 **跨平台** - Android、iOS、Windows 桌面客户端
-  **资产管理** - 查看余额、交易记录、资产查询
- 🔄 **转账功能** - 支持链上转账和跨链兑换
- 🎯 **竞猜系统** - 虚拟赛事竞猜功能

## 项目结构

```
qianbao/
├── mobile_app/          # 移动端应用
│   ├── frontend/        # Flutter 移动端前端
│   └── backend/         # Flask 移动端后端 API
├── desktop/             # Windows 桌面客户端
── modules/             # 共享模块（钱包核心、配置等）
├── backend/             # 后端 API 服务
── data/                # 数据文件
```

## 快速开始

### 环境要求

- Python 3.8+
- Flutter 3.x
- MySQL 5.7+
- Node.js 16+ (可选，用于前端)

### 后端配置

1. 复制配置示例文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，填入你的配置：
```env
DB_HOST=localhost
DB_USER=your_user
DB_PASSWORD=your_password
CLIENT_KEY=your_32_byte_key
SERVER_KEY=your_32_byte_key
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 启动后端服务：
```bash
cd backend
python server.py
```

### 移动端编译

#### Android

1. 进入 Flutter 项目目录：
```bash
cd mobile_app/frontend
```

2. 配置签名（可选，用于正式发布）：
   - 生成密钥：`keytool -genkey -v -keystore wallet-release.keystore -alias wallet -keyalg RSA -keysize 2048 -validity 10000`
   - 创建 `android/key.properties` 文件

3. 编译 APK：
```bash
# Debug 版本
flutter build apk --debug

# Release 版本
flutter build apk --release
```

输出位置：`build/app/outputs/flutter-apk/app-release.apk`

#### iOS

需要 macOS 环境：
```bash
cd mobile_app/frontend
flutter build ios --release
```

### 桌面客户端

```bash
cd desktop
python main.py
```

## 安全说明

### 加密机制

- **客户端加密**：敏感数据（助记词、私钥）在客户端使用 `CLIENT_KEY` 加密
- **服务器加密**：服务器使用 `SERVER_KEY` 对数据进行二次加密
- **传输加密**：所有 API 通信使用 HTTPS

### 密钥管理

- 生成随机密钥：
```python
import os
key = os.urandom(32).hex()
print(key)  # 64位十六进制字符串
```

- **重要**：丢失密钥将无法解密钱包数据！

## 数据库配置

### 初始化数据库

```sql
CREATE DATABASE wallet_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 数据表结构

项目包含以下主要数据表：
- `wallets` - 钱包信息
- `transactions` - 交易记录
- `users` - 用户信息
- `backups` - 备份记录

## API 文档

### 钱包管理

- `POST /api/wallet/create` - 创建钱包
- `GET /api/wallet/list` - 获取钱包列表
- `POST /api/wallet/backup` - 备份钱包
- `GET /api/wallet/balance` - 查询余额

### 交易管理

- `POST /api/transaction/send` - 发送交易
- `GET /api/transaction/history` - 交易历史

## 区块链节点配置

### TRON

```env
TRON_NODE_URL=https://api.trongrid.io
TRON_GRID_API_KEY=your_api_key
```

### Ethereum

```env
ETH_NODE_URL=https://eth-mainnet.g.alchemy.com/v2/your_key
```

### BSC

```env
BSC_NODE_URL=https://bsc-dataseed.binance.org
```

## 常见问题

### Q: 如何重置数据库？
A: 删除 `data/` 目录下的数据库文件，重新运行初始化脚本。

### Q: 忘记加密密钥怎么办？
A: 密钥无法找回，需要重新创建钱包。请务必妥善保管密钥！

### Q: 支持哪些区块链？
A: 目前支持 TRON、Ethereum、BSC，后续会添加更多链。

## 贡献指南

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 免责声明

本项目仅供学习和研究使用。使用本项目创建的产品时，请遵守当地法律法规。作者不对使用本项目造成的任何损失负责。

## 联系方式

- GitHub Issues: 提交问题和建议
- Email: your-email@example.com

## 致谢

- [tronpy](https://github.com/iontronic/tronpy) - TRON Python SDK
- [web3.py](https://github.com/ethereum/web3.py) - Ethereum Python SDK
- [Flutter](https://flutter.dev/) - 跨平台 UI 框架
- [Flask](https://flask.palletsprojects.com/) - Python Web 框架
