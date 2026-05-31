import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../betting/betting_api_service.dart';
import '../services/wallet_storage.dart';

/// 赛事数据页面 - 显示可竞猜的比赛列表
/// 借鉴Github开源项目esports的实现
class MatchesPage extends StatefulWidget {
  const MatchesPage({super.key});

  @override
  State<MatchesPage> createState() => _MatchesPageState();
}

class _MatchesPageState extends State<MatchesPage> {
  bool _isLoading = true;
  List<Map<String, dynamic>> _liveMatches = []; // 进行中
  List<Map<String, dynamic>> _todayMatches = []; // 今日
  List<Map<String, dynamic>> _upcomingMatches = []; // 即将开始
  Set<String> _selectedGames = {'lol', 'dota2', 'csgo'}; // 选中的游戏

  @override
  void initState() {
    super.initState();
    _loadMatches();
  }

  Future<void> _loadMatches() async {
    setState(() => _isLoading = true);
    try {
      // 加载进行中的赛事
      final liveResult = await BettingApiService.getMatchesList(
        game: 'all',
        status: 'live',
        page: 1,
      );
      
      // 加载今日赛事
      final todayResult = await BettingApiService.getMatchesList(
        game: 'all',
        status: 'upcoming',
        page: 1,
      );
      
      if (liveResult['success'] && todayResult['success']) {
        setState(() {
          _liveMatches = List<Map<String, dynamic>>.from(liveResult['matches']);
          _todayMatches = List<Map<String, dynamic>>.from(todayResult['matches']);
          _upcomingMatches = _todayMatches; // 即将开始的赛事
        });
      }
    } catch (e) {
      print('加载赛事失败: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          // 筛选器
          _buildFilters(),
          // 赛事列表
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _matches.isEmpty
                    ? const Center(
                        child: Text('暂无赛事', style: TextStyle(color: Colors.white54)),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _matches.length,
                        itemBuilder: (context, index) {
                          return _buildMatchCard(_matches[index]);
                        },
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilters() {
    return Container(
      color: const Color(0xFF1A1A3E),
      padding: const EdgeInsets.all(16),
      child: Column(
        children: [
          // 游戏类型筛选
          Row(
            children: [
              const Text('游戏类型:', style: TextStyle(color: Colors.white70)),
              const SizedBox(width: 8),
              _buildGameChip('lol', 'LOL'),
              const SizedBox(width: 8),
              _buildGameChip('dota2', 'DOTA2'),
              const SizedBox(width: 8),
              _buildGameChip('csgo', 'CS2'),
            ],
          ),
          const SizedBox(height: 12),
          // 赛事状态筛选
          Row(
            children: [
              const Text('赛事状态:', style: TextStyle(color: Colors.white70)),
              const SizedBox(width: 8),
              _buildStatusChip('upcoming', '即将开始'),
              const SizedBox(width: 8),
              _buildStatusChip('live', '进行中'),
              const SizedBox(width: 8),
              _buildStatusChip('finished', '已结束'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildGameChip(String value, String label) {
    final isSelected = _selectedGame == value;
    return FilterChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (selected) {
        setState(() => _selectedGame = value);
        _loadMatches();
      },
      backgroundColor: const Color(0xFF2A2A4E),
      selectedColor: const Color(0xFF00FF88).withOpacity(0.3),
      labelStyle: TextStyle(
        color: isSelected ? const Color(0xFF00FF88) : Colors.white70,
      ),
    );
  }

  Widget _buildStatusChip(String value, String label) {
    final isSelected = _selectedStatus == value;
    return FilterChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (selected) {
        setState(() => _selectedStatus = value);
        _loadMatches();
      },
      backgroundColor: const Color(0xFF2A2A4E),
      selectedColor: const Color(0xFF00FF88).withOpacity(0.3),
      labelStyle: TextStyle(
        color: isSelected ? const Color(0xFF00FF88) : Colors.white70,
      ),
    );
  }

  Widget _buildMatchCard(Map<String, dynamic> match) {
    final team1 = match['team1'] ?? '未知';
    final team2 = match['team2'] ?? '未知';
    final odds1 = match['odds_team1'] != null ? double.parse(match['odds_team1'].toString()) : 0.0;
    final odds2 = match['odds_team2'] != null ? double.parse(match['odds_team2'].toString()) : 0.0;
    final startTime = match['start_time'] ?? '';
    final league = match['league_name'] ?? '';

    return Card(
      color: const Color(0xFF1A1A3E),
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // 联赛信息
            Row(
              children: [
                const Icon(Icons.sports_esports, color: Color(0xFF00FF88), size: 20),
                const SizedBox(width: 8),
                Text(
                  league,
                  style: const TextStyle(color: Colors.white70, fontSize: 14),
                ),
                const Spacer(),
                Text(
                  _formatTime(startTime),
                  style: const TextStyle(color: Colors.white54, fontSize: 12),
                ),
              ],
            ),
            const SizedBox(height: 12),
            // 对阵双方
            Row(
              children: [
                Expanded(
                  child: Text(
                    team1,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ),
                const Text(' VS ', style: TextStyle(color: Colors.white54, fontSize: 16)),
                Expanded(
                  child: Text(
                    team2,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            // 赔率
            Row(
              children: [
                Expanded(
                  child: _buildOddsButton(team1, odds1, match),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _buildOddsButton(team2, odds2, match),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOddsButton(String team, double odds, Map<String, dynamic> match) {
    return ElevatedButton(
      onPressed: odds > 0 ? () => _showBetDialog(team, odds, match) : null,
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF2A2A4E),
        padding: const EdgeInsets.symmetric(vertical: 12),
      ),
      child: Column(
        children: [
          Text(
            '赔率 ${odds.toStringAsFixed(2)}',
            style: const TextStyle(color: Color(0xFF00FF88), fontSize: 16),
          ),
          const SizedBox(height: 4),
          Text(
            team,
            style: const TextStyle(color: Colors.white70, fontSize: 12),
          ),
        ],
      ),
    );
  }

  void _showBetDialog(String team, double odds, Map<String, dynamic> match) {
    final TextEditingController betAmountController = TextEditingController();
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A3E),
        title: Text('下注竞猜', style: TextStyle(color: Colors.white)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              '${match['team1']} vs ${match['team2']}',
              style: TextStyle(color: Colors.white70),
            ),
            const SizedBox(height: 8),
            Text(
              '你选择: $team (赔率: ${odds.toStringAsFixed(2)})',
              style: TextStyle(color: const Color(0xFF00FF88)),
            ),
            const SizedBox(height: 16),
            TextField(
              controller: betAmountController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                labelText: '下注积分',
                labelStyle: TextStyle(color: Colors.white54),
                enabledBorder: OutlineInputBorder(borderSide: BorderSide(color: Color(0xFF00FF88))),
              ),
              style: const TextStyle(color: Colors.white),
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
              final amount = double.tryParse(betAmountController.text);
              if (amount == null || amount <= 0) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('请输入有效的下注金额')),
                );
                return;
              }
              
              Navigator.pop(context);
              await _placeBet(match, team, amount, odds);
            },
            style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF00FF88)),
            child: const Text('确认下注'),
          ),
        ],
      ),
    );
  }

  Future<void> _placeBet(Map<String, dynamic> match, String team, double amount, double odds) async {
    try {
      final address = await WalletStorage.getCurrentAddress();
      if (address == null || address.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('请先创建或导入钱包')),
        );
        return;
      }

      final result = await BettingApiService.placeBet(
        address: address,
        matchId: match['id'],
        matchName: '${match['team1']} vs ${match['team2']}',
        teamBet: team,
        betAmount: amount,
        odds: odds,
      );

      if (result['success']) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message'] ?? '下注成功')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(result['message'] ?? '下注失败')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('下注异常: $e')),
      );
    }
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
