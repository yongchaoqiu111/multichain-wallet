import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'services/wallet_api_service.dart';
import 'services/wallet_backup_service.dart';
import 'services/wallet_storage.dart';
import 'betting/betting_api_service.dart';
import 'betting/betting_tab.dart';

void main() {
  runApp(const WalletApp());
}

class WalletApp extends StatelessWidget {
  const WalletApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '多链钱包',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0D0D2B),
        primaryColor: const Color(0xFF00FF88),
        appBarTheme: const AppBarTheme(
          backgroundColor: Color(0xFF1A1A3E),
        ),
        bottomNavigationBarTheme: const BottomNavigationBarThemeData(
          backgroundColor: Color(0xFF1A1A3E),
          selectedItemColor: Color(0xFF00FF88),
          unselectedItemColor: Colors.white54,
        ),
      ),
      home: const MainScreen(),
    );
  }
}

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 0;
  String _currentNetwork = 'TRON';
  String? _sessionId;
  String _currentAddress = '未加载钱包';
  String? _currentPrivateKey;
  String? _currentMnemonic;

  void _onSessionChanged(String? sessionId, String address, String? privateKey, String? mnemonic) {
    setState(() {
      _sessionId = sessionId;
      _currentAddress = address;
      _currentPrivateKey = privateKey;
      _currentMnemonic = mnemonic;
    });
  }

  void _onNetworkChanged(String network) {
    setState(() {
      _currentNetwork = network;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('多链钱包'),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFF2A2A4E),
                borderRadius: BorderRadius.circular(15),
              ),
              child: DropdownButton<String>(
                value: _currentNetwork,
                underline: const SizedBox(),
                dropdownColor: const Color(0xFF1A1A3E),
                items: ['TRON', 'BSC', 'ETH'].map((String network) {
                  return DropdownMenuItem<String>(
                    value: network,
                    child: Text(network, style: const TextStyle(color: Colors.white)),
                  );
                }).toList(),
                onChanged: (String? newValue) {
                  if (newValue != null) {
                    _onNetworkChanged(newValue);
                  }
                },
              ),
            ),
          ),
        ],
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: [
          WalletManagementPage(
            network: _currentNetwork,
            onSessionChanged: _onSessionChanged,
          ),
          AssetQueryPage(
            network: _currentNetwork,
            address: _currentAddress,
          ),
          TransferPage(
            network: _currentNetwork,
            sessionId: _sessionId,
            privateKey: _currentPrivateKey,
            mnemonic: _currentMnemonic,
          ),
          const TransactionHistoryPage(),
          const BettingTabPage(), // 竞猜Tab
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.account_balance_wallet),
            label: '钱包',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.query_stats),
            label: '资产',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.send),
            label: '转账',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.history),
            label: '记录',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.sports_esports),
            label: '竞猜',
          ),
        ],
      ),
    );
  }
}

class WalletManagementPage extends StatefulWidget {
  final String network;
  final Function(String?, String, String?, String?) onSessionChanged;

  const WalletManagementPage({
    super.key,
    required this.network,
    required this.onSessionChanged,
  });

  @override
  State<WalletManagementPage> createState() => _WalletManagementPageState();
}

class _WalletManagementPageState extends State<WalletManagementPage> {
  String _address = '未加载钱包';
  String? _mnemonic;
  String? _privateKey;
  String? _sessionId;
  bool _isLoading = false;
  bool _isBackingUp = false;
  List<Map<String, dynamic>> _localWallets = [];

  @override
  void initState() {
    super.initState();
    _loadLocalWallets();
  }

  @override
  void didUpdateWidget(WalletManagementPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    // 当网络切换时，如果有助记词则从本地加载对应网络的地址
    if (oldWidget.network != widget.network && (_mnemonic?.isNotEmpty ?? false)) {
      _loadWalletForNewNetwork();
    }
  }

