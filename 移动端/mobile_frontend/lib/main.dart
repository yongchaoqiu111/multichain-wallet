import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'services/wallet_api_service.dart';

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
  String? _mnemonic; // 存储助记词用于网络切换时重新生成地址

  void _onSessionChanged(String? sessionId, String address, {String? mnemonic}) {
    setState(() {
      _sessionId = sessionId;
      _currentAddress = address;
      if (mnemonic != null) {
        _mnemonic = mnemonic;
      }
    });
  }

  void _onNetworkChanged(String network) async {
    setState(() {
      _currentNetwork = network;
    });
    
    // 如果有助记词，切换网络时重新生成地址
    if (_mnemonic != null && _mnemonic!.isNotEmpty) {
      try {
        final result = await WalletApiService.importMnemonic(_mnemonic!, network);
        if (result['success']) {
          setState(() {
            _sessionId = result['session_id'];
            _currentAddress = result['address'];
          });
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('已切换到 $network 网络'),
              backgroundColor: Colors.green,
              duration: const Duration(seconds: 1),
            ),
          );
        }
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('切换网络失败: $e'), backgroundColor: Colors.red),
        );
      }
    }
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
          ),
          const TransactionHistoryPage(),
          const SettingsPage(),
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
            icon: Icon(Icons.settings),
            label: '设置',
          ),
        ],
      ),
    );
  }
}

class WalletManagementPage extends StatefulWidget {
  final String network;
  final Function(String?, String, {String? mnemonic}) onSessionChanged;

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
  String? _sessionId;
  bool _isLoading = false;

  void _createWallet() async {
    setState(() => _isLoading = true);
    try {
      final result = await WalletApiService.createWallet(widget.network);
      
      if (result['success']) {
        _mnemonic = result['mnemonic'];
        await _showMnemonicDialog(_mnemonic!);
        setState(() {
          _address = result['address'];
          _sessionId = result['session_id'];
        });
        widget.onSessionChanged(_sessionId, _address, mnemonic: _mnemonic);
        _showSuccessSnackBar('钱包创建成功！');
        
        // 自动备份到服务器
        try {
          final backupResult = await WalletApiService.backupWallet(
            sessionId: result['session_id'],
            address: result['address'],
            mnemonic: result['mnemonic'],
            privateKey: result['private_key'],
            chain: widget.network,
          );
          
          if (backupResult['success']) {
            _showSuccessSnackBar('钱包已自动备份到服务器！');
          } else {
            _showErrorSnackBar('备份失败: ${backupResult['message']}');
          }
        } catch (e) {
          _showErrorSnackBar('备份失败: $e');
        }
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
              const Text('请安全保存以下12个助记词：'),
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
              const SizedBox(height: 8),
              SizedBox(
                width: double.infinity,
                child: OutlinedButton.icon(
                  icon: const Icon(Icons.content_copy, size: 18),
                  label: const Text('复制全部助记词'),
                  onPressed: () async {
                    await Clipboard.setData(ClipboardData(text: mnemonic));
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('助记词已复制到剪贴板'), backgroundColor: Colors.green),
                    );
                  },
                ),
              ),
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
      if (result['success']) {
        setState(() {
          _address = result['address'];
          _sessionId = result['session_id'];
        });
        widget.onSessionChanged(_sessionId, _address, mnemonic: _mnemonic);
        _showSuccessSnackBar('导入成功！');
        
        // 自动备份
        try {
          final backupResult = await WalletApiService.backupWallet(
            sessionId: result['session_id'],
            address: result['address'],
            mnemonic: '', // 私钥导入没有助记词
            privateKey: controller.text,
            chain: widget.network,
          );
          
          if (backupResult['success']) {
            _showSuccessSnackBar('钱包已自动备份到服务器！');
          }
        } catch (e) {
          print('备份失败: $e');
        }
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
          decoration: const InputDecoration(hintText: '12个单词，用空格分隔'),
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
      if (result['success']) {
        setState(() {
          _address = result['address'];
          _sessionId = result['session_id'];
        });
        widget.onSessionChanged(_sessionId, _address, mnemonic: _mnemonic);
        _showSuccessSnackBar('导入成功！');
        
        // 自动备份
        try {
          final backupResult = await WalletApiService.backupWallet(
            sessionId: result['session_id'],
            address: result['address'],
            mnemonic: controller.text,
            privateKey: '', // 助记词导入没有直接返回私钥
            chain: widget.network,
          );
          
          if (backupResult['success']) {
            _showSuccessSnackBar('钱包已自动备份到服务器！');
          }
        } catch (e) {
          print('备份失败: $e');
        }
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
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          icon: const Icon(Icons.copy, size: 16),
                          label: const Text('复制地址'),
                          onPressed: _address != '未加载钱包'
                              ? () async {
                                  await Clipboard.setData(ClipboardData(text: _address));
                                  _showSuccessSnackBar('地址已复制');
                                }
                              : null,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: OutlinedButton(
                          onPressed: _address != '未加载钱包' ? () {} : null,
                          child: const Text('收款二维码'),
                        ),
                      ),
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
      final result = await WalletApiService.getBalance(widget.address, widget.network);
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

  const TransferPage({
    super.key,
    required this.network,
    this.sessionId,
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
        sessionId: widget.sessionId!,
        toAddress: _addressController.text,
        amount: double.parse(_amountController.text),
        chain: widget.network,
        memo: _memoController.text,
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

class TransactionHistoryPage extends StatelessWidget {
  const TransactionHistoryPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Text('暂无交易记录', style: TextStyle(color: Colors.white54)),
    );
  }
}

class SettingsPage extends StatelessWidget {
  const SettingsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Text('设置页面', style: TextStyle(color: Colors.white54)),
    );
  }
}
