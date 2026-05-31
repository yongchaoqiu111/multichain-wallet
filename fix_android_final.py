file_path = '/opt/personal-website/frontend/download/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到包含Android和href="#"的行
for i, line in enumerate(lines):
    if 'Android 版下载' in line:
        print(f"找到Android在第{i+1}行")
        # 往前查找<a>标签
        for j in range(max(0, i-10), i+1):
            if 'href="#"' in lines[j] and 'download-btn' in lines[j]:
                print(f"找到链接在第{j+1}行: {lines[j].strip()}")
                # 修改这行
                lines[j] = lines[j].replace('href="#"', 'href="/download/app.apk" download')
                print(f"修改后: {lines[j].strip()}")
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                print("修改成功！")
                break
        break
