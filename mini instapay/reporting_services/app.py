from flask import Flask, jsonify
from report_generator import ReportGenerator

app = Flask(__name__)

@app.route('/generate_report/<int:user_id>', methods=['GET'])
def generate_report(user_id):
    report_generator = ReportGenerator()
    report = report_generator.generate_report(user_id)
    return jsonify(report)

if __name__ == '__main__':
    app.run(debug=True, port=5003)
