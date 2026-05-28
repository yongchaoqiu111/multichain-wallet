# 多链钱包移动端应用

基于 Flutter 开发的多链钱包应用，支持 Android、iOS 和 Web 平台。

## 功能特性

- 钱包创建（助记词生成）
- 私钥导入
- 助记词导入
- 余额查询（TRON/BSC/ETH）
- 转账功能
- 多链支持切换

## 技术栈

- Flutter 3.0+
- Dart
- HTTP API 调用

## 快速开始

### 环境要求

- Flutter SDK 3.0+
- Dart SDK 3.0+

### 安装依赖

```bash
flutter pub get
```

### 运行项目

```bash
# Android
flutter run

# iOS
flutter run -d ios

# Web
flutter run -d chrome
```

### 构建发布版本

```bash
# Android APK
flutter build apk --release

# iOS IPA
flutter build ios --release

# Web
flutter build web
```

## 项目结构

```
lib/
├── main.dart           # 应用入口
└── services/
    └── wallet_api_service.dart  # API 服务封装
```

## API 配置

API 服务地址在 `lib/services/wallet_api_service.dart` 中配置：

```dart
static const String baseUrl = 'https://api.ai656.top/api';
```

## 支持的网络

- TRON
- BSC (Binance Smart Chain)
- ETH (Ethereum)
