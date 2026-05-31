import re

# 读取Nginx配置
with open('/etc/nginx/sites-enabled/personal-website', 'r') as f:
    content = f.read()

# 在 /api/wallet/import/mnemonic 后面添加 balance 路由
balance_location = """
    location /api/wallet/balance {
        proxy_pass http://127.0.0.1:5000/api/wallet/balance;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
    }
"""

# 找到 mnemonic 路由的位置并插入
pattern = r'(location /api/wallet/import/mnemonic \{[^}]+\})'
match = re.search(pattern, content)
if match:
    insert_pos = match.end()
    content = content[:insert_pos] + balance_location + content[insert_pos:]
    
    with open('/etc/nginx/sites-enabled/personal-website', 'w') as f:
        f.write(content)
    print("已添加 balance 路由")
else:
    print("未找到插入位置")
