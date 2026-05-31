import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../betting/betting_api_service.dart';
import '../services/wallet_storage.dart';

/// 积分页面 - 显示积分余额和USDT转换
class PointsPage extends StatefulWidget {
  const PointsPage({super.key});

  @override
  State<PointsPage> createState() => _PointsPageState();
}

class _PointsPageState extends State<PointsPage> {
  bool _isLoading = true;
  double _points = 0.0;
  double _totalEarned = 0.0;
  double _totalSpent = 0.0;

  @override
  void initState() {
    super.initState();
    _loadPointsBalance();
  }

  Future<void> _loadPointsBalance() async {
    setState(() => _isLoading = true);
    try {
      final address = await WalletStorage.getCurrentAddress();
      if (address == null || address.isEmpty) {
        setState(() => _isLoading = false);
        return;
      }

      final result = await BettingApiService.getPointsBalance(address);
      if (result['success']) {
        setState(() {
          _points = double.parse(result['points'].toString());
          _totalEarned = double.parse(result['total_earned'].toString());
          _totalSpent = double.parse(result['total_spent'].toString());
        });
      }
    } catch (e) {
      print('加载积分余额失败: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showConvertDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A3E),
        title: const Text('TRX兑换积分', style: TextStyle(color: Colors.white)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              '查询钱包TRX余额，按1:1兑换成积分',
              style: TextStyle(color: Color(0xFF00FF88), fontSize: 14),
            ),
            const SizedBox(height: 16),
            const Text(
              '24小时内只能兑换一次',
              style: TextStyle(color: Colors.white54, fontSize: 12),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消', style: TextStyle(color: Colors.white54)),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              await _convertFromTrx();
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00FF88)),
            child: const Text('确认兑换'),
          ),
        ],
      ),
    );
  }

  Future<void> _convertFromTrx() async {
    try {
      final address = await WalletStorage.getCurrentAddress();
      if (address == null || address.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('请先创建或导入钱包')),
        );
        return;
      }

      // 步骤1: 检查欠款
      final debtCheck = await BettingApiService.checkDebt(address);
      if (debtCheck['success'] && debtCheck['has_debt']) {
        _showDebtPaymentDialog(debtCheck['debt']);
        return;
      }

      // 步骤2: 检查24小时冷却
      final cooldownCheck = await BettingApiService.checkExchangeCooldown(address);
      if (cooldownCheck['success'] && !cooldownCheck['can_exchange']) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('24小时内只能兑换一次，下次可兑换: ${cooldownCheck['next_time']}')),
        );
        return;
      }

      // 步骤3: 调用TRX兑换API
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('正在查询TRX余额...')),
      );

      final result = await BettingApiService.exchangeToTrx(
        address: address,
        pointsAmount: 0, // 0表示查询全部余额
      );

      if (result['success']) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('兑换成功！获得 ${result['trx_amount']} 积分')),
        );
        _loadPointsBalance();
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message'] ?? '兑换失败')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('兑换异常: $e')),
      );
    }
  }

  void _showDebtPaymentDialog(Map<String, dynamic> debt) {
    final payAmount = debt['pay_amount'];
    final receiveAddress = debt['receive_address'];
    final debtId = debt['id'];

    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A3E),
        title: Row(
          children: [
            const Icon(Icons.warning, color: Colors.orange, size: 28),
            const SizedBox(width: 8),
            const Text('有待支付订单', style: TextStyle(color: Colors.white)),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              '您有未付清的竞猜欠款，请先完成支付',
              style: TextStyle(color: Colors.white70),
            ),
            const SizedBox(height: 16),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFF2A2A4E),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    '应付: $payAmount TRX',
                    style: const TextStyle(
                      color: Color(0xFF00FF88),
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text('收款地址:', style: TextStyle(color: Colors.white54, fontSize: 12)),
                  SelectableText(
                    receiveAddress,
                    style: const TextStyle(color: Colors.white, fontSize: 11),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('关闭', style: TextStyle(color: Colors.white54)),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  // 积分余额卡片
                  Card(
                    color: const Color(0xFF1A1A3E),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    elevation: 3,
                    child: Padding(
                      padding: const EdgeInsets.all(24),
                      child: Column(
                        children: [
                          const Text(
                            '我的积分',
                            style: TextStyle(color: Colors.white54, fontSize: 16),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _points.toStringAsFixed(2),
                            style: GoogleFonts.convergence(
                              fontSize: 48,
                              color: const Color(0xFF00FF88),
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 24),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                            children: [
                              _buildStatCard('累计获得', _totalEarned, Colors.green),
                              _buildStatCard('累计花费', _totalSpent, Colors.orange),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  // 转换按钮
                  ElevatedButton.icon(
                    onPressed: _showConvertDialog,
                    icon: const Icon(Icons.account_balance_wallet),
                    label: const Text('TRX兑换积分'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF00FF88),
                      padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                  ),
                  const SizedBox(height: 16),
                  const Text(
                    '提示：查询TRX余额并按1:1兑换成积分',
                    style: TextStyle(color: Colors.white54, fontSize: 12),
                  ),
                ],
              ),
            ),
    );
  }

  Widget _buildStatCard(String label, double value, Color color) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0xFF2A2A4E),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Text(
            label,
            style: const TextStyle(color: Colors.white54, fontSize: 12),
          ),
          const SizedBox(height: 8),
          Text(
            value.toStringAsFixed(2),
            style: TextStyle(
              color: color,
              fontSize: 24,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
