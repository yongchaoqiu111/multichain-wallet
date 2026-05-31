#!/usr/bin/env python3
with open('/etc/nginx/sites-enabled/personal-website', 'r') as f:
    config = f.read()

config = config.replace(
    'Host System.Management.Automation.Internal.Host.InternalHost;',
    'Host $host;'
)
config = config.replace(
    'X-Real-IP ;',
    'X-Real-IP $remote_addr;'
)
config = config.replace(
    'X-Forwarded-For ;',
    'X-Forwarded-For $proxy_add_x_forwarded_for;'
)

with open('/etc/nginx/sites-enabled/personal-website', 'w') as f:
    f.write(config)

print('Nginx配置已修复')
