#!/usr/bin/env python3
"""部署完整钱包 API + 备份服务（SSH: personal-server）"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SSH = ["ssh", "-o", "BatchMode=yes", "personal-server"]
SCP = ["scp", "-o", "BatchMode=yes"]


def run(cmd, check=True):
    print(">", " ".join(cmd))
    r = subprocess.run(cmd, cwd=ROOT)
    if check and r.returncode != 0:
        sys.exit(r.returncode)


def scp(local_rel, remote):
    local = os.path.join(ROOT, local_rel)
    if not os.path.exists(local):
        print(f"跳过: {local_rel}")
        return
    run(SCP + [local, f"personal-server:{remote}"])


def main():
    run(SSH + ["mkdir -p /root/wallet/modules /root/qianbao/houduan"])

    scp("backend/wallet_api_service.py", "/root/wallet/wallet_api_service.py")
    scp("backend/modules/config.py", "/root/wallet/modules/config.py")
    scp("modules/wallet_core.py", "/root/wallet/modules/wallet_core.py")
    scp("backend/requirements.txt", "/root/wallet/requirements.txt")
    scp("mobile_app/backend/.env", "/root/wallet/.env")
    scp("houduan/server.py", "/root/qianbao/houduan/server.py")

    remote = r"""
set -e
cd /root/wallet
pip3 install -r requirements.txt -q 2>/dev/null || pip3 install -r requirements.txt
pkill -f "python3 wallet_api_service.py" || true
sleep 1
nohup python3 wallet_api_service.py > api.log 2>&1 &
sleep 2
echo "=== wallet API health ==="
curl -s http://127.0.0.1:5001/api/health
echo ""
echo "=== balance test ==="
curl -s -X POST http://127.0.0.1:5001/api/wallet/balance \
  -H 'Content-Type: application/json' \
  -d '{"address":"TQn9Y2khEsLJW1ChVWFMSMeRDow5KcbLSE","chain":"TRON"}'
echo ""

cd /root/qianbao/houduan
export DB_PASSWORD='WalletBackup2026!'
export BACKUP_PORT=5002
pkill -f "/root/qianbao/houduan/server.py" || true
pkill -f "python3 server.py" || true
sleep 1
nohup python3 server.py > server_run.log 2>&1 &
sleep 2
echo "=== backup health ==="
curl -s http://127.0.0.1:5002/ 2>/dev/null | head -c 80 || curl -s -X POST http://127.0.0.1:5002/api/wallet/list -H 'Content-Type: application/json' -d '{}' | head -c 200
echo ""

CONF=/etc/nginx/sites-enabled/personal-website
if [ -f "$CONF" ] && grep -q 'location /api/wallet/backup' "$CONF"; then
  if grep -q '127.0.0.1:5000' "$CONF"; then
    sed -i 's|proxy_pass http://127.0.0.1:5000;|proxy_pass http://127.0.0.1:5002;|g' "$CONF"
    nginx -t && systemctl reload nginx
    echo "nginx backup routes -> 5002"
  fi
fi
"""
    run(SSH + ["bash", "-c", remote])
    print("\n部署完成。")


if __name__ == "__main__":
    main()
