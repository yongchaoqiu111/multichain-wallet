#!/usr/bin/env python3
with open('/root/wallet/server.py', 'r') as f:
    lines = f.readlines()

# 找到if __name__行号
main_line = None
for i, line in enumerate(lines):
    if line.strip().startswith('if __name__'):
        main_line = i
        break

if main_line is None:
    print("Error: if __name__ not found")
    exit(1)

# 找到3个mobile API函数的起始和结束行
mobile_start = None
mobile_end = None
for i, line in enumerate(lines):
    if "@app.route('/api/wallet/create'" in line:
        mobile_start = i
    if mobile_start and i > mobile_start and ("@app.route('/admin/" in line or line.strip().startswith('if __name__')):
        mobile_end = i
        break

if mobile_start is None or mobile_end is None:
    print(f"Error: mobile APIs not found properly. start={mobile_start}, end={mobile_end}")
    exit(1)

print(f"Found if __name__ at line {main_line + 1}")
print(f"Found mobile APIs from line {mobile_start + 1} to {mobile_end}")

# 重组：[0..main_line-1] + [mobile APIs] + [main_line..end]
new_lines = lines[:main_line] + lines[mobile_start:mobile_end] + ['\n'] + lines[main_line:]

with open('/root/wallet/server.py', 'w') as f:
    f.writelines(new_lines)

print("Done! File restructured successfully")
