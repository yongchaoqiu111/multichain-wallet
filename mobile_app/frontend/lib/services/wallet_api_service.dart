import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';

class WalletApiException implements Exception {
  final String message;
  WalletApiException(this.message);
  @override
  String toString() => message;
}

class WalletApiService {
  static const String baseUrl = ApiConfig.walletApiBaseUrl;
  static const Duration _timeout = Duration(seconds: 30);

  static Future<Map<String, dynamic>> _post(
    String path,
    Map<String, dynamic> body,
  ) async {
    final response = await http
        .post(
          Uri.parse('$baseUrl$path'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(_timeout);

    Map<String, dynamic> data;
    try {
      data = jsonDecode(response.body) as Map<String, dynamic>;
    } catch (_) {
      throw WalletApiException('服务器返回异常: ${response.statusCode}');
    }

    if (response.statusCode >= 400) {
      throw WalletApiException(data['message']?.toString() ?? '请求失败');
    }
    if (data['success'] == false) {
      throw WalletApiException(data['message']?.toString() ?? '操作失败');
    }
    return data;
  }

  static Future<Map<String, dynamic>> createWallet(String chain) =>
      _post('/wallet/create', {'chain': chain});

  static Future<Map<String, dynamic>> importPrivateKey(
    String privateKey,
    String chain,
  ) =>
      _post('/wallet/import/private_key', {
        'private_key': privateKey,
        'chain': chain,
      });

  static Future<Map<String, dynamic>> importMnemonic(
    String mnemonic,
    String chain,
  ) =>
      _post('/wallet/import/mnemonic', {
        'mnemonic': mnemonic,
        'chain': chain,
      });

  static Future<Map<String, dynamic>> getBalance({
    required String address,
    required String chain,
    String? token,
    String? sessionId,
  }) =>
      _post('/wallet/balance', {
        'address': address,
        'chain': chain,
        if (token != null && token.isNotEmpty) 'token': token,
        if (sessionId != null) 'session_id': sessionId,
      });

  static Future<Map<String, dynamic>> transfer({
    required String sessionId,
    required String toAddress,
    required double amount,
    required String chain,
    String? memo,
    String? privateKey,
    String? mnemonic,
  }) =>
      _post('/wallet/transfer', {
        'session_id': sessionId,
        'to_address': toAddress,
        'amount': amount,
        'chain': chain,
        if (memo != null && memo.isNotEmpty) 'memo': memo,
        if (privateKey != null && privateKey.isNotEmpty) 'private_key': privateKey,
        if (mnemonic != null && mnemonic.isNotEmpty) 'mnemonic': mnemonic,
      });

  static Future<Map<String, dynamic>> estimateFee({
    required String sessionId,
    required String chain,
  }) =>
      _post('/wallet/estimate_fee', {
        'session_id': sessionId,
        'chain': chain,
      });

  /// 会话失效时用本地私钥/助记词重新获取 session_id
  static Future<String> refreshSession({
    required String chain,
    String? privateKey,
    String? mnemonic,
  }) async {
    Map<String, dynamic> result;
    if (mnemonic != null && mnemonic.trim().isNotEmpty) {
      result = await importMnemonic(mnemonic.trim(), chain);
    } else if (privateKey != null && privateKey.trim().isNotEmpty) {
      result = await importPrivateKey(privateKey.trim(), chain);
    } else {
      throw WalletApiException('无法恢复会话：缺少私钥或助记词');
    }
    return result['session_id'] as String;
  }

  static Future<Map<String, dynamic>> healthCheck() async {
    final response = await http
        .get(Uri.parse('$baseUrl/health'))
        .timeout(_timeout);
    return jsonDecode(response.body) as Map<String, dynamic>;
  }
}
