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
  List<Map<String, dynamic>> _liveMatches = [];
  List<Map<String, dynamic>> _upcomingMatches = [];
  Set<String> _selectedGames = {'lol', 'dota2', 'csgo'};

  @override
  void initState() {
    super.initState();
    _loadMatches();
  }

  Future<void> _loadMatches() async {
    setState(() => _isLoading = true);
    try {
      // 只调用一次获取所有即将开始的赛事
      final result = await BettingApiService.getMatchesList(game: 'all', page: 1);

      if (result['success']) {
        setState(() {
          _liveMatches = []; // 目前没有live赛事
          _upcomingMatches = List<Map<String, dynamic>>.from(result['matches']);
        });
      }
    } catch (e) {
      print('加载赛事失败: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  List<Map<String, dynamic>> _filterMatches(List<Map<String, dynamic>> matches) {
    return matches.where((m) => _selectedGames.contains(m['game'])).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : CustomScrollView(
              slivers: [
                // 游戏筛选器
                SliverToBoxAdapter(child: _buildGameFilter()),
                // LIVE赛事 - 横向滚动
                if (_filterMatches(_liveMatches).isNotEmpty)
                  _buildLiveSection(),
                // 今日赛事 - 垂直列表
                _buildUpcomingSection(),
              ],
            ),
    );
  }

  Widget _buildGameFilter() {
    return Container(
      color: const Color(0xFF1A1A3E),
      padding: const EdgeInsets.all(12),
      child: Wrap(
        spacing: 8,
        runSpacing: 8,
        children: [
          _buildGameChip('lol', '英雄联盟'),
          _buildGameChip('dota2', 'DOTA2'),
          _buildGameChip('csgo', 'CS2'),
        ],
      ),
    );
  }

  Widget _buildGameChip(String game, String label) {
    final isSelected = _selectedGames.contains(game);
    return FilterChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (selected) {
        setState(() {
          if (selected) {
            _selectedGames.add(game);
          } else {
            _selectedGames.remove(game);
          }
        });
      },
      backgroundColor: const Color(0xFF2A2A4E),
      selectedColor: const Color(0xFF00FF88).withOpacity(0.3),
      labelStyle: TextStyle(
        color: isSelected ? const Color(0xFF00FF88) : Colors.white70,
      ),
    );
  }

  Widget _buildLiveSection() {
    final liveMatches = _filterMatches(_liveMatches);
    return SliverToBoxAdapter(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                Text(
                  '🔴 进行中',
                  style: GoogleFonts.convergence(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const Spacer(),
                IconButton(
                  icon: const Icon(Icons.refresh, color: Colors.grey),
                  onPressed: _loadMatches,
                ),
              ],
            ),
          ),
          SizedBox(
            height: 200,
            child: ListView.builder(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: liveMatches.length,
              itemBuilder: (context, index) {
                return _buildLiveMatchCard(liveMatches[index]);
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLiveMatchCard(Map<String, dynamic> match) {
    final team1 = match['team1'] ?? '?';
    final team2 = match['team2'] ?? '?';
    final league = match['league_name'] ?? '';

    return Container(
      width: 180,
      margin: const EdgeInsets.only(right: 8, bottom: 8),
      child: Card(
        color: const Color(0xFF1A1A3E),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        elevation: 3,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(match['game']?.toUpperCase() ?? '', 
                style: const TextStyle(color: Color(0xFF00FF88), fontSize: 14)),
              const SizedBox(height: 4),
              Text(league, style: const TextStyle(color: Colors.white54, fontSize: 12)),
              const SizedBox(height: 8),
              Text(team1, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
              const Text('VS', style: TextStyle(color: Colors.white54, fontSize: 12)),
              Text(team2, style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold)),
              const SizedBox(height: 8),
              ElevatedButton(
                onPressed: () => _showBetDialog(match),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF00FF88),
                ),
                child: const Text('下注'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildUpcomingSection() {
    final upcomingMatches = _filterMatches(_upcomingMatches);
    return SliverList(
      delegate: SliverChildBuilderDelegate(
        (context, index) {
          if (index == 0) {
            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Text(
                '📅 即将开始',
                style: GoogleFonts.convergence(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Colors.white,
                ),
              ),
            );
          }
          return _buildUpcomingMatchCard(upcomingMatches[index - 1]);
        },
        childCount: upcomingMatches.isEmpty ? 1 : upcomingMatches.length + 1,
      ),
    );
  }

  Widget _buildUpcomingMatchCard(Map<String, dynamic> match) {
    final team1 = match['team1'] ?? '?';
    final team2 = match['team2'] ?? '?';
    final odds1 = match['odds_team1'] != null ? double.parse(match['odds_team1'].toString()) : 0.0;
    final odds2 = match['odds_team2'] != null ? double.parse(match['odds_team2'].toString()) : 0.0;
    final startTime = match['start_time'] ?? '';
    final league = match['league_name'] ?? '';

    return Card(
      color: const Color(0xFF1A1A3E),
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      elevation: 3,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Text(match['game']?.toUpperCase() ?? '', 
                  style: const TextStyle(color: Color(0xFF00FF88), fontSize: 14)),
                const SizedBox(width: 8),
                Text(league, style: const TextStyle(color: Colors.white54, fontSize: 12)),
                const Spacer(),
                Text(_formatTime(startTime), style: const TextStyle(color: Colors.white54)),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: Text(team1, textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                ),
                const Text(' VS ', style: TextStyle(color: Colors.white54)),
                Expanded(
                  child: Text(team2, textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(child: _buildOddsButton(team1, odds1, match)),
                const SizedBox(width: 12),
                Expanded(child: _buildOddsButton(team2, odds2, match)),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOddsButton(String team, double odds, Map<String, dynamic> match) {
    return ElevatedButton(
      onPressed: odds > 0 ? () => _showBetDialog(match, teamBet: team, odds: odds) : null,
      style: ElevatedButton.styleFrom(
        backgroundColor: const Color(0xFF2A2A4E),
        padding: const EdgeInsets.symmetric(vertical: 12),
      ),
      child: Column(
        children: [
          Text('赔率 ${odds.toStringAsFixed(2)}', 
            style: const TextStyle(color: Color(0xFF00FF88), fontSize: 16)),
          const SizedBox(height: 4),
          Text(team, style: const TextStyle(color: Colors.white70, fontSize: 12)),
        ],
      ),
    );
  }

  void _showBetDialog(Map<String, dynamic> match, {String? teamBet, double? odds}) {
    final TextEditingController betAmountController = TextEditingController();
    final team = teamBet ?? match['team1'];
    final selectedOdds = odds ?? (match['odds_team1'] != null ? double.parse(match['odds_team1'].toString()) : 2.0);
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFF1A1A3E),
        title: const Text('下注竞猜', style: TextStyle(color: Colors.white)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('${match['team1']} vs ${match['team2']}', 
              style: const TextStyle(color: Colors.white70)),
            const SizedBox(height: 8),
            Text('你选择: $team (赔率: ${selectedOdds.toStringAsFixed(2)})', 
              style: const TextStyle(color: Color(0xFF00FF88))),
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
              await _placeBet(match, team, amount, selectedOdds);
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