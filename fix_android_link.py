import sys

file_path = '/opt/personal-website/frontend/download/index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 找到Android下载按钮的链接并修改
old_text = '''                    <a href="#" class="download-btn">
                        <div class="download-btn-icon"></div>
                        <div class="download-btn-info">
                            <h3>Android 版下载</h3>'''

new_text = '''                    <a href="/download/app.apk" class="download-btn" download>
                        <div class="download-btn-icon">🤖</div>
                        <div class="download-btn-info">
                            <h3>Android 版下载</h3>'''

content = content.replace(old_text, new_text)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('修改成功')
