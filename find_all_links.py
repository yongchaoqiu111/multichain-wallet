file_path = '/opt/personal-website/frontend/download/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    lines = content.split('\n')

# 查找所有download-btn
for i, line in enumerate(lines):
    if 'download-btn' in line and 'href' in line:
        # 显示这行和后面3行
        print(f"第{i+1}行:")
        for j in range(i, min(len(lines), i+4)):
            print(f"  {lines[j]}")
        print()
