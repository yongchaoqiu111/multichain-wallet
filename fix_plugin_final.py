file_path = '/opt/personal-website/frontend/download/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 修改第71行（索引70）
if 70 < len(lines):
    print(f"修改前: {lines[70].strip()}")
    lines[70] = lines[70].replace('href="#"', 'href="/download/PointsPanel.exe" download')
    print(f"修改后: {lines[70].strip()}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print("修改成功！")
else:
    print(f"文件只有{len(lines)}行")
