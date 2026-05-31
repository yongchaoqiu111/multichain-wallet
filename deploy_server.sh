#!/bin/bash
# 在服务器上执行：部署钱包 API(5001) + 备份服务(5002) + Nginx
set -e

WALLET_DIR=/root/wallet
HOUDUAN_DIR=/root/qianbao/houduan
NGINX_CONF=/etc/nginx/sites-enabled/personal-website

echo "=== 1. 重启钱包 API :5001 ==="
cd "$WALLET_DIR"
pip3 install -q Flask Flask-CORS requests mnemonic bip32utils ecdsa base58 pycryptodome web3 tronpy 2>/dev/null || true
pkill -f "python3 wallet_api_service.py" || true
sleep 1
nohup python3 wallet_api_service.py >> api.log 2>&1 &
sleep 2
curl -s http://127.0.0.1:5001/api/health
echo ""

echo "=== 2. 启动备份服务 :5002 ==="
cd "$HOUDUAN_DIR"
pip3 install -q Flask Flask-CORS pymysql cryptography 2>/dev/null || true
export DB_PASSWORD='WalletBackup2026!'
export BACKUP_PORT=5002
pkill -f "${HOUDUAN_DIR}/server.py" || true
pkill -f "python3 server.py" || true
sleep 1
nohup python3 server.py >> server_run.log 2>&1 &
sleep 3
curl -s -X POST http://127.0.0.1:5002/api/wallet/list -H 'Content-Type: application/json' -d '{}' | head -c 300
echo ""

echo "=== 3. Nginx 备份路由 -> 5002 ==="
for loc in backup list restore delete; do
  sed -i "/location \/api\/wallet\/${loc}/,/}/ s|http://127.0.0.1:5000|http://127.0.0.1:5002|g" "$NGINX_CONF"
done
nginx -t && systemctl reload nginx
grep -A2 'location /api/wallet/backup' "$NGINX_CONF"

echo "=== 4. 外网备份测试 ==="
curl -s -X POST https://api.ai656.top/api/wallet/backup \
  -H 'Content-Type: application/json' \
  -d '{"address":"TTestDeploy123","chain":"TRON","encrypted_data":"{\"private_key\":\"pk\",\"mnemonic\":\"\",\"address\":\"TTestDeploy123\"}"}' | head -c 200
echo ""
echo "=== 完成 ==="
