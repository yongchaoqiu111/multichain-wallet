#!/usr/bin/env python3
"""在 Nginx 配置中添加 API 代理"""

config_file = "/etc/nginx/sites-enabled/personal-website"

# 读取现有配置
with open(config_file, 'r') as f:
    lines = f.readlines()

# 找到 location /admin/ 的位置，在前面插入
new_lines = []
for i, line in enumerate(lines):
    if 'location /admin/' in line:
        # 插入新的 location 块
        new_lines.append('    location /api/ {\n')
        new_lines.append('        proxy_pass http://127.0.0.1:5001/api/;\n')
        new_lines.append('        proxy_set_header Host $host;\n')
        new_lines.append('        proxy_set_header X-Real-IP $remote_addr;\n')
        new_lines.append('        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n')
        new_lines.append('        proxy_set_header X-Forwarded-Proto $scheme;\n')
        new_lines.append('    }\n\n')
    new_lines.append(line)

# 写回文件
with open(config_file, 'w') as f:
    f.writelines(new_lines)

print("配置已更新")
