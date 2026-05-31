file_path = '/opt/personal-website/frontend/download/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到包含"浏览器插件"的行，显示上下文
for i, line in enumerate(lines):
    if '浏览器插件' in line:
        print(f"找到浏览器插件在第{i+1}行")
        # 显示前后15行
        for j in range(max(0, i-15), min(len(lines), i+5)):
            print(f"{j+1}: {lines[j].rstrip()}")
        break
