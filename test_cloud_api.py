#!/usr/bin/env python3
"""
测试云端钱包API - 完整功能测试
服务器地址: https://api.ai656.top
"""
import requests
import json

BASE_URL = "https://api.ai656.top/api"

def test_api(endpoint, method='POST', data=None, description=""):
    """测试单个API端点"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"测试: {description}")
    print(f"URL: {url}")
    print(f"方法: {method}")
    if data:
        print(f"参数: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    try:
        if method == 'POST':
            response = requests.post(url, json=data, verify=False)
        else:
            response = requests.get(url, verify=False)
        
        print(f"状态码: {response.status_code}")
        try:
            result = response.json()
            print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            return result
        except:
            print(f"响应内容: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"请求失败: {str(e)}")
        return None

def main():
    print("🚀 开始测试云端钱包API")
    print(f"服务器地址: {BASE_URL}")
    print("="*60)
    
    # 存储测试结果
    test_results = {}
    
    # 1. 创建钱包 - TRON
    print("\n📦 1. 创建TRON钱包")
    result = test_api(
        "/wallet/create",
        method='POST',
        data={"chain": "TRON"},
        description="创建新的TRON钱包"
    )
    if result and result.get('success'):
        test_results['tron_wallet'] = result
        print(f"✅ 创建成功! 地址: {result['address'][:10]}...")
    else:
        print("❌ 创建失败")
    
    # 2. 创建钱包 - BSC
    print("\n📦 2. 创建BSC钱包")
    result = test_api(
        "/wallet/create", 
        method='POST',
        data={"chain": "BSC"},
        description="创建新的BSC钱包"
    )
    if result and result.get('success'):
        test_results['bsc_wallet'] = result
        print(f"✅ 创建成功! 地址: {result['address'][:10]}...")
    
    # 3. 创建钱包 - ETH
    print("\n📦 3. 创建ETH钱包")
    result = test_api(
        "/wallet/create",
        method='POST',
        data={"chain": "ETH"},
        description="创建新的ETH钱包"
    )
    if result and result.get('success'):
        test_results['eth_wallet'] = result
        print(f"✅ 创建成功! 地址: {result['address'][:10]}...")
    
    # 4. 查询余额（使用会话ID）
    if test_results.get('tron_wallet'):
        print("\n💰 4. 查询TRON余额（会话方式）")
        result = test_api(
            "/wallet/balance",
            method='POST',
            data={"session_id": test_results['tron_wallet']['session_id']},
            description="查询钱包余额（会话方式）"
        )
    
    # 5. 查询余额（直接查询）
    if test_results.get('tron_wallet'):
        print("\n💰 5. 查询TRON余额（直接地址）")
        result = test_api(
            "/wallet/balance",
            method='POST',
            data={
                "address": test_results['tron_wallet']['address'],
                "chain": "TRON"
            },
            description="直接查询地址余额"
        )
    
    # 6. 私钥导入测试
    print("\n🔑 6. 私钥导入测试")
    result = test_api(
        "/wallet/import/private_key",
        method='POST',
        data={
            "chain": "TRON",
            "private_key": "7a25d973f86b45d7fbc44e94c589d6570946e2a492a1dd332a8a1b38b5a6b7c9"
        },
        description="通过私钥导入钱包"
    )
    if result and result.get('success'):
        test_results['imported_wallet'] = result
    
    # 7. 助记词导入测试
    print("\n🔑 7. 助记词导入测试")
    result = test_api(
        "/wallet/import/mnemonic",
        method='POST',
        data={
            "chain": "TRON",
            "mnemonic": "apple banana cherry date elderberry fig grape honeydew"
        },
        description="通过助记词导入钱包"
    )
    
    # 8. 估算矿工费
    if test_results.get('tron_wallet'):
        print("\n⚡ 8. 估算矿工费")
        result = test_api(
            "/wallet/estimate_fee",
            method='POST',
            data={"session_id": test_results['tron_wallet']['session_id']},
            description="估算转账矿工费"
        )
    
    # 9. 派生地址测试
    print("\n🔗 9. 派生地址测试")
    result = test_api(
        "/wallet/derive_address",
        method='POST',
        data={
            "chain": "TRON",
            "mnemonic": "apple banana cherry date elderberry fig grape honeydew",
            "account_index": 1
        },
        description="从助记词派生新地址"
    )
    
    # 汇总
    print("\n" + "="*60)
    print("📊 测试汇总")
    print("="*60)
    print(f"已创建钱包: {len([k for k in test_results.keys() if 'wallet' in k])} 个")
    if test_results.get('tron_wallet'):
        print(f"TRON钱包地址: {test_results['tron_wallet']['address']}")
        print(f"TRON钱包会话ID: {test_results['tron_wallet']['session_id']}")
    print("\n🎉 API测试完成!")

if __name__ == "__main__":
    import warnings
    warnings.filterwarnings("ignore", message="Unverified HTTPS request")
    main()
