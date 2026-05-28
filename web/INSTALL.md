# 多链钱包 - 移动端部署文档

## 项目结构

```
F:\web\
├── backend/                    # 后端 API 服务
│   └── wallet_api_service.py   # Flask API 服务
├── modules/                    # 核心模块
│   ├── wallet_core.py          # 钱包核心逻辑（TRON地址生成使用tronpy）
│   └── config.py               # 链配置
├── frontend/                   # Flutter 前端
│   ├── lib/
│   │   ├── main.dart           # 主应用
│   │   ├── config/
│   │   │   └── api_config.dart # API配置
│   │   └── services/
│   │       ├── wallet_api_service.dart      # API服务调用
│   │       ├── wallet_backup_service.dart   # 钱包备份服务
│   │       └── wallet_storage.dart          # 本地存储
│   ── pubspec.yaml            # Flutter依赖
├── wallet_backup.sql           # 数据库表结构
── INSTALL.md                  # 本安装文档
```

## 环境要求

### 服务器端
- **操作系统**: Ubuntu 22.04 或更高版本
- **Python**: 3.13（必须，Python 3.10 不支持 ripemd160）
- **MySQL**: 8.0+
- **Nginx**: 用于反向代理和 HTTPS

### 开发端
- **Flutter**: 3.x
- **Dart**: 3.x

## 服务器端部署

### 1. 安装 Python 3.13

```bash
# 安装依赖
apt update && apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget curl llvm libncursesw5-dev xz-utils \
    tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev

# 下载并编译 Python 3.13
cd /root
wget https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tgz
tar -xf Python-3.13.0.tgz
cd Python-3.13.0
./configure --prefix=/opt/python3.13
make -j4
make install

# 创建软链接
ln -s /opt/python3.13/bin/python3.13 /usr/local/bin/python3.13
ln -s /opt/python3.13/bin/pip3.13 /usr/local/bin/pip3.13

# 验证
python3.13 --version
```

### 2. 安装 Python 依赖

```bash
pip3.13 install flask flask-cors bip32utils base58 ecdsa pycryptodome \
    mnemonic tronpy web3 mysql-connector-python
```

### 3. 修补 bip32utils 库（支持 ripemd160）

```python
#!/usr/bin/env python3
import sys

bip32utils_path = '/opt/python3.13/lib/python3.13/site-packages/bip32utils/BIP32Key.py'

with open(bip32utils_path, 'r') as f:
    content = f.read()

if 'from Crypto.Hash import RIPEMD160' not in content:
    content = content.replace(
        'import hashlib',
        'import hashlib\nfrom Crypto.Hash import RIPEMD160'
    )

content = content.replace(
    "hashlib.new('ripemd160', sha256(cK).digest()).digest()",
    "RIPEMD160.new(sha256(cK).digest()).digest()"
)

content = content.replace(
    "hashlib.new('ripemd160', sha256(pk_bytes).digest()).digest()",
    "RIPEMD160.new(sha256(pk_bytes).digest()).digest()"
)

content = content.replace(
    "hashlib.new('ripemd160', sha256(script_sig).digest()).digest()",
    "RIPEMD160.new(sha256(script_sig).digest()).digest()"
)

with open(bip32utils_path, 'w') as f:
    f.write(content)

print('bip32utils patched successfully!')
```

### 4. 部署代码

```bash
# 创建目录
mkdir -p /root/wallet/modules

# 上传文件（从本地 F:\web 上传）
# backend/wallet_api_service.py -> /root/wallet/wallet_api_service.py
# modules/wallet_core.py -> /root/wallet/modules/wallet_core.py
# modules/config.py -> /root/wallet/modules/config.py
```

### 5. 配置环境变量

创建 `/root/wallet/.env` 文件：

```env
# API服务配置
API_HOST=0.0.0.0
API_PORT=5000

# 数据库配置
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=YourPassword
DB_NAME=wallet_backup

# 调试模式
DEBUG=false
```

### 6. 初始化数据库

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE wallet_backup CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 导入表结构
mysql -u root -p wallet_backup < /root/wallet/wallet_backup.sql
```

### 7. 启动服务

```bash
# 清除缓存
find /root/wallet -name '__pycache__' -exec rm -rf {} + 2>/dev/null
find /root/wallet -name '*.pyc' -delete 2>/dev/null

# 后台运行
cd /root/wallet
nohup python3.13 wallet_api_service.py >> api.log 2>&1 &

# 查看日志
tail -f api.log

# 测试服务
curl http://127.0.0.1:5000/api/health
```

### 8. 配置 Nginx（HTTPS）

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 前端部署（Flutter）

### 1. 修改 API 配置

编辑 `frontend/lib/config/api_config.dart`：

```dart
class ApiConfig {
  static const String baseUrl = 'https://api.yourdomain.com';
}
```

### 2. 安装 Flutter 依赖

```bash
cd frontend
flutter pub get
```

### 3. 运行应用

```bash
# Android
flutter run

# iOS
flutter run -d ios

# Web
flutter run -d chrome
```

### 4. 打包 APK

```bash
flutter build apk --release
```

## 关键修复说明

### TRON 地址生成问题

**问题**: 手动实现的地址生成算法（ecdsa + RIPEMD160）生成错误的地址

**修复**: 
1. `wallet_core.py` 使用 `tronpy.keys.PrivateKey` 生成地址
2. `wallet_api_service.py` 导入 `modules.wallet_core.MultiChainWallet`，不定义本地类

**验证**:
```python
from tronpy.keys import PrivateKey
pk = PrivateKey(bytes.fromhex(private_key))
address = pk.public_key.to_base58check_address()
# 正确地址: TSfXD9bidCC2fojPUhXNvtJger5yUEnqb7
```

## 测试验证

### 1. 测试助记词导入

```python
#!/usr/bin/env python3
import requests

url = "http://127.0.0.1:5000/api/wallet/import/mnemonic"
data = {
    "mnemonic": "aisle define upon property force sentence country tonight wife autumn normal entry",
    "chain": "TRON"
}

response = requests.post(url, json=data)
print(response.json())
# 应返回: {"address": "TSfXD9bidCC2fojPUhXNvtJger5yUEnqb7", ...}
```

### 2. 检查服务状态

```bash
# 查看进程
ps aux | grep wallet_api

# 查看端口
lsof -i :5000

# 查看日志
tail -100 /root/wallet/api.log
```

## 常见问题

### Python 版本问题
- 必须使用 Python 3.13，Python 3.10 不支持 ripemd160

### 地址不一致
- 确保 `wallet_api_service.py` 没有定义本地 `MultiChainWallet` 类
- 确保从 `modules.wallet_core` 导入

### 服务无法启动
- 检查端口是否被占用: `lsof -i :5000`
- 清除 Python 缓存: `find . -name '__pycache__' -exec rm -rf {} +`
- 查看日志: `tail -f api.log`

## 维护命令

```bash
# 重启服务
pkill -9 -f wallet_api
cd /root/wallet && nohup python3.13 wallet_api_service.py >> api.log 2>&1 &

# 查看日志
tail -f /root/wallet/api.log

# 备份数据库
mysqldump -u root -p wallet_backup > backup_$(date +%Y%m%d).sql
```

## 技术支持

如有问题，请检查：
1. Python 版本是否为 3.13
2. bip32utils 是否已修补
3. wallet_api_service.py 是否正确导入 MultiChainWallet
4. 数据库连接是否正常
