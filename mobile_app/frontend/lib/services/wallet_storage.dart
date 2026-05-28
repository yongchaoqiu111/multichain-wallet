import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class WalletStorage {
  static const _walletsKey = 'wallets_v1';
  static const _transactionsKey = 'transactions_v1';
  static const _activeKey = 'active_wallet_v1';

  static Future<List<Map<String, dynamic>>> loadWallets() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_walletsKey);
    if (raw == null || raw.isEmpty) return [];
    final list = jsonDecode(raw) as List<dynamic>;
    return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  static Future<void> saveWallet(Map<String, dynamic> wallet) async {
    final wallets = await loadWallets();
    final idx = wallets.indexWhere(
      (w) =>
          w['address'] == wallet['address'] && w['chain'] == wallet['chain'],
    );
    if (idx >= 0) {
      wallets[idx] = wallet;
    } else {
      wallets.add(wallet);
    }
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_walletsKey, jsonEncode(wallets));
  }

  static Future<void> deleteWallet(String address, String chain) async {
    final wallets = await loadWallets();
    wallets.removeWhere(
      (w) => w['address'] == address && w['chain'] == chain,
    );
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_walletsKey, jsonEncode(wallets));
  }

  static Future<void> setActiveWallet(String? address, String? chain) async {
    final prefs = await SharedPreferences.getInstance();
    if (address == null) {
      await prefs.remove(_activeKey);
      return;
    }
    await prefs.setString(_activeKey, jsonEncode({'address': address, 'chain': chain}));
  }

  static Future<Map<String, String>?> getActiveWallet() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_activeKey);
    if (raw == null) return null;
    final m = jsonDecode(raw) as Map<String, dynamic>;
    return {'address': m['address'] as String, 'chain': m['chain'] as String};
  }

  static Future<List<Map<String, dynamic>>> loadTransactions() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_transactionsKey);
    if (raw == null || raw.isEmpty) return [];
    final list = jsonDecode(raw) as List<dynamic>;
    return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }

  static Future<void> addTransaction(Map<String, dynamic> tx) async {
    final list = await loadTransactions();
    list.insert(0, tx);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_transactionsKey, jsonEncode(list));
  }

  static Future<void> clearTransactions() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_transactionsKey);
  }
}
