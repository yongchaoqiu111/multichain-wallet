import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../betting/betting_api_service.dart';
import '../services/wallet_storage.dart';

/// 我的竞猜页面 - 显示用户的竞猜记录
class MyBetsPage extends StatefulWidget {
  const MyBetsPage({super.key});

  @override
  State<MyBetsPage> createState() => _MyBetsPageState();
}

class _MyBetsPageState extends State<MyBetsPage> {
  bool _isLoading = true;
  List<Map<String, dynamic>> _bets = [];
  String _filterStatus = 'all';

  @override
  void initState() {
    super.initState();
    _loadMyBets();
  }

  Future<void> _loadMyBets() async {
    setState(() => _isLoading = true);
    try {
      final address = await WalletStorage.getCurrentAddress();
      if (address == null || address.isEmpty) {
        setState(() => _isLoading = false);
        return;
      }

      final result = await BettingApiService.getMyBets(
        address: address,
        status: _filterStatus,
      );
      if (result['success']) {
        setState(() {
          _bets = List<Map<String, dynamic>>.from(result['records']);
        });
      }
    } catch (e) {
      print('加载竞猜记录失败: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          Container(
            color: const Color(0xFF1A1A3E),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                _buildFilterChip('all', '全部'),
                const SizedBox(width: 8),
                _buildFilterChip('pending', '待结算'),
                const SizedBox(width: 8),
                _buildFilterChip('won', '已中奖'),
                const SizedBox(width: 8),
                _buildFilterChip('lost', '未中奖'),
              ],
            ),
          ),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _bets.isEmpty
                    ? const Center(
                        child: Text('暂无竞猜记录', style: TextStyle(color: Colors.white54)),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _bets.length,
                        itemBuilder: (context, index) {
                          return _buildBetCard(_bets[index]);
                        },
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String value, String label) {
    final isSelected = _filterStatus == value;
    return FilterChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (selected) {
        setState(() => _filterStatus = value);
        _loadMyBets();
      },
      backgroundColor: const Color(0xFF2A2A4E),
      selectedColor: const Color(0xFF00FF88).withOpacity(0.3),
      labelStyle: TextStyle(
        color: isSelected ? const Color(0xFF00FF88) : Colors.white70,
      ),
    );
  }

  Widget _buildBetCard(Map<String, dynamic> bet) {
    final status = bet['status'] ?? 'pending';
    final matchName = bet['match_name'] ?? '未知赛事';
    final teamBet = bet['team_bet'] ?? '未知';
    final betAmount = double.parse(bet['bet_amount'].toString());
    final odds = bet['odds'] != null ? double.parse(bet['odds'].toString()) : 0.0;
    final potentialWin = bet['potential_win'] != null ? double.parse(bet['potential_win'].toString()) : 0.0;
    final actualWin = bet['actual_win'] != null ? double.parse(bet['actual_win'].toString()) : 0.0;
    final createdAt = bet['created_at'] ?? '';

    Color statusColor;
    String statusText;
    IconData statusIcon;

    switch (status) {
      case 'won':
        statusColor = Colors.green;
        statusText = '已中奖';
        statusIcon = Icons.emoji_events;
        break;
      case 'lost':
        statusColor = Colors.red;
        statusText = '未中奖';
        statusIcon = Icons.cancel;
        break;
      default:
        statusColor = Colors.orange;
        statusText = '待结算';
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
            // 头部：状态和时间
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
            // 赛事信息
            Text(
              matchName,
              style: GoogleFonts.convergence(
                fontSize: 18,
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                const Text('我押:', style: TextStyle(color: Colors.white54)),
                const SizedBox(width: 8),
                Text(
                  teamBet,
                  style: const TextStyle(color: Color(0xFF00FF88), fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                Text(
                  '赔率: ${odds.toStringAsFixed(2)}',
                  style: const TextStyle(color: Colors.white70),
                ),
              ],
            ),
            const SizedBox(height: 12),
            // 金额信息
            Row(
              children: [
                Expanded(
                  child: _buildAmountCard('下注金额', betAmount, Colors.orange),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildAmountCard(
                    status == 'won' ? '赢得积分' : '预计赢得',
                    status == 'won' ? actualWin : potentialWin,
                    status == 'won' ? Colors.green : Colors.blue,
                  ),
                ),
              ],
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
