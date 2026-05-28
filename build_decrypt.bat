@echo off
chcp 65001
echo 开始打包客服解密工具...

pyinstaller --name=DecryptTool --windowed --hidden-import=requests --hidden-import=base64 decrypt_tool_gui.py

echo.
echo 打包完成！exe在 dist\DecryptTool\DecryptTool.exe

pause
