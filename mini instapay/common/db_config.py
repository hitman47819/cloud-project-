from flask import Flask, request, jsonify
import sqlite3
import os
from contextlib import contextmanager

# Database configuration
DATABASE = 'instapay.db'
DATABASE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', DATABASE)

@contextmanager
def get_db_connection():
    """Establishes and returns a connection to the SQLite database with automatic cleanup."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Allows column access by name
    conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initializes the database with required tables and indexes."""
    print("Initializing the database...")
    with get_db_connection() as conn:
        # Users table with additional security fields
        conn.execute(''' 
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                balance REAL DEFAULT 0.0 CHECK(balance >= 0),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT,
                is_active INTEGER DEFAULT 1
            )
        ''')
        print("Users table created.")

        # Transactions table with enhanced fields
        conn.execute(''' 
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                type TEXT CHECK(type IN ('deposit', 'withdrawal', 'transfer')),
                amount REAL NOT NULL CHECK(amount > 0),
                counterparty_id INTEGER,
                description TEXT,
                status TEXT DEFAULT 'completed' CHECK(status IN ('pending', 'completed', 'failed')),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(counterparty_id) REFERENCES users(id) ON DELETE SET NULL
            )
        ''')

        # Create indexes for better performance
        conn.execute('CREATE INDEX IF NOT EXISTS idx_user_email ON users(email)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_user_email ON users(email)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user ON transactions(user_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_transactions_timestamp ON transactions(timestamp)')

def get_transaction_history(user_id, limit=100):
    """Fetches transaction history with pagination support."""
    with get_db_connection() as conn:
        return conn.execute(''' 
            SELECT t.*, 
                   u1.email AS user_email,
                   u2.email AS counterparty_email
            FROM transactions t
            LEFT JOIN users u1 ON t.user_id = u1.id
            LEFT JOIN users u2 ON t.counterparty_id = u2.id
            WHERE t.user_id = ? OR t.counterparty_id = ?
            ORDER BY t.timestamp DESC
            LIMIT ?
        ''', (user_id, user_id, limit)).fetchall()

def get_balance(user_id):
    """Fetches the current balance with account verification."""
    with get_db_connection() as conn:
        account = conn.execute(''' 
            SELECT balance FROM users 
            WHERE id = ? AND is_active = 1
        ''', (user_id,)).fetchone()
        return account['balance'] if account else 0.0

def update_balance(user_id, amount):
    """Atomically updates user balance with transaction recording."""
    with get_db_connection() as conn:
        try:
            conn.execute("BEGIN TRANSACTION")
            
            # Update balance
            conn.execute(''' 
                UPDATE users 
                SET balance = balance + ? 
                WHERE id = ? AND is_active = 1
            ''', (amount, user_id))
            
            # Verify update was successful
            if conn.total_changes == 0:
                conn.execute("ROLLBACK")
                return False
            
            conn.execute("COMMIT")
            return True
            
        except sqlite3.Error:
            conn.execute("ROLLBACK")
            return False

def create_test_data():
    """Populates the database with test data for development."""
    from werkzeug.security import generate_password_hash
    
    with get_db_connection() as conn:
        # Create test users
        users = [
            ('user1@example.com', generate_password_hash('password123'), 1000.0),
            ('user2@example.com', generate_password_hash('password123'), 500.0),
            ('admin@instapay.com', generate_password_hash('secureadmin'), 10000.0)
        ]
        
        conn.executemany(''' 
            INSERT INTO users (email, password, balance)
            VALUES (?, ?, ?)
        ''', users)
        
        # Create sample transactions
        transactions = [
            (1, 'deposit', 500.0, None, 'Initial deposit'),
            (2, 'deposit', 300.0, None, 'Account funding'),
            (1, 'transfer', 200.0, 2, 'Money transfer to user2'),
            (2, 'withdrawal', 100.0, None, 'ATM withdrawal')
        ]
        
        conn.executemany(''' 
            INSERT INTO transactions (user_id, type, amount, counterparty_id, description)
            VALUES (?, ?, ?, ?, ?)
        ''', transactions)
def get_user_by_email():
    """Fetches a user by their email."""
    email = request.args.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400

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
        })
if __name__ == "__main__":
    # Initialize database and optionally create test data
    init_db()
    
    # Uncomment for development/testing
    # create_test_data()
    print("Database initialized successfully")
