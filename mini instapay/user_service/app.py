# backend: user_service.py (running on port 5001)
from flask import Flask, request, jsonify
from user_manager import UserManager
import logging
from flask_cors import CORS

app = Flask(__name__)
user_manager = UserManager()
# Enable CORS for all routes
CORS(app)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

@app.route('/login', methods=['POST'])
def login():
    try:
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400

        logging.debug(f"Attempting login with email: {email}")

        if user_manager.authenticate_user(email, password):
            user_id = user_manager.get_user_id(email)
            return jsonify({'user_id': user_id}), 200
        return jsonify({'error': 'Invalid credentials'}), 401

    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/register', methods=['POST'])
def register():
    try:
        # Get form data
        email = request.form.get('email')
        password = request.form.get('password')

        # Validate the form data
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400

        # Check if the user already exists
        if user_manager.user_exists(email):
            return jsonify({'error': 'Email already registered'}), 400

        # Create the user
        user_manager.create_user(email, password)
        return jsonify({'message': 'Registration successful'}), 201

    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/user_balance', methods=['GET'])
def get_balance():
    try:
        user_id = request.args.get('user_id')

        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400

        balance = user_manager.get_user_balance(user_id)
        if balance is not None:
            return jsonify({'balance': balance}), 200

        return jsonify({'error': 'Balance not found'}), 404

    except Exception as e:
        logging.error(f"Error fetching balance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(port=5001, debug=True)
