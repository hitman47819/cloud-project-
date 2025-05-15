# frontend: app.py (running on port 5000)
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import logging
import os
import requests
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Service configuration
SERVICES = {
    'user': 'http://localhost:5001',
    'transaction': 'http://localhost:5002',
    'reporting': 'http://localhost:5003'
}


@app.route('/')
def home():
    return redirect(url_for('dashboard'))

@app.route('/history', methods=['GET'])
def history():
    user_id = session.get('user_id')
    
    if not user_id:
        flash('You must log in to view your transaction history.', 'danger')
        return redirect(url_for('login'))

    try:
        # Fetch the transaction history from the backend
        response = requests.get(f"{SERVICES['transaction']}/received_transactions/{user_id}")
        
        if response.status_code == 200:
            transactions = response.json()
        else:
            flash('Error fetching transaction history. Please try again later.', 'danger')
            return redirect(url_for('dashboard'))

        # Render the history page with the transactions
        return render_template('history.html', transactions=transactions)

    except Exception as e:
        logging.error(f"Error fetching transaction history: {str(e)}")
        flash('An error occurred while loading your transaction history. Please try again later.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            password = request.form.get('password')

            if not email or not password:
                logging.error('Email or password missing')
                flash('Email and password are required.', 'danger')
                return redirect(url_for('login'))

            logging.info(f'Trying to authenticate user: {email}')

            # Make a POST request to the backend to authenticate the user
            response = requests.post(
                f"{SERVICES['user']}/login",
                data={'email': email, 'password': password}
            )

            if response.status_code == 200:
                user_id = response.json().get('user_id')
                logging.info(f'User authenticated, user_id: {user_id}')
                session['user_id'] = user_id  # Store user ID in the session for authentication
                return redirect(url_for('dashboard'))  # Redirect to the dashboard page

            logging.warning(f'Invalid credentials for email: {email}')
            flash('Invalid credentials. Please try again.', 'danger')
            return redirect(url_for('login'))

        except Exception as e:
            logging.error(f"Login error: {str(e)}")
            flash(f'An error occurred. Please try again later. Error: {str(e)}', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    user_id = session.get('user_id')
    
    if not user_id:
        flash('You must log in to access the dashboard.', 'danger')
        return redirect(url_for('login'))

    try:
        logging.info(f"Fetching balance for user_id: {user_id}")

        # Request the user's balance from the backend
        response = requests.get(f"{SERVICES['user']}/user_balance", params={'user_id': user_id})

        if response.status_code == 200:
            balance = response.json().get('balance')
            logging.info(f"Balance for user_id {user_id}: ${balance}")
            return render_template('dashboard.html', balance=balance)
        else:
            logging.error(f"Failed to fetch balance for user_id: {user_id}")
            flash('Error fetching balance. Please try again later.', 'danger')
            return redirect(url_for('login'))

    except Exception as e:
        logging.error(f"Error loading dashboard for user_id {user_id}: {str(e)}")
        flash('An error occurred while loading the dashboard. Please try again later.', 'danger')
        return redirect(url_for('login'))

@app.route('/send', methods=['GET', 'POST'])
def send():
    user_id = session.get('user_id')
    
    if not user_id:
        flash('You must be logged in to send money.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        recipient_email = request.form.get('recipient_email')
        amount = request.form.get('amount')

        # Debugging the form data
        print(f"Recipient Email: {recipient_email}, Amount: {amount}")

        if recipient_email and amount:  # Checks both fields
            try:
                amount = float(amount)  # Convert amount to float

                if amount > 0:
                    # Make a POST request to send money
                    response = requests.post(
                        f"{SERVICES['transaction']}/send",
                        json={'sender_id': user_id, 'recipient_email': recipient_email, 'amount': amount}
                    )

                    if response.status_code == 200:
                        flash(f'Successfully sent ${amount:.2f} to {recipient_email}.', 'success')
                        return redirect(url_for('dashboard'))
                    else:
                        flash('Error sending money. Please try again.', 'danger')
                        return redirect(url_for('send'))

                flash('Amount must be greater than zero.', 'danger')

            except ValueError:
                flash('Invalid amount. Please enter a valid number.', 'danger')

        else:
            flash('Please provide a valid recipient and amount.', 'danger')

    return render_template('send.html')




@app.route('/receive', methods=['GET'])
def receive():
    user_id = session.get('user_id')
    if not user_id:
        flash('You must be logged in to receive money.', 'danger')
        return redirect(url_for('login'))

    try:
        resp = requests.get(f"{SERVICES['transaction']}/received_transactions/{user_id}")
        if resp.status_code == 200:
            transactions = resp.json()
            print("Received transactions JSON:", transactions)  # <-- this should appear in your terminal
            return render_template('receive.html', transactions=transactions)
        else:
            print("Transaction service error:", resp.status_code, resp.text)
            flash('Error fetching received transactions. Please try again later.', 'danger')
            return redirect(url_for('dashboard'))
    except Exception as e:
        print("Exception occurred while fetching transactions:", e)
        flash(f'Error fetching received transactions: {e}', 'danger')
        return redirect(url_for('dashboard'))



# Add the Deposit Money Page
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    user_id = session.get('user_id')

    if not user_id:
        flash('You must be logged in to deposit money.', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        amount = float(request.form.get('amount'))

        if amount > 0:
            # Make a POST request to deposit money

            response = requests.post(
                f"{SERVICES['transaction']}/deposit",
                json={'user_id': user_id, 'amount': amount}
            )

            if response.status_code == 200:
                flash(f'Deposit of ${amount:.2f} successful.', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Error depositing money. Please try again.', 'danger')
                return redirect(url_for('deposit'))

        flash('Please enter a valid amount to deposit.', 'danger')

    return render_template('deposit.html')




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Get form data
            email = request.form.get('email')
            password = request.form.get('password')

            # Check if the form fields are filled
            if not email or not password:
                flash('Email and password are required.', 'danger')
                return redirect(url_for('register'))

            # Send the form data to the backend for registration
            response = requests.post(
                f"{SERVICES['user']}/register",
                data={'email': email, 'password': password},
                timeout=5
            )

            if response.status_code == 201:
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))

            flash(response.json().get('error', 'Registration failed'), 'danger')

        except requests.exceptions.RequestException as e:
            logging.error(f"Service connection error: {str(e)}")
            flash('User service unavailable', 'danger')

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove the user_id from the session
    flash('You have been logged out successfully.', 'success')  # Optional: flash a success message
    return redirect(url_for('login'))  # Redirect the user to the login page

# Add other routes like dashboard, logout, etc.

if __name__ == '__main__':
    app.run(port=5000, debug=True)
    