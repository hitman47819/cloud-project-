import sys
import os
from flask import Flask, request, jsonify
import requests

from transaction_manager import TransactionManager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.db_config import get_db_connection
from common.db_config import init_db  # <-- import this

app = Flask(__name__)

# Initialize transaction manager
transaction_manager = TransactionManager()

@app.route('/balance/<int:user_id>', methods=['GET'])
def get_balance(user_id):
    balance = transaction_manager.get_balance(user_id)
    return jsonify({'balance': balance})
from flask import current_app
@app.route('/user_by_email', methods=['GET'])
@app.route('/user_by_email', methods=['GET'])
def get_user_by_email():
    email = request.args.get('email')  # Get the email parameter from the URL
    if not email:
        return jsonify({'error': 'Email parameter is required'}), 400

    # Real query to fetch user details from the database
    with get_db_connection() as conn:
        user = conn.execute('''
            SELECT id, email, balance FROM users WHERE email = ?
        ''', (email,)).fetchone()

        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'id': user['id'],
            'email': user['email'],
            'balance': user['balance']
        }), 200

@app.route('/send', methods=['POST'])
def send_money():
    data = request.get_json()
    if not data:
        print(f"Raw request body: {request.data}")  # Debug: see raw data
        return jsonify({'error': 'No JSON data provided'}), 400

    print("Received send request:", data)  # Debugging

    sender_id = data.get('sender_id')
    recipient_email = data.get('recipient_email')
    amount = data.get('amount')

    if not sender_id or not recipient_email or not amount:
        return jsonify({'error': 'Missing sender_id, recipient_email, or amount'}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than zero'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid amount format'}), 400

    # Fetch recipient user data from user service
    user_service = current_app.config.get('USER_SERVICE_URL', 'http://localhost:5002')

    try:
        response = requests.get(f"{user_service}/user_by_email", params={'email': recipient_email})
        if response.status_code != 200:
            print(f"Failed to get recipient: {response.status_code} - {response.text}")  # Debug
            return jsonify({'error': 'Recipient not found'}), 404

        recipient_data = response.json()
        receiver_id = recipient_data.get('id')

        if not receiver_id:
            return jsonify({'error': 'Recipient has no ID'}), 404

        # Send the money
        success = transaction_manager.send(sender_id, receiver_id, amount)
        if success:
            return jsonify({'message': f'Sent ${amount:.2f} to {recipient_email}'}), 200
        else:
            return jsonify({'error': 'Transaction failed: insufficient funds or invalid accounts'}), 400

    except requests.exceptions.RequestException as e:
        print(f"Exception contacting user service: {e}")  # Debug
        return jsonify({'error': f'Failed to contact user service: {str(e)}'}), 500




 

from flask import request

# alias /receive?user_id=… to /received_transactions/<user_id>
@app.route('/receive', methods=['GET'])
def receive_alias():
    user_id = request.args.get('user_id', type=int)
    if user_id is None:
        return jsonify({'error': 'user_id required'}), 400
    transactions = transaction_manager.get_received_transactions(user_id)
    return jsonify(transactions), 200




@app.route('/deposit', methods=['POST'])
def deposit_money():
    data = request.get_json()
    if not data:
        print(f"Raw request body: {request.data}")  # Debugging request body
        return jsonify({'error': 'No JSON data provided'}), 400

    print("Received deposit request:", data)  # Debugging
    if 'user_id' not in data or 'amount' not in data:
        return jsonify({'error': 'Invalid request'}), 400

    user_id = data['user_id']
    amount = data['amount']

    if amount <= 0:
        return jsonify({'error': 'Amount must be positive'}), 400

    success = transaction_manager.deposit(user_id, amount)

    if success:
        return jsonify({'message': f'Deposit of ${amount} successful'}), 200
    else:
        return jsonify({'error': 'Invalid deposit amount'}), 400





@app.route('/received_transactions/<int:user_id>', methods=['GET'])
def get_received_transactions(user_id):
    transactions = transaction_manager.get_received_transactions(user_id)
    return jsonify(transactions), 200

if __name__ == '__main__':
    app.run(debug=True, port=5002)
