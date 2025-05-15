class ReportGenerator:
    def __init__(self):
        self.transactions = {}

    def generate_report(self, user_id):
        user_transactions = [t for t in self.transactions if t['sender_id'] == user_id or t['receiver_id'] == user_id]
        report = {
            'user_id': user_id,
            'total_transactions': len(user_transactions),
            'total_balance': sum(t['amount'] for t in user_transactions)
        }
        return report
