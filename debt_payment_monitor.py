"""
欠款支付监控系统
监控用户向指定地址转账TRX，自动确认支付并更新欠款状态
"""
import pymysql
import requests
import time
import threading
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'WalletBackup2026!',
    'database': 'wallet_backup',
    'charset': 'utf8mb4'
}

# 收款地址
RECEIVE_ADDRESS = 'TBo93T5a1iP31rdFF8aeowaDvrhxVbCjac'

# TronScan API配置
TRONSCAN_API_KEY = ''  # 需要配置API Key
MONITOR_INTERVAL = 10  # 每10秒查询一次

db_lock = threading.Lock()


def get_unpaid_debts():
    """获取所有待支付的欠款订单"""
    with db_lock:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        cursor.execute("USE wallet_backup")
        cursor.execute('''
            SELECT id, address, debt_amount, paid_amount, created_at
            FROM user_debts
            WHERE status = 0
            ORDER BY created_at ASC
        ''')
        debts = cursor.fetchall()
        cursor.close()
        conn.close()
    return debts


def check_tron_transactions(address):
    """
    查询TRON链上指定地址的交易记录
    返回最近的交易列表
    """
    try:
        if not TRONSCAN_API_KEY:
            # 没有API Key时返回空，但不报错
            return []
        
        url = "https://apilist.tronscanapi.com/api/transaction"
        params = {
            "address": address,
            "limit": 50,
            "sort": "-timestamp",
            "token": "TRX"  # 只查询TRX交易
        }
        headers = {
            "TRON-PRO-API-KEY": TRONSCAN_API_KEY
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            print(f"❌ TronScan API请求失败: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ 查询交易失败: {str(e)}")
        return []


def process_debt_payment(debt_id, address, debt_amount, tx_hash, actual_amount):
    """
    处理欠款支付
    更新数据库状态
    """
    with db_lock:
        conn = pymysql.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("USE wallet_backup")
        
        try:
            # 更新欠款记录
            cursor.execute('''
                UPDATE user_debt
                SET paid_amount = paid_amount + %s,
                    status = CASE WHEN paid_amount + %s >= debt_amount THEN 1 ELSE 0 END,
                    updated_at = NOW()
                WHERE id = %s
            ''', (actual_amount, actual_amount, debt_id))
            
            # 记录支付流水
            cursor.execute('''
                INSERT INTO debt_payments (debt_id, address, tx_hash, amount, paid_at)
                VALUES (%s, %s, %s, %s, NOW())
            ''', (debt_id, address, tx_hash, actual_amount))
            
            conn.commit()
            print(f"✅ 欠款订单 {debt_id} 支付成功！")
            print(f"   交易哈希: {tx_hash}")
            print(f"   支付金额: {actual_amount} TRX")
            
            return True
            
        except Exception as e:
            conn.rollback()
            print(f"❌ 更新数据库失败: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()


def monitor_debts():
    """监控所有待支付欠款"""
    print(f"🔍 开始监控欠款支付，收款地址: {RECEIVE_ADDRESS}")
    print(f"⏱ 查询间隔: {MONITOR_INTERVAL}秒")
    
    # 记录已处理的交易哈希，避免重复处理
    processed_txs = set()
    
    while True:
        try:
            # 获取所有待支付欠款
            debts = get_unpaid_debts()
            
            if not debts:
                time.sleep(MONITOR_INTERVAL)
                continue
            
            print(f"\n📊 当前待支付订单: {len(debts)} 个")
            
            # 查询收款地址的交易记录
            transactions = check_tron_transactions(RECEIVE_ADDRESS)
            
            if not transactions:
                time.sleep(MONITOR_INTERVAL)
                continue
            
            # 检查每笔交易
            for tx in transactions:
                tx_hash = tx.get('hash', '')
                
                # 跳过已处理的交易
                if tx_hash in processed_txs:
                    continue
                
                # 获取交易详情
                from_address = tx.get('ownerAddress', '')
                amount_sun = tx.get('raw_data', {}).get('contract', [{}])[0].get('parameter', {}).get('value', {}).get('amount', 0)
                amount_trx = amount_sun / 1_000_000  # 转换为TRX
                
                # 匹配欠款订单
                for debt in debts:
                    if debt['address'] == from_address:
                        # 检查金额是否匹配（允许误差0.01 TRX）
                        if abs(amount_trx - debt['debt_amount']) < 0.01:
                            print(f"\n✅ 发现匹配交易！")
                            print(f"   用户: {from_address}")
                            print(f"   金额: {amount_trx} TRX")
                            print(f"   订单ID: {debt['id']}")
                            
                            # 处理支付
                            if process_debt_payment(debt['id'], from_address, debt['debt_amount'], tx_hash, amount_trx):
                                processed_txs.add(tx_hash)
                            break
                
                # 限制查询数量
                if len(processed_txs) > 1000:
                    processed_txs = set(list(processed_txs)[-500:])  # 只保留最近500条
            
            time.sleep(MONITOR_INTERVAL)
            
        except KeyboardInterrupt:
            print("\n⏹ 监控停止")
            break
        except Exception as e:
            print(f"❌ 监控错误: {str(e)}")
            time.sleep(MONITOR_INTERVAL)


if __name__ == '__main__':
    monitor_debts()
