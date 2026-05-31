import 'package:flutter/material.dart';
import 'matches_page_v2.dart';
import 'my_bets_page.dart';
import 'points_page.dart';
import 'exchange_page.dart';

/// 竞猜系统主Tab - 包含赛事、我的竞猜、积分、兑换4个子页面
class BettingTabPage extends StatefulWidget {
  const BettingTabPage({super.key});

  @override
  State<BettingTabPage> createState() => _BettingTabPageState();
}

class _BettingTabPageState extends State<BettingTabPage>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('电竞竞猜'),
        bottom: TabBar(
          controller: _tabController,
          labelColor: const Color(0xFF00FF88),
          unselectedLabelColor: Colors.white54,
          indicatorColor: const Color(0xFF00FF88),
          tabs: const [
            Tab(icon: Icon(Icons.sports), text: '赛事'),
            Tab(icon: Icon(Icons.emoji_events), text: '我的'),
            Tab(icon: Icon(Icons.account_balance_wallet), text: '积分'),
            Tab(icon: Icon(Icons.swap_horiz), text: '兑换'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabController,
        children: const [
          MatchesPage(), // 赛事数据
          MyBetsPage(), // 我的竞猜
          PointsPage(), // 积分管理
          ExchangePage(), // 积分兑换
        ],
      ),
    );
  }
}
