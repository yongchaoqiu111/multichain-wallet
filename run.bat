@echo off
chcp 65001 >nul
echo ========================================
echo 多链钱包工具 - 快速启动
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    pause
    exit /b 1
)

echo [1/3] 检查依赖...
pip show PyQt6 >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
) else (
    echo 依赖已安装
)

echo.
echo [2/3] 启动程序...
echo.

python main.py

if errorlevel 1 (
    echo.
    echo [错误] 程序运行失败
    pause
)
