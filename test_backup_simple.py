from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/wallet/backup', methods=['POST'])
def backup_wallet():
    print("=== Request received ===")
    print(f"Method: {request.method}")
    print(f"Content-Type: {request.content_type}")
    print(f"Data length: {len(request.data)}")
    
    try:
        data = request.get_json(force=True)
        print(f"Parsed data: {data}")
        return jsonify({'success': True, 'message': 'OK'}), 200
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
