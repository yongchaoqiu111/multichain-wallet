import 'package:http/http.dart' as http;
import 'dart:convert';
import '../config/api_config.dart';

/// 竞猜系统API服务
class BettingApiService {
  static const String baseUrl = ApiConfig.bettingApiUrl;

  // ==================== 赛事数据板块 ====================

  /// 获取赛事列表
  static Future<Map<String, dynamic>> getMatchesList({
    String game = 'all',
    String status = 'upcoming',
    int page = 1,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/matches/list'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'game': game,
        'status': status,
        'page': page,
      }),
    );
    return json.decode(response.body);
  }

  /// 获取赛事详情
  static Future<Map<String, dynamic>> getMatchDetail(int matchId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/matches/detail'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'match_id': matchId}),
    );
    return json.decode(response.body);
  }

  /// 同步赛事数据（管理员调用）
  static Future<Map<String, dynamic>> syncMatches(String game) async {
    final response = await http.post(
      Uri.parse('$baseUrl/matches/sync'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'game': game}),
    );
    return json.decode(response.body);
  }

  // ==================== 参与竞猜板块 ====================

  /// 查询积分余额
  static Future<Map<String, dynamic>> getPointsBalance(String address) async {
    final response = await http.post(
      Uri.parse('$baseUrl/points/balance'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'address': address}),
    );
    return json.decode(response.body);
  }

  /// USDT转换为积分 (1 USDT = 1 积分)
  static Future<Map<String, dynamic>> convertToPoints(String address, double usdtAmount) async {
    final response = await http.post(
      Uri.parse('$baseUrl/points/convert'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'address': address,
        'usdt_amount': usdtAmount,
      }),
    );
    return json.decode(response.body);
  }

  /// 下注竞猜
  static Future<Map<String, dynamic>> placeBet({
    required String address,
    required int matchId,
    required String matchName,
    required String teamBet,
    required double betAmount,
    double odds = 2.0,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/bet/place'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'address': address,
        'match_id': matchId,
        'match_name': matchName,
        'team_bet': teamBet,
        'bet_amount': betAmount,
        'odds': odds,
      }),
    );
    return json.decode(response.body);
  }

  /// 查询我的竞猜记录
  static Future<Map<String, dynamic>> getMyBets({
    required String address,
    String status = 'all',  // all, pending, won, lost
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/bet/my-bets'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'address': address,
        'status': status,
      }),
    );
    return json.decode(response.body);
  }

  /// 查询积分流水（账单）
  static Future<Map<String, dynamic>> getTransactions(String address) async {
    final response = await http.post(
      Uri.parse('$baseUrl/points/transactions'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'address': address}),
    );
    return json.decode(response.body);
  }

  /// 竞猜结算（管理员调用）
  static Future<Map<String, dynamic>> settleBet(int betId, bool isWin, double actualWin) async {
    final response = await http.post(
      Uri.parse('$baseUrl/bet/settle'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'bet_id': betId,
        'is_win': isWin,
        'actual_win': actualWin,
      }),
    );
    return json.decode(response.body);
  }

  /// 申请积分兑换USDT
  static Future<Map<String, dynamic>> requestExchange({
    required String address,
    required double pointsAmount,
    required double usdtAmount,
    double exchangeRate = 1.0,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/exchange/request'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'address': address,
        'points_amount': pointsAmount,
        'usdt_amount': usdtAmount,
        'exchange_rate': exchangeRate,
      }),
    );
    return json.decode(response.body);
  }

  /// 检查是否有欠款
  static Future<Map<String, dynamic>> checkDebt(String address) async {
    final response = await http.post(
      Uri.parse('$baseUrl/debt/check'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'address': address}),
    );
    return json.decode(response.body);
  }

  /// 检查24小时兑换冷却时间
  static Future<Map<String, dynamic>> checkExchangeCooldown(String address) async {
    final response = await http.post(
      Uri.parse('$baseUrl/exchange/cooldown'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'address': address}),
    );
    return json.decode(response.body);
  }

  /// 积分兑换TRX（查询链上余额并1:1兑换）
  static Future<Map<String, dynamic>> exchangeToTrx({
    required String address,
    required double pointsAmount,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/exchange/to_trx'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'address': address,
        'points_amount': pointsAmount,
      }),
    );
    return json.decode(response.body);
  }

  /// 检查欠款支付状态
  static Future<Map<String, dynamic>> checkDebtPaymentStatus(int debtId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/debt/payment_status'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'debt_id': debtId}),
    );
    return json.decode(response.body);
  }

  /// 查询兑换历史
  static Future<Map<String, dynamic>> getExchangeHistory(String address) async {
    final response = await http.post(
      Uri.parse('$baseUrl/exchange/history'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'address': address}),
    );
    return json.decode(response.body);
  }
}
