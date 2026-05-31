import sys

file_path = '/opt/personal-website/frontend/download/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到包含"Android"的行，然后查看前面的<a>标签
for i, line in enumerate(lines):
    if 'Android 版下载' in line:
        # 往前找<a>标签
        for j in range(max(0, i-5), i+1):
            print(f"{j}: {lines[j].rstrip()}")
        break
