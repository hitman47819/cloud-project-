import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import bcrypt
from common.db_config import get_db_connection

class UserManager:
    def __init__(self):
        self.initialize_db()

    @staticmethod
    def initialize_db():
        # Initialize the DB by creating necessary tables (if not already created)
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    balance REAL DEFAULT 0.0  -- Add balance column
                )
            ''')
            conn.commit()  # Commit the changes to the database

    def user_exists(self, email):
        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            return user is not None

    def create_user(self, email, password, initial_balance=0.0):
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')  # Hash the password
        with get_db_connection() as conn:
            conn.execute('INSERT INTO users (email, password, balance) VALUES (?, ?, ?)', 
                         (email, hashed, initial_balance))
            conn.commit()  # Commit the changes to the database

    def authenticate_user(self, email, password):
        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            if not user:
                return False  # No user found with the given email
            
            stored_password = user['password'].encode('utf-8')
            return bcrypt.checkpw(password.encode('utf-8'), stored_password)  # Check the password

    def get_user_id(self, email):
        with get_db_connection() as conn:
            user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            return user['id'] if user else None  # Return the user ID if found

    def get_user_balance(self, user_id):
        with get_db_connection() as conn:
            user = conn.execute('SELECT balance FROM users WHERE id = ?', (user_id,)).fetchone()
            return user['balance'] if user else None  # Return the balance if found

    def update_user_balance(self, user_id, new_balance):
        with get_db_connection() as conn:
            conn.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user_id))
            conn.commit()
