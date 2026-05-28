@echo off
chcp 65001
echo 开始打包钱包应用...

pyinstaller --noconfirm "多链钱包工具.spec"

echo.
echo 打包完成！exe在 dist\WalletApp\WalletApp.exe

pause
