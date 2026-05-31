#!/usr/bin/env python3
import requests
import json

# 测试API返回的数据
url = 'https://api.ai656.top/api/wallet/list'
headers = {
    'Content-Type': 'application/json',
    'X-Auth-Password': 'admin123'
}

try:
    response = requests.post(url, headers=headers, timeout=10)
    data = response.json()
    
    print(f"成功: {data.get('success')}")
    print(f"钱包数量: {data.get('count')}")
    
    if data.get('wallets'):
        wallet = data['wallets'][0]
        print(f"\n第一条钱包数据:")
        for key, value in wallet.items():
            if key == 'encrypted_data':
                # 只显示前50个字符
                display_value = f"{value[:50]}..." if value else "None"
                print(f"  {key}: {display_value}")
                print(f"  {key}_length: {len(value) if value else 0}")
                print(f"  {key}_type: {type(value)}")
            else:
                print(f"  {key}: {value}")
        
        # 检查encrypted_data是否是Base64格式
        import base64
        encrypted_data = wallet.get('encrypted_data')
        if encrypted_data:
            try:
                decoded = base64.b64decode(encrypted_data)
                print(f"\n✅ Base64解码成功，长度: {len(decoded)} bytes")
                print(f"   前12字节(nonce): {decoded[:12].hex()}")
                print(f"   剩余字节(ciphertext): {len(decoded[12:])} bytes")
            except Exception as e:
                print(f"\n❌ Base64解码失败: {e}")
                
except Exception as e:
    print(f"请求失败: {e}")
