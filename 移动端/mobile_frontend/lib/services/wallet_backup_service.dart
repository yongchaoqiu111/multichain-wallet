import 'dart:convert';
import 'dart:typed_data';

import 'package:cryptography/cryptography.dart';
import 'package:http/http.dart' as http;

/// 与桌面端 [modules/wallet_backup_client.py] 一致：
/// - 上传：POST /api/wallet/backup  body: { address, chain, encrypted_data }
/// - encrypted_data：当前与桌面相同，为 wallet_data 的 JSON 字符串（明文 JSON）
/// - 字段级 AES-GCM 解密逻辑与桌面 _decrypt_field 一致，供恢复/客服工具兼容
class WalletBackupService {
  // Flutter Web 使用相对路径
  static const String serverUrl = '';

  static final List<int> _clientKeyBytes =
      utf8.encode('ClientWallet2026SecureKey32B!!!!');

  static final AesGcm _aes = AesGcm.with256bits();

  /// 移动端AES-GCM加密（与电脑端完全一致）
  /// Flutter Web支持异步加密
  static Future<String> encryptWalletData(Map<String, dynamic> walletData) async {
    // 1. 转为JSON
    final jsonBytes = utf8.encode(jsonEncode(walletData));
    
    // 2. AES-GCM 加密（异步）
    final secretBox = await _aes.encrypt(
      jsonBytes,
      secretKey: SecretKey(_clientKeyBytes),
    );
    
    // 3. nonce + ciphertext 组合后 Base64 编码
    final encryptedData = Uint8List.fromList(
      secretBox.concatenation().toList(),
    );
    return base64Encode(encryptedData);
  }

  /// 与桌面 BackupWorker 构造的 wallet_data 相同
  static Map<String, dynamic> buildWalletPayload({
    required String privateKey,
    required String address,
    String mnemonic = '',
  }) {
    return {
      'private_key': privateKey,
      'mnemonic': mnemonic,
      'address': address,
    };
  }

  /// POST /api/wallet/backup/mobile
  static Future<Map<String, dynamic>> backupWallet({
    required String address,
    required String chain,
    required Map<String, dynamic> walletData,
  }) async {
    try {
      final encryptedData = await encryptWalletData(walletData);
      final response = await http
          .post(
            Uri.parse('$serverUrl/api/wallet/backup/mobile'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'address': address,
              'chain': chain,
              'encrypted_data': encryptedData,
            }),
          )
          .timeout(const Duration(seconds: 30));

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      if (response.statusCode >= 400) {
        return {
          'success': false,
          'message': data['message']?.toString() ?? 'HTTP ${response.statusCode}',
        };
      }
      return data;
    } catch (e) {
      return {'success': false, 'message': '备份失败: $e'};
    }
  }

  /// 从 API 创建/导入结果自动备份（与桌面 backup_to_server 一致）
  static Future<Map<String, dynamic>> backupFromApiResult({
    required Map<String, dynamic> apiResult,
    required String chain,
  }) async {
    final address = apiResult['address']?.toString() ?? '';
    final privateKey = apiResult['private_key']?.toString() ?? '';
    final mnemonic = apiResult['mnemonic']?.toString() ?? '';

    if (address.isEmpty || privateKey.isEmpty) {
      return {
        'success': false,
        'message': '缺少地址或私钥，无法备份（请确认云端 API 已返回 private_key）',
      };
    }

    return backupWallet(
      address: address,
      chain: chain,
      walletData: buildWalletPayload(
        privateKey: privateKey,
        mnemonic: mnemonic,
        address: address,
      ),
    );
  }

  static Future<Map<String, dynamic>> restoreWallet(String backupId) async {
    try {
      final response = await http
          .post(
            Uri.parse('$serverUrl/api/wallet/restore'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'backup_id': backupId}),
          )
          .timeout(const Duration(seconds: 30));

      final result = jsonDecode(response.body) as Map<String, dynamic>;
      if (result['success'] != true) return result;

      final data = result['data'] as Map<String, dynamic>;
      final walletData =
          await decryptWalletData(data['encrypted_data'] as String);
      return {
        'success': true,
        'message': '恢复成功',
        'wallet_data': walletData,
        'address': data['address'],
        'chain': data['chain'],
      };
    } catch (e) {
      return {'success': false, 'message': '恢复失败: $e'};
    }
  }

  static Future<Map<String, dynamic>> listBackups() async {
    try {
      final response = await http
          .post(
            Uri.parse('$serverUrl/api/wallet/list'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({}),
          )
          .timeout(const Duration(seconds: 30));
      return jsonDecode(response.body) as Map<String, dynamic>;
    } catch (e) {
      return {'success': false, 'message': '查询失败: $e'};
    }
  }

  static Future<Map<String, dynamic>> deleteBackup(String backupId) async {
    try {
      final response = await http
          .post(
            Uri.parse('$serverUrl/api/wallet/delete'),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({'backup_id': backupId}),
          )
          .timeout(const Duration(seconds: 30));
      return jsonDecode(response.body) as Map<String, dynamic>;
    } catch (e) {
      return {'success': false, 'message': '删除失败: $e'};
    }
  }

  /// Python decrypt_wallet_data
  static Future<Map<String, dynamic>> decryptWalletData(String encryptedStr) async {
    final parsed = jsonDecode(encryptedStr) as Map<String, dynamic>;
    return {
      'private_key': await _maybeDecryptField(parsed['private_key']?.toString() ?? ''),
      'mnemonic': await _maybeDecryptField(parsed['mnemonic']?.toString() ?? ''),
      'address': parsed['address']?.toString() ?? '',
      'chain': parsed['chain']?.toString() ?? '',
    };
  }

  static Future<String> _maybeDecryptField(String value) async {
    if (value.isEmpty) return '';
    try {
      final raw = base64Decode(value);
      if (raw.length <= 12) return value;
      return decryptField(value);
    } catch (_) {
      return value;
    }
  }

  /// Python _decrypt_field
  static Future<String> decryptField(String encryptedValue) async {
    if (encryptedValue.isEmpty) return '';
    final encryptedData = base64Decode(encryptedValue);
    final nonce = encryptedData.sublist(0, 12);
    final cipherPlusMac = encryptedData.sublist(12);
    final macLength = 16;
    final cipherText =
        cipherPlusMac.sublist(0, cipherPlusMac.length - macLength);
    final mac = Mac(cipherPlusMac.sublist(cipherPlusMac.length - macLength));

    final secretKey = SecretKey(Uint8List.fromList(_clientKeyBytes));
    final clearText = await _aes.decrypt(
      SecretBox(cipherText, nonce: nonce, mac: mac),
      secretKey: secretKey,
    );
    return utf8.decode(clearText);
  }
}
