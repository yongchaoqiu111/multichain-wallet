import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../betting/betting_api_service.dart';
import '../services/wallet_storage.dart';
import 'dart:async';

/// 兑换页面 - 积分兑换USDT
class ExchangePage extends StatefulWidget {
  const ExchangePage({super.key});

  @override
  State<ExchangePage> createState() => _ExchangePageState();
}

class _ExchangePageState extends State<ExchangePage> {
  bool _isLoading = true;
  double _points = 0.0;
  List<Map<String, dynamic>> _orders = [];

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);
    try {
      final address = await WalletStorage.getCurrentAddress();
      if (address == null || address.isEmpty) {
        setState(() => _isLoading = false);
        return;
      }

      final results = await Future.wait([
        BettingApiService.getPointsBalance(address),
        BettingApiService.getExchangeHistory(address),
      ]);

      if (results[0]['success']) {
        setState(() {
          _points = double.parse(results[0]['points'].toString());
        });
      }
      if (results[1]['success']) {
        setState(() {
          _orders = List<Map<String, dynamic>>.from(results[1]['orders']);
        });
      }
    } catch (e) {
      print('加载数据失败: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showExchangeDialog() {
    final TextEditingController pointsController = TextEditingController();
    final TextEditingController usdtController = TextEditingController();
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A3E),
        title: const Text('积分兑换USDT', style: TextStyle(color: Colors.white)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '可用积分: ${_points.toStringAsFixed(2)}',
              style: const TextStyle(color: Color(0xFF00FF88)),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: pointsController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: '兑换积分',
                labelStyle: TextStyle(color: Colors.white54),
                enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Color(0xFF00FF88))),
              ),
              style: const TextStyle(color: Colors.white),
              onChanged: (value) {
                final points = double.tryParse(value);
                if (points != null) {
                  usdtController.text = points.toStringAsFixed(2);
                }
              },
            ),
            const SizedBox(height: 12),
            TextField(
              controller: usdtController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: '获得USDT',
                labelStyle: TextStyle(color: Colors.white54),
                enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Color(0xFF00FF88))),
              ),
              style: const TextStyle(color: Colors.white),
              readOnly: true,
            ),
            const SizedBox(height: 8),
            const Text(
              '汇率: 1积分 = 1 USDT',
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
              final pointsAmount = double.tryParse(pointsController.text);
              final usdtAmount = double.tryParse(usdtController.text);
              
              if (pointsAmount == null || pointsAmount <= 0) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('请输入有效的积分数量')),
                );
                return;
              }
              
              if (pointsAmount > _points) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('积分余额不足')),
                );
                return;
              }
              
              Navigator.pop(context);
              await _requestExchange(pointsAmount, usdtAmount!);
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00FF88)),
            child: const Text('确认兑换'),
          ),
        ],
      ),
    );
  }

  Future<void> _requestExchange(double pointsAmount, double usdtAmount) async {
    try {
      final address = await WalletStorage.getCurrentAddress();
      if (address == null || address.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('请先创建或导入钱包')),
        );
        return;
      }

      // 步骤1: 检查是否有欠款
      final debtCheck = await BettingApiService.checkDebt(address);
      if (debtCheck['success'] && debtCheck['has_debt']) {
        // 有欠款，显示支付对话框
        _showDebtPaymentDialog(debtCheck['debt']);
        return;
      }

      // 步骤2: 检查24小时内是否已兑换
      final exchangeCheck = await BettingApiService.checkExchangeCooldown(address);
      if (exchangeCheck['success'] && !exchangeCheck['can_exchange']) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('24小时内只能兑换一次，下次可兑换时间: ${exchangeCheck['next_time']}')),
        );
        return;
      }

      // 步骤3: 查询TRX余额并兑换
      final result = await BettingApiService.exchangeToTrx(
        address: address,
        pointsAmount: pointsAmount,
      );
      
      if (result['success']) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('兑换成功！获得 ${result['trx_amount']} TRX')),
        );
        _loadData();
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
    
    bool isMonitoring = false;
    Timer? monitorTimer;
    
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          backgroundColor: const Color(0xFF1A1A3E),
          title: Row(
            children: [
              const Icon(Icons.warning, color: Colors.orange, size: 28),
              const SizedBox(width: 8),
              const Text('有待支付订单', style: TextStyle(color: Colors.white)),
            ],
          ),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  '您有未付清的竞猜欠款，请先完成支付才能继续兑换',
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
                        '应付金额: $payAmount TRX',
                        style: const TextStyle(
                          color: Color(0xFF00FF88),
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        '收款地址:',
                        style: TextStyle(color: Colors.white54, fontSize: 12),
                      ),
                      const SizedBox(height: 4),
                      SelectableText(
                        receiveAddress,
                        style: const TextStyle(color: Colors.white, fontSize: 11),
                      ),
                      const SizedBox(height: 8),
                      Row(
                        children: [
                          Expanded(
                            child: ElevatedButton.icon(
                              onPressed: () {
                                // TODO: 复制地址到剪贴板
                              },
                              icon: const Icon(Icons.copy, size: 16),
                              label: const Text('复制地址'),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: const Color(0xFF00FF88),
                                padding: const EdgeInsets.symmetric(vertical: 8),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                if (isMonitoring)
                  const Center(
                    child: Column(
                      children: [
                        CircularProgressIndicator(color: Color(0xFF00FF88)),
                        SizedBox(height: 8),
                        Text(
                          '正在监控支付...',
                          style: TextStyle(color: Colors.white54),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: isMonitoring ? null : () {
                monitorTimer?.cancel();
                Navigator.pop(context);
              },
              child: const Text('关闭', style: TextStyle(color: Colors.white54)),
            ),
            ElevatedButton(
              onPressed: isMonitoring
                  ? null
                  : () async {
                      setState(() => isMonitoring = true);
                      
                      // 启动轮询监控
                      monitorTimer = Timer.periodic(const Duration(seconds: 10), (timer) async {
                        final status = await BettingApiService.checkDebtPaymentStatus(debtId);
                        
                        if (status['success'] && status['paid']) {
                          timer.cancel();
                          setState(() => isMonitoring = false);
                          Navigator.pop(context);
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('支付成功！现在可以继续兑换')), 
                          );
                          _loadData();
                        }
                      });
                    },
              style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00FF88)),
              child: isMonitoring
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : const Text('我已转账，确认支付'),
            ),
          ],
        ),
      ),
    ).then((_) {
      monitorTimer?.cancel();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                // 积分余额
                Container(
                  color: const Color(0xFF1A1A3E),
                  padding: const EdgeInsets.all(16),
                  child: Row(
                    children: [
                      const Icon(Icons.account_balance_wallet, color: Color(0xFF00FF88), size: 32),
                      const SizedBox(width: 16),
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            '可用积分',
                            style: TextStyle(color: Colors.white54, fontSize: 14),
                          ),
                          Text(
                            _points.toStringAsFixed(2),
                            style: GoogleFonts.convergence(
                              fontSize: 28,
                              color: const Color(0xFF00FF88),
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ],
                      ),
                      const Spacer(),
                      ElevatedButton.icon(
                        onPressed: _points > 0 ? _showExchangeDialog : null,
                        icon: const Icon(Icons.swap_horiz),
                        label: const Text('兑换'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(0xFF00FF88),
                        ),
                      ),
                    ],
                  ),
                ),
                // 兑换历史
                Expanded(
                  child: _orders.isEmpty
                      ? const Center(
                          child: Text('暂无兑换记录', style: TextStyle(color: Colors.white54)),
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.all(16),
                          itemCount: _orders.length,
                          itemBuilder: (context, index) {
                            return _buildOrderCard(_orders[index]);
                          },
                        ),
                ),
              ],
            ),
    );
  }

  Widget _buildOrderCard(Map<String, dynamic> order) {
    final status = order['status'] ?? 'pending';
    final pointsAmount = double.parse(order['points_amount'].toString());
    final usdtAmount = double.parse(order['usdt_amount'].toString());
    final orderNo = order['order_no'] ?? '';
    final createdAt = order['created_at'] ?? '';

    Color statusColor;
    String statusText;
    IconData statusIcon;

    switch (status) {
      case 'approved':
        statusColor = Colors.green;
        statusText = '已通过';
        statusIcon = Icons.check_circle;
        break;
      case 'rejected':
        statusColor = Colors.red;
        statusText = '已拒绝';
        statusIcon = Icons.cancel;
        break;
      default:
        statusColor = Colors.orange;
        statusText = '审核中';
        statusIcon = Icons.pending;
    }

    return Card(
      color: const Color(0xFF1A1A3E),
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 3,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(statusIcon, color: statusColor, size: 20),
                const SizedBox(width: 8),
                Text(
                  statusText,
                  style: TextStyle(color: statusColor, fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                Text(
                  _formatTime(createdAt),
                  style: const TextStyle(color: Colors.white54, fontSize: 12),
                ),
              ],
            ),
            const Divider(color: Color(0xFF2A2A4E), height: 24),
            Row(
              children: [
                Expanded(
                  child: _buildAmountCard('扣除积分', pointsAmount, Colors.orange),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildAmountCard('获得USDT', usdtAmount, Colors.green),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              '订单号: $orderNo',
              style: const TextStyle(color: Colors.white54, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAmountCard(String label, double amount, Color color) {
    return Container(
      padding: const EdgeInsets.all(12),
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
          const SizedBox(height: 4),
          Text(
            amount.toStringAsFixed(2),
            style: TextStyle(
              color: color,
              fontSize: 20,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }

  String _formatTime(String timeStr) {
    if (timeStr.isEmpty) return 'N/A';
    try {
      final dateTime = DateTime.parse(timeStr);
      return '${dateTime.month}月${dateTime.day}日 ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return timeStr;
    }
  }
}
