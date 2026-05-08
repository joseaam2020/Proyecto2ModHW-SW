# web/app.py
from flask import Flask, render_template, send_from_directory
from flask import request, redirect, url_for
from typing import List
from models.pipeline_builder import PipelineBuilder
from models.process import Process

import os
import json


app = Flask(__name__)

REPORTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'reports')

@app.route('/')
def index():
    # List all report files
    os.makedirs(REPORTS_DIR, exist_ok=True)
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
    processes : List[Process] = builder.build()

    #Deletes all files in the reports directory before a new simulation.
    reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
    reports_dir = os.path.abspath(reports_dir)
    if os.path.exists(reports_dir):
        for filename in os.listdir(reports_dir):
            file_path = os.path.join(reports_dir, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
    else:
        os.makedirs(reports_dir, exist_ok=True)

    tick = 1
    while True:
        for process in processes:
            process.tick()
            process.save_report(tick)
        # Check if all products in the last process are done
        last_process = next(p for p in processes if p.is_last)
        if last_process.products and all(product.state == 'D' for product in last_process.products):
            break
        tick += 1

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)