  Future<void> _loadWalletForNewNetwork() async {
    // 从本地存储查找当前网络的钱包
    final all = await WalletStorage.loadWallets();
    
    // BSC和ETH共用同一个地址（都是EVM链）
    String searchChain = widget.network;
    if (widget.network == 'ETH') searchChain = 'BSC';
    
    final wallet = all.firstWhere(
      (w) => w['chain'] == searchChain && w['mnemonic'] == _mnemonic,
      orElse: () => <String, dynamic>{},
    );

    if (wallet.isNotEmpty) {
      // 找到对应网络的钱包，直接加载
      final address = wallet['address']?.toString() ?? '';
      final sessionId = wallet['session_id']?.toString();
      final privateKey = wallet['private_key']?.toString() ?? '';
      
      setState(() {
        _address = address;
        _sessionId = sessionId;
        _privateKey = privateKey;
      });
      widget.onSessionChanged(sessionId, address, privateKey, _mnemonic);
      await WalletStorage.setActiveWallet(address, widget.network);
      
      // 如果session_id为空或失效，尝试刷新
      if (sessionId == null || sessionId.isEmpty) {
        try {
          final newSid = await WalletApiService.refreshSession(
            chain: widget.network,
            privateKey: privateKey,
            mnemonic: _mnemonic,
          );
          setState(() => _sessionId = newSid);
          widget.onSessionChanged(newSid, address, privateKey, _mnemonic);
          await WalletStorage.saveWallet({...wallet, 'session_id': newSid});
        } catch (e) {
          _showErrorSnackBar('会话刷新失败: $e');
        }
      }
    } else {
      // 没有找到对应网络的钱包，需要创建
      _createWalletForNetwork();
    }
  }

