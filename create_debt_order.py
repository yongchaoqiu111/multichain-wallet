import pymysql
import random

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'WalletBackup2026!',
    'database': 'wallet_backup',
    'charset': 'utf8mb4'
}

def create_debt_order(address, lost_points):
    """生成待支付订单"""
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # 计算应付TRX金额：欠款 - 随机减免(0.01~0.99)
    discount = random.uniform(0.01, 0.99)
    pay_amount = round(lost_points - discount, 2)
    
    # 插入欠款记录
    cursor.execute('''
        INSERT INTO user_debts (address, debt_amount, paid_amount, status)
        VALUES (%s, %s, 0, 0)
    ''', (address, pay_amount))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return {
        'address': address,
        'pay_to': 'TBo93T5a1iP31rdFF8aeowaDvrhxVbCjac',
        'debt_amount': lost_points,
        'pay_amount': pay_amount,
        'discount': round(discount, 2)
    }

if __name__ == '__main__':
    # 测试
    result = create_debt_order('test_address_123', 1000)
    print(f"欠款订单生成成功：")
    print(f"用户地址: {result['address']}")
    print(f"欠款积分: {result['debt_amount']}")
    print(f"应付TRX: {result['pay_amount']}")
    print(f"收款地址: {result['pay_to']}")
    print(f"优惠减免: {result['discount']} TRX")
