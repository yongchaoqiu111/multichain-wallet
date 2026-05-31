#!/usr/bin/env python3
with open('/root/wallet/server.py', 'r') as f:
    lines = f.readlines()

# 在第51行后插入except块
lines.insert(51, '    except Exception:\n')
lines.insert(52, '        return "ai-wallet-query-2026"\n')

with open('/root/wallet/server.py', 'w') as f:
    f.writelines(lines)

print("Fixed!")
