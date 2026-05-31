file_path = '/opt/personal-website/frontend/download/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 修改第62行（索引61）
if 61 < len(lines):
    lines[61] = lines[61].replace('href="#"', 'href="/download/app.apk" download')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('修改成功')
else:
    print(f'文件只有{len(lines)}行')
