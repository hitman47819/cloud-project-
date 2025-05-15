import sys
import os
# ensure parent directory is on path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.db_config import get_db_connection, get_balance as db_get_balance

class TransactionManager:
    """Handles send, deposit, and receive operations using SQLite backend."""

    def get_balance(self, user_id: int) -> float:
        """Return the current balance for the given user."""
        return db_get_balance(user_id)

    def send(self, sender_id: int, receiver_id: int, amount: float) -> bool:
        """Transfer amount from sender to receiver if funds are sufficient."""
        if amount <= 0:
            return False
        with get_db_connection() as conn:
            try:
                conn.execute("BEGIN TRANSACTION")
                # Check sender
                row = conn.execute(
                    "SELECT balance FROM users WHERE id = ? AND is_active = 1", (sender_id,)
                ).fetchone()
                if not row or row["balance"] < amount:
                    conn.execute("ROLLBACK")
                    return False
                # Deduct
                conn.execute("UPDATE users SET balance = balance - ? WHERE id = ?", (amount, sender_id))
                # Credit
                conn.execute("UPDATE users SET balance = balance + ? WHERE id = ? AND is_active = 1", (amount, receiver_id))
                # Log
                conn.execute(
                    "INSERT INTO transactions (user_id, type, amount, counterparty_id, description) VALUES (?, 'transfer', ?, ?, ?)",
                    (sender_id, amount, receiver_id, f"Transfer to user {receiver_id}")
                )
                conn.execute("COMMIT")
                return True
            except Exception:
                conn.execute("ROLLBACK")
                return False

    def deposit(self, user_id: int, amount: float) -> bool:
     """Deposit the given amount into the user's account."""
     if amount <= 0:
         return False
     with get_db_connection() as conn:
         try:
             conn.execute("BEGIN TRANSACTION")
            # Check user
             row = conn.execute(
                 "SELECT balance FROM users WHERE id = ? AND is_active = 1", (user_id,)
             ).fetchone()
             if not row:
                 conn.execute("ROLLBACK")
                 print(f"User with ID {user_id} not found or is inactive.")  # Debugging
                 return False
              # Update balance
             conn.execute("UPDATE users SET balance = balance + ? WHERE id = ?", (amount, user_id))
             # Log deposit
             conn.execute(
                 "INSERT INTO transactions (user_id, type, amount, counterparty_id, description) VALUES (?, 'deposit', ?, NULL, ?)",
                 (user_id, amount, "Deposit funds")
             )
             conn.execute("COMMIT")
             return True
         except Exception as e:
            conn.execute("ROLLBACK")
            print(f"Error during deposit: {e}")  # Debugging
            return False


    def get_received_transactions(self, user_id: int) -> list:
        """Return list of transactions where this user is the receiver."""
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT id, user_id AS sender_id, amount, timestamp FROM transactions WHERE counterparty_id = ? AND type = 'transfer' ORDER BY timestamp DESC", (user_id,)
            ).fetchall()
            return [
                {'id': r['id'], 'sender_id': r['sender_id'], 'amount': float(r['amount']), 'date': r['timestamp']}
                for r in rows
            ]
