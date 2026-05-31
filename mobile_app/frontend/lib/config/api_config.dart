/// API配置 - 统一管理所有API地址
/// 部署时只需修改此文件中的常量
class ApiConfig {
  /// 后端API服务器地址（不含协议）
  static const String serverHost = 'api.ai656.top';
  
  /// 后端API服务器地址（完整URL）
  static const String serverUrl = 'https://api.ai656.top';
  
  /// 钱包API基础路径（通过Nginx转发）
  static const String walletApiBaseUrl = '$serverUrl/api';
  
  /// 钱包备份API基础路径（通过Nginx转发）
  static const String backupApiBaseUrl = serverUrl;
  
  /// 竞猜系统API（通过Nginx HTTPS转发）
  static const String bettingApiUrl = '$serverUrl/betting';
}
