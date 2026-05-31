nginx_conf = """server {
    listen 80;
    server_name chaseqiu.top www.chaseqiu.top ai656.top www.ai656.top api.ai656.top;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name chaseqiu.top www.chaseqiu.top ai656.top www.ai656.top api.ai656.top;

    ssl_certificate /etc/letsencrypt/live/chaseqiu.top/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chaseqiu.top/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location /666/ {
        root /opt/personal-website;
        index index.html;
        try_files $uri $uri/ /666/index.html;
    }

    location / {
        root /opt/personal-website/frontend;
        try_files $uri $uri/ /index.html;
    }

    location /admin/ {
        proxy_pass http://127.0.0.1:5001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
    }

    location /betting {
        proxy_pass http://127.0.0.1:5004/betting;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
    }

    # 钱包API
    location /api/wallet/create {
        proxy_pass http://127.0.0.1:5000/api/wallet/create;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
    }

    location /api/wallet/import/private_key {
        proxy_pass http://127.0.0.1:5000/api/wallet/import/private_key;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
    }

    location /api/wallet/import/mnemonic {
        proxy_pass http://127.0.0.1:5000/api/wallet/import/mnemonic;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:5002/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_http_version 1.1;
    }
}
"""

with open('/etc/nginx/sites-enabled/personal-website', 'w') as f:
    f.write(nginx_conf)

print("Nginx配置已更新")
