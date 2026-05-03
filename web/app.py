# web/app.py
from flask import Flask, render_template, send_from_directory
from flask import request, redirect, url_for
from models.pipeline_builder import PipelineBuilder

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

@app.route('/simulate', methods=['POST'])
def simulate():
    # Parse number of products and processes/tasks from the form
    num_products = int(request.form['num_products'])
    # Parse process/task structure
    processes_data = []
    i = 1
    while True:
        task_times = request.form.getlist(f'processes[{i}][tasks][]')
        if not task_times:
            break
        processes_data.append({"tasks": [int(t) for t in task_times]})
        i += 1

    # Prepare product data (IDs 1..num_products)
    products_data = list(range(1, num_products + 1))

    # Build pipeline
    builder = PipelineBuilder(processes_data, products_data)
    processes = builder.build()

    # Run simulation for a fixed number of ticks (e.g., 10)
    NUM_TICKS = 10
    for tick in range(1, NUM_TICKS + 1):
        for process in processes:
            process.tick()
            report = process.generate_report()
            process.save_report(report, tick)  # Save report for each process/tick if desired

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)