  Future<void> _createWalletForNetwork() async {
    if (_mnemonic == null || _mnemonic!.isEmpty) return;
    
    setState(() => _isLoading = true);
    try {
      final result = await WalletApiService.importMnemonic(_mnemonic!, widget.network);
      if (result['success'] == true) {
        await _finalizeWallet(result);
      }
    } catch (e) {
      _showErrorSnackBar('创建钱包失败: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _loadLocalWallets() async {
    final all = await WalletStorage.loadWallets();
    final filtered =
        all.where((w) => w['chain'] == widget.network).toList();
    if (mounted) setState(() => _localWallets = filtered);
  }

  /// 保存本地 + 云端备份（与桌面 _save_and_backup_wallet / backup_to_server 一致）
  Future<void> _finalizeWallet(Map<String, dynamic> apiResult) async {
    final address = apiResult['address']?.toString() ?? '';
    final sessionId = apiResult['session_id']?.toString();
    final privateKey = apiResult['private_key']?.toString() ?? '';
    final mnemonic = apiResult['mnemonic']?.toString() ?? '';

    // 保存当前网络的钱包
    await WalletStorage.saveWallet({
      'chain': widget.network,
      'address': address,
      'private_key': privateKey,
      'mnemonic': mnemonic,
      'session_id': sessionId,
    });
    await WalletStorage.setActiveWallet(address, widget.network);
    await _loadLocalWallets();

    setState(() {
      _address = address;
      _sessionId = sessionId;
      _privateKey = privateKey;
      _mnemonic = mnemonic.isNotEmpty ? mnemonic : _mnemonic;
    });
    widget.onSessionChanged(sessionId, address, privateKey, _mnemonic);

    // 如果有助记词，自动生成另一个网络的地址
    if (mnemonic.isNotEmpty) {
      await _generateOtherNetworkWallet(mnemonic, privateKey);
    }

    setState(() => _isBackingUp = true);
    final backup = await WalletBackupService.backupFromApiResult(
      apiResult: apiResult,
      chain: widget.network,
    );
    if (mounted) {
      setState(() => _isBackingUp = false);
      if (backup['success'] == true) {
        _showSuccessSnackBar(
          '钱包已备份到云端 ID: ${backup['backup_id'] ?? ''}',
        );
      } else {
        _showErrorSnackBar('云端备份失败: ${backup['message']}');
      }
    }
  }

  /// 生成另一个网络的钱包（BSC/ETH共用，TRON独立）
  Future<void> _generateOtherNetworkWallet(String mnemonic, String privateKey) async {
    try {
      String otherChain;
      
      // 如果当前是TRON，生成EVM链地址；如果当前是EVM链，生成TRON地址
      if (widget.network == 'TRON') {
        otherChain = 'BSC'; // BSC和ETH共用
      } else {
        otherChain = 'TRON';
      }
      
      // 检查是否已经存在另一个网络的钱包
      final all = await WalletStorage.loadWallets();
      final exists = all.any((w) => w['chain'] == otherChain && w['mnemonic'] == mnemonic);
      
      if (!exists) {
        // 调用后端API生成另一个网络的地址
        final result = await WalletApiService.importMnemonic(mnemonic, otherChain);
        if (result['success'] == true) {
          await WalletStorage.saveWallet({
            'chain': otherChain,
            'address': result['address'],
            'private_key': result['private_key'],
            'mnemonic': mnemonic,
            'session_id': result['session_id'],
          });
        }
      }
    } catch (e) {
      print('生成其他网络钱包失败: $e');
      // 不显示错误提示，避免干扰用户体验
    }
  }

  Future<void> _loadLocalWallet(Map<String, dynamic> w) async {
    final address = w['address']?.toString() ?? '';
    setState(() {
      _address = address;
      _sessionId = w['session_id']?.toString();
      _privateKey = w['private_key']?.toString();
      _mnemonic = w['mnemonic']?.toString();
    });
    widget.onSessionChanged(_sessionId, address, _privateKey, _mnemonic);
    await WalletStorage.setActiveWallet(address, widget.network);

    if (_sessionId == null && (_privateKey?.isNotEmpty ?? false)) {
      try {
        final sid = await WalletApiService.refreshSession(
          chain: widget.network,
          privateKey: _privateKey,
          mnemonic: _mnemonic,
        );
        setState(() => _sessionId = sid);
        widget.onSessionChanged(sid, address, _privateKey, _mnemonic);
        await WalletStorage.saveWallet({...w, 'session_id': sid});
        await _loadLocalWallets();
      } catch (e) {
        _showErrorSnackBar('恢复会话失败: $e');
      }
    }
    _showSuccessSnackBar('已切换钱包');
  }

  Future<void> _manualBackup() async {
    if (_privateKey == null || _privateKey!.isEmpty) {
      _showErrorSnackBar('请先创建或导入钱包');
      return;
    }
    setState(() => _isBackingUp = true);
    final backup = await WalletBackupService.backupWallet(
      address: _address,
      chain: widget.network,
      walletData: WalletBackupService.buildWalletPayload(
        privateKey: _privateKey!,
        mnemonic: _mnemonic ?? '',
        address: _address,
      ),
    );
    if (mounted) {
      setState(() => _isBackingUp = false);
      if (backup['success'] == true) {
        _showSuccessSnackBar('手动备份成功: ${backup['backup_id']}');
      } else {
        _showErrorSnackBar('备份失败: ${backup['message']}');
      }
    }
  }

  void _createWallet() async {
    setState(() => _isLoading = true);
    try {
      final result = await WalletApiService.createWallet(widget.network);
      
      if (result['success'] == true) {
        _mnemonic = result['mnemonic']?.toString();
        if (_mnemonic != null && _mnemonic!.isNotEmpty) {
          await _showMnemonicDialog(_mnemonic!);
        }
        await _finalizeWallet(result);
        _showSuccessSnackBar('钱包创建成功！');
      }
    } catch (e) {
      _showErrorSnackBar('创建失败: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _showMnemonicDialog(String mnemonic) async {
    final words = mnemonic.split(' ');
    await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('备份助记词'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('请安全保存以下${words.length}个助记词：'),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: words.asMap().entries.map((entry) {
                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text('${entry.key + 1}. ${entry.value}'),
                  );
                }).toList(),
              ),
              const SizedBox(height: 16),
              const Text('⚠️ 丢失助记词将永久无法恢复钱包！', style: TextStyle(color: Colors.orange)),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('我已备份'),
          ),
        ],
      ),
    );
  }

  void _importPrivateKey() async {
    final controller = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('私钥导入'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(hintText: '请输入私钥'),
          obscureText: true,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('取消')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('导入')),
        ],
      ),
    );

    if (confirmed != true || controller.text.isEmpty) return;

    setState(() => _isLoading = true);
    try {
      final result = await WalletApiService.importPrivateKey(controller.text, widget.network);
      if (result['success'] == true) {
        await _finalizeWallet(result);
        _showSuccessSnackBar('导入成功！');
      }
    } catch (e) {
      _showErrorSnackBar('导入失败: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _importMnemonic() async {
    final controller = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('助记词导入'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(hintText: '助记词，用空格分隔'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('取消')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('导入')),
        ],
      ),
    );

    if (confirmed != true || controller.text.isEmpty) return;

    setState(() => _isLoading = true);
    try {
      final result = await WalletApiService.importMnemonic(controller.text, widget.network);
      if (result['success'] == true) {
        await _finalizeWallet(result);
        _showSuccessSnackBar('导入成功！');
      }
    } catch (e) {
      _showErrorSnackBar('导入失败: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showSuccessSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.green),
    );
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red),
    );
  }

  // 获取链颜色
  Color _getChainColor(String chain) {
    switch (chain) {
      case 'TRON':
        return Colors.red;
      case 'BSC':
        return Colors.yellow.shade700;
      case 'ETH':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  // 显示二维码
  void _showQRCode(String address) {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: const Color(0xFF1A1A3E),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text(
                '收款地址',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: QrImageView(
                  data: address,
                  version: QrVersions.auto,
                  size: 200.0,
                ),
              ),
              const SizedBox(height: 16),
              Text(
                address,
                style: const TextStyle(fontSize: 12),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton.icon(
                      icon: const Icon(Icons.copy, size: 18),
                      label: const Text('复制地址'),
                      onPressed: () {
                        Clipboard.setData(ClipboardData(text: address));
                        Navigator.pop(context);
                        _showSuccessSnackBar('地址已复制');
                      },
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('关闭'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  // 删除钱包
  Future<void> _deleteWallet(Map<String, dynamic> wallet) async {
    final address = wallet['address']?.toString() ?? '';
    final chain = wallet['chain']?.toString() ?? '';
    
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('确认删除'),
        content: Text('确定要删除 $chain 钱包\n$address 吗？\n\n️ 删除后将无法恢复！'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: const Text('删除'),
          ),
        ],
      ),
    );

    if (confirmed != true) return;

    try {
      await WalletStorage.deleteWallet(address, chain);
      await _loadLocalWallets();
      
      // 如果删除的是当前钱包，清空显示
      if (address == _address) {
        setState(() {
          _address = '未加载钱包';
          _sessionId = null;
          _privateKey = null;
          _mnemonic = null;
        });
        widget.onSessionChanged(null, '未加载钱包', null, null);
      }
      
      _showSuccessSnackBar('钱包已删除');
    } catch (e) {
      _showErrorSnackBar('删除失败: $e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Card(
            color: const Color(0xFF1A1A3E),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('钱包操作', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _createWallet,
                          child: _isLoading ? const CircularProgressIndicator(color: Colors.white) : const Text('创建新钱包'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _importPrivateKey,
                          style: ElevatedButton.styleFrom(backgroundColor: Colors.blue),
                          child: const Text('私钥导入'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _isLoading ? null : _importMnemonic,
                      style: ElevatedButton.styleFrom(backgroundColor: Colors.purple),
                      child: const Text('助记词导入'),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            color: const Color(0xFF1A1A3E),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('钱包信息', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Text('地址: $_address', style: const TextStyle(fontSize: 14)),
                  if (_isBackingUp)
                    const Padding(
                      padding: EdgeInsets.only(top: 8),
                      child: Text('正在备份到云端…', style: TextStyle(color: Colors.orange)),
                    ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton(
                          onPressed: _address != '未加载钱包'
                              ? () {
                                  Clipboard.setData(ClipboardData(text: _address));
                                  _showSuccessSnackBar('地址已复制');
                                }
                              : null,
                          child: const Text('复制地址'),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: OutlinedButton(
                          onPressed: (_address != '未加载钱包' && !_isBackingUp)
                              ? _manualBackup
                              : null,
                          child: const Text('备份到云端'),
                        ),
                      ),
                    ],
                  ),
                  if (_localWallets.isNotEmpty)
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 16),
                        const Text('本地钱包列表', style: TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(height: 8),
                        ..._localWallets.map((w) {
                      final addr = w['address']?.toString() ?? '';
                      final short = addr.length > 16
                          ? '${addr.substring(0, 8)}...${addr.substring(addr.length - 6)}'
                          : addr;
                      final chain = w['chain']?.toString() ?? '';
                      final isCurrentWallet = addr == _address;
                      
                      return Card(
                        margin: const EdgeInsets.only(bottom: 8),
                        color: isCurrentWallet ? const Color(0xFF2A2A5E) : const Color(0xFF1A1A3E),
                        child: ListTile(
                          dense: true,
                          leading: CircleAvatar(
                            backgroundColor: _getChainColor(chain),
                            child: Text(chain.substring(0, 1), style: const TextStyle(fontSize: 12, fontWeight: FontWeight.bold)),
                          ),
                          title: Text(short, style: const TextStyle(fontSize: 13)),
                          subtitle: Text(chain),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              // 二维码按钮
                              IconButton(
                                icon: const Icon(Icons.qr_code, size: 20),
                                onPressed: () => _showQRCode(addr),
                                tooltip: '显示二维码',
                              ),
                              // 删除按钮
                              IconButton(
                                icon: const Icon(Icons.delete_outline, size: 20, color: Colors.redAccent),
                                onPressed: () => _deleteWallet(w),
                                tooltip: '删除钱包',
                              ),
                            ],
                          ),
                          onTap: () => _loadLocalWallet(w),
                        ),
                      );
                    }),
                      ],
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class AssetQueryPage extends StatefulWidget {
  final String network;
  final String address;

  const AssetQueryPage({
    super.key,
    required this.network,
    required this.address,
  });

  @override
  State<AssetQueryPage> createState() => _AssetQueryPageState();
}

class _AssetQueryPageState extends State<AssetQueryPage> {
  String _balance = '0.000000';
  String _selectedToken = '';
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _updateToken();
  }

  void _updateToken() {
    switch (widget.network) {
      case 'TRON':
        _selectedToken = 'TRX';
        break;
      case 'BSC':
        _selectedToken = 'BNB';
        break;
      case 'ETH':
        _selectedToken = 'ETH';
        break;
    }
  }

  void _refreshBalance() async {
    if (widget.address.isEmpty || widget.address == '未加载钱包') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请先创建或导入钱包'), backgroundColor: Colors.orange),
      );
      return;
    }

    setState(() => _isLoading = true);
    try {
      final result = await WalletApiService.getBalance(
        address: widget.address,
        chain: widget.network,
        token: _selectedToken,
      );
      if (result['success']) {
        setState(() {
          _balance = result['balance'].toString();
        });
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('查询失败: $e'), backgroundColor: Colors.red),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Card(
            color: const Color(0xFF1A1A3E),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('选择币种', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    value: _selectedToken,
                    decoration: const InputDecoration(border: OutlineInputBorder()),
                    items: ['TRX', 'USDT', 'BNB', 'ETH'].map((String token) {
                      return DropdownMenuItem(value: token, child: Text(token));
                    }).toList(),
                    onChanged: (val) {
                      setState(() => _selectedToken = val!);
                    },
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            color: const Color(0xFF1A1A3E),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('余额信息', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 12),
                  Text('当前余额: $_balance $_selectedToken', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _isLoading ? null : _refreshBalance,
                      child: _isLoading ? const CircularProgressIndicator(color: Colors.white) : const Text('刷新余额'),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class TransferPage extends StatefulWidget {
  final String network;
  final String? sessionId;
  final String? privateKey;
  final String? mnemonic;

  const TransferPage({
    super.key,
    required this.network,
    this.sessionId,
    this.privateKey,
    this.mnemonic,
  });

  @override
  State<TransferPage> createState() => _TransferPageState();
}

class _TransferPageState extends State<TransferPage> {
  final _addressController = TextEditingController();
  final _amountController = TextEditingController();
  final _memoController = TextEditingController();
  bool _isTransferring = false;

  void _startTransfer() async {
    if (widget.sessionId == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请先创建或导入钱包'), backgroundColor: Colors.orange),
      );
      return;
    }

    if (_addressController.text.isEmpty || _amountController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('请填写收款地址和金额'), backgroundColor: Colors.orange),
      );
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('确认转账'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('收款地址: ${_addressController.text}'),
            const SizedBox(height: 8),
            Text('转账金额: ${_amountController.text}'),
            const SizedBox(height: 8),
            Text('网络: ${widget.network}'),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('取消')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('确认')),
        ],
      ),
    );

    if (confirmed != true) return;

    setState(() => _isTransferring = true);
    try {
      final result = await WalletApiService.transfer(
        sessionId: widget.sessionId ?? '',
        toAddress: _addressController.text,
        amount: double.parse(_amountController.text),
        chain: widget.network,
        memo: _memoController.text,
        privateKey: widget.privateKey,
        mnemonic: widget.mnemonic,
      );

      if (result['success']) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('转账成功！交易哈希: ${result['tx_hash']}'), backgroundColor: Colors.green),
        );
        _addressController.clear();
        _amountController.clear();
        _memoController.clear();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('转账失败: $e'), backgroundColor: Colors.red),
      );
    } finally {
      setState(() => _isTransferring = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Card(
        color: const Color(0xFF1A1A3E),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('转账', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 16),
              const Text('收款地址'),
              TextField(
                controller: _addressController,
                decoration: const InputDecoration(border: OutlineInputBorder()),
              ),
              const SizedBox(height: 16),
              const Text('转账金额'),
              TextField(
                controller: _amountController,
                decoration: const InputDecoration(border: OutlineInputBorder(), hintText: '0.00'),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
              ),
              const SizedBox(height: 16),
              const Text('备注 (可选)'),
              TextField(
                controller: _memoController,
                decoration: const InputDecoration(border: OutlineInputBorder()),
              ),
              const SizedBox(height: 16),
              SizedBox(
                width: double.infinity,
                child: ElevatedButton(
                  onPressed: _isTransferring ? null : _startTransfer,
                  style: ElevatedButton.styleFrom(backgroundColor: Colors.blue, padding: const EdgeInsets.symmetric(vertical: 16)),
                  child: _isTransferring ? const CircularProgressIndicator(color: Colors.white) : const Text('确认转账', style: TextStyle(fontSize: 16)),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class TransactionHistoryPage extends StatefulWidget {
  final String? address;
  
  const TransactionHistoryPage({super.key, this.address});

  @override
  State<TransactionHistoryPage> createState() => _TransactionHistoryPageState();
}

class _TransactionHistoryPageState extends State<TransactionHistoryPage> {
  bool _isLoading = true;
  List<Map<String, dynamic>> _transactions = [];
  String _filterType = 'all'; // all, transfer, bet, exchange

  @override
  void initState() {
    super.initState();
    _loadTransactions();
  }

  Future<void> _loadTransactions() async {
    if (widget.address == null || widget.address!.isEmpty) {
      setState(() => _isLoading = false);
      return;
    }

    setState(() => _isLoading = true);
    try {
      // 加载积分流水（竞猜、兑换）
      final pointsResult = await BettingApiService.getTransactions(widget.address!);
      if (pointsResult['success']) {
        setState(() {
          _transactions = List<Map<String, dynamic>>.from(pointsResult['transactions']);
        });
      }
    } catch (e) {
      print('加载账单失败: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  List<Map<String, dynamic>> get _filteredTransactions {
    if (_filterType == 'all') return _transactions;
    return _transactions.where((t) => t['type'] == _filterType).toList();
  }

  Color _getTypeColor(String type) {
    switch (type) {
      case 'convert':
        return Colors.blue;
      case 'bet':
        return Colors.orange;
      case 'win':
        return Colors.green;
      case 'exchange':
        return Colors.purple;
      default:
        return Colors.grey;
    }
  }

  String _getTypeName(String type) {
    switch (type) {
      case 'convert':
        return '转换积分';
      case 'bet':
        return '竞猜下注';
      case 'win':
        return '竞猜奖励';
      case 'exchange':
        return '积分兑换';
      default:
        return type;
    }
  }

  IconData _getTypeIcon(String type) {
    switch (type) {
      case 'convert':
        return Icons.swap_horiz;
      case 'bet':
        return Icons.sports_esports;
      case 'win':
        return Icons.emoji_events;
      case 'exchange':
        return Icons.attach_money;
      default:
        return Icons.receipt;
    }
  }

  @override
  Widget build(BuildContext context) {
    if (widget.address == null || widget.address!.isEmpty) {
      return const Center(
        child: Text('请先创建或导入钱包', style: TextStyle(color: Colors.white54)),
      );
    }

    return Scaffold(
      body: Column(
        children: [
          // 筛选标签
          Container(
            color: const Color(0xFF1A1A3E),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                _buildFilterChip('all', '全部'),
                const SizedBox(width: 8),
                _buildFilterChip('convert', '转换'),
                const SizedBox(width: 8),
                _buildFilterChip('bet', '竞猜'),
                const SizedBox(width: 8),
                _buildFilterChip('exchange', '兑换'),
              ],
            ),
          ),
          // 账单列表
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _filteredTransactions.isEmpty
                    ? const Center(
                        child: Text('暂无账单记录', style: TextStyle(color: Colors.white54)),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _filteredTransactions.length,
                        itemBuilder: (context, index) {
                          final tx = _filteredTransactions[index];
                          return _buildTransactionCard(tx);
                        },
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String value, String label) {
    final isSelected = _filterType == value;
    return FilterChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (selected) {
        setState(() => _filterType = value);
      },
      backgroundColor: const Color(0xFF2A2A4E),
      selectedColor: const Color(0xFF00FF88).withOpacity(0.3),
      labelStyle: TextStyle(
        color: isSelected ? const Color(0xFF00FF88) : Colors.white70,
      ),
    );
  }

  Widget _buildTransactionCard(Map<String, dynamic> tx) {
    final type = tx['transaction_type'] ?? 'unknown';
    final amount = double.parse(tx['amount'].toString());
    final description = tx['description'] ?? '';
    final createdAt = tx['created_at'] ?? '';
    final balanceAfter = tx['balance_after'] != null ? double.parse(tx['balance_after'].toString()) : 0.0;

    return Card(
      color: const Color(0xFF1A1A3E),
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: _getTypeColor(type).withOpacity(0.2),
          child: Icon(_getTypeIcon(type), color: _getTypeColor(type)),
        ),
        title: Text(
          _getTypeName(type),
          style: const TextStyle(fontWeight: FontWeight.bold),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(description, style: const TextStyle(fontSize: 12, color: Colors.white70)),
            Text(createdAt, style: const TextStyle(fontSize: 11, color: Colors.white54)),
          ],
        ),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              '${amount > 0 ? '+' : ''}${amount.toStringAsFixed(2)} 积分',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: amount > 0 ? Colors.green : Colors.red,
              ),
            ),
            Text(
              '余额: ${balanceAfter.toStringAsFixed(2)}',
              style: const TextStyle(fontSize: 11, color: Colors.white54),
            ),
          ],
        ),
      ),
    );
  }
}


