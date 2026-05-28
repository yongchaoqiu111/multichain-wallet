import sys

with open('/root/qianbao/houduan/server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 找到 restore_wallet 函数的结尾部分，添加错误日志
old_code = '''        return jsonify({
            'success': True,
            'message': '恢复成功',
            'data': decrypted_data
        }), 200'''

new_code = '''    except Exception as e:
        print(f"restore_wallet 错误: {str(e)}", flush=True)
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'服务器错误: {str(e)}'}), 500

        return jsonify({
            'success': True,
            'message': '恢复成功',
            'data': decrypted_data
        }), 200'''

# 找到函数的 try 块开始
if 'def restore_wallet():' in content and 'try:' not in content.split('def restore_wallet():')[1].split('def ')[0]:
    # 在函数开始添加 try
    content = content.replace(
        "def restore_wallet():\n    data = request.get_json()",
        "def restore_wallet():\n    try:\n        data = request.get_json()"
    )
    
    # 在 return 之前添加 except
    content = content.replace(old_code, new_code)

with open('/root/qianbao/houduan/server.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('已添加错误日志！')
