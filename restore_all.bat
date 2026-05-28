@echo off
chcp 65001 >nul
echo ========================================
echo   钱包服务一键恢复脚本
echo ========================================
echo.

echo [1/4] 上传服务文件到服务器...
scp -i C:\Users\Administrator\.ssh\id_rsa_personal_website F:\web\backend\list_service.py root@personal-server:/root/wallet/list_service.py
scp -i C:\Users\Administrator\.ssh\id_rsa_personal_website F:\web\backend\server_wallet.py root@personal-server:/root/wallet/server_wallet.py
scp -i C:\Users\Administrator\.ssh\id_rsa_personal_website F:\web\backend\server.py root@personal-server:/root/wallet/server.py

echo.
echo [2/4] 上传Nginx配置...
scp -i C:\Users\Administrator\.ssh\id_rsa_personal_website F:\web\backend\nginx_config_backup root@personal-server:/etc/nginx/sites-enabled/personal-website

echo.
echo [3/4] 重启Nginx...
ssh root@personal-server "nginx -t && systemctl reload nginx"

echo.
echo [4/4] 重启所有服务...
ssh root@personal-server "pkill -9 python3.13; sleep 2; cd /root/wallet && nohup python3.13 list_service.py > list_5001.log 2>&1 & nohup python3.13 server_wallet.py > wallet_5003.log 2>&1 & nohup python3.13 server.py > backup_5002.log 2>&1 &"

echo.
echo ========================================
echo   恢复完成！等待5秒后测试...
echo ========================================
timeout /t 5 /nobreak >nul

echo.
echo 测试接口...
curl.exe -s https://api.ai656.top/api/wallet/list | findstr "success"
curl.exe -s -X POST https://api.ai656.top/api/wallet/create -H "Content-Type: application/json" -d "{\"chain\":\"TRON\"}" | findstr "success"
curl.exe -s -X POST https://api.ai656.top/api/wallet/backup -H "Content-Type: application/json" -d "{\"chain\":\"TRON\",\"address\":\"test\",\"encrypted_data\":\"test\"}" | findstr "success"

echo.
echo ========================================
echo   所有服务已恢复！
echo ========================================
pause
