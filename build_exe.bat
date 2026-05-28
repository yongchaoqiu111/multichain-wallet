@echo off
chcp 65001 >nul
echo ========================================
echo 正在打包多链钱包工具...
echo ========================================

REM 检查是否安装PyInstaller
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyInstaller...
    python -m pip install pyinstaller
)

REM 清理旧的构建文件
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM 打包程序
echo 开始打包...
pyinstaller --name="多链钱包工具" ^
    --windowed ^
    --onefile ^
    --icon=NONE ^
    --add-data "modules;modules" ^
    --add-data "data;data" ^
    --hidden-import=web3 ^
    --hidden-import=tronpy ^
    --collect-all web3 ^
    --collect-all tronpy ^
    main.py

if exist dist\多链钱包工具.exe (
    echo.
    echo ========================================
    echo 打包成功！
    echo EXE位置: dist\多链钱包工具.exe
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 打包失败，请检查错误信息
    echo ========================================
)

pause
