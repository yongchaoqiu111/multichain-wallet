file_path = '/opt/personal-website/frontend/download/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"总行数: {len(lines)}")
print(f"第62行内容: {repr(lines[61])}")
print(f"第62行内容: {lines[61]}")
