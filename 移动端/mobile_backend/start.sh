#!/bin/bash
# 移动端钱包API服务启动脚本

echo "=================================="
echo " 启动钱包API服务"
echo "=================================="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
pip3 install -r requirements.txt > /dev/null 2>&1

# 启动服务
echo "🚀 启动API服务..."
nohup python3 wallet_api_service.py > api.log 2>&1 &

# 等待启动
sleep 2

# 检查是否启动成功
if ps aux | grep "wallet_api_service.py" | grep -v grep > /dev/null; then
    echo "✅ 服务启动成功!"
    echo "📡 服务地址: http://localhost:5001"
    echo "🌐 对外地址: https://api.ai656.top/api"
    echo "📝 日志文件: api.log"
else
    echo "❌ 服务启动失败!"
    cat api.log
    exit 1
fi
