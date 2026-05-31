#!/bin/bash
for i in $(seq 1 33); do
    file=$(printf "/var/lib/mysql/binlog.%06d" $i)
    if [ -f "$file" ]; then
        count=$(mysqlbinlog --base64-output=DECODE-ROWS -v "$file" 2>/dev/null | grep -c 'DELETE FROM.*wallet_backups')
        if [ $count -gt 0 ]; then
            echo "=== binlog.$(printf '%06d' $i): $count 次删除 ==="
            mysqlbinlog --base64-output=DECODE-ROWS -v "$file" 2>/dev/null | grep -B5 'DELETE FROM.*wallet_backups' | head -10
        fi
    fi
done
