/// API配置 - 统一管理所有API地址
/// 部署时只需修改此文件中的常量
class ApiConfig {
  /// 后端API服务器地址（不含/api路径）
  static const String serverUrl = 'https://api.ai656.top';
  
  /// 钱包API基础路径
  static const String walletApiBaseUrl = '$serverUrl/api';
  
  /// 钱包备份API基础路径
  static const String backupApiBaseUrl = serverUrl;
}
