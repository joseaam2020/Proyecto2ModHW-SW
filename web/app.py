# web/app.py
from flask import Flask, render_template, send_from_directory
import os
import json

app = Flask(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')

@app.route('/')
def index():
    # List all report files
    reports = sorted(f for f in os.listdir(REPORTS_DIR) if f.endswith('.json'))
    return render_template('index.html', reports=reports)

@app.route('/report/<filename>')
def report(filename):
    # Show a specific report
    with open(os.path.join(REPORTS_DIR, filename)) as f:
        report = json.load(f)
    return render_template('report.html', report=report, filename=filename)

if __name__ == '__main__':
    app.run(debug=True)