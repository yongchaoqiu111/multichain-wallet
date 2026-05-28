#!/bin/bash
# 重启钱包 API 服务

pkill -f wallet_api_service.py
sleep 2

cd /root/wallet
nohup python3.13 wallet_api_service.py >> api.log 2>&1 &

echo "✅ API 服务已重启"
sleep 2
ps aux | grep wallet_api_service.py | grep -v grep
