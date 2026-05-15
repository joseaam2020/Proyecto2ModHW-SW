# web/app.py
import sys
import os
import json

# Agrega la raíz del proyecto al path para encontrar report_generator
# y telemetry_analyzer, que viven un nivel arriba de web/
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from flask import (
    Flask, render_template, send_from_directory, abort,
    request, redirect, url_for, send_file, jsonify,
)
from typing import List
from models.pipeline_builder import PipelineBuilder
from models.process import Process
from models.report_generator import generate_pdf

# Forzar rutas absolutas para templates y static
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(_BASE_DIR, 'templates'),
    static_folder=os.path.join(_BASE_DIR, 'static')
)

REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports'))
PDF_PATH    = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'informe_general.pdf'))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _list_report_files():
    """Devuelve la lista ordenada de archivos report_tick_*.json."""
    if not os.path.isdir(REPORTS_DIR):
        return []
    return sorted(
        f for f in os.listdir(REPORTS_DIR)
        if f.startswith('report_tick_') and f.endswith('.json')
    )


# ---------------------------------------------------------------------------
# Rutas del simulador (existentes)
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    reports = _list_report_files()
    pdf_ready = os.path.isfile(PDF_PATH)
    return render_template('index.html', reports=reports, pdf_ready=pdf_ready)


@app.route('/report/<filename>')
def report(filename):
    file_path = os.path.join(REPORTS_DIR, filename)
    if not os.path.isfile(file_path):
        abort(404)
    if filename.endswith('.json'):
        return send_from_directory(REPORTS_DIR, filename, mimetype='application/json')
    with open(file_path) as f:
        report_data = json.load(f)
    return render_template('report.html', report=report_data, filename=filename)


@app.route('/simulate', methods=['POST'])
def simulate():
    num_products = int(request.form['num_products'])

    processes_data = []
    i = 1
    while True:
        task_times = request.form.getlist(f'processes[{i}][tasks][]')
        if not task_times:
            break
        processes_data.append({"tasks": [int(t) for t in task_times]})
        i += 1

    if not processes_data:
        return redirect(url_for('index'))

    products_data = list(range(1, num_products + 1))

    builder = PipelineBuilder(processes_data, products_data)
    processes: List[Process] = builder.build()

    # Limpiar reportes anteriores y el PDF previo
    os.makedirs(REPORTS_DIR, exist_ok=True)
    for fname in os.listdir(REPORTS_DIR):
        fpath = os.path.join(REPORTS_DIR, fname)
        if os.path.isfile(fpath):
            os.remove(fpath)
    if os.path.isfile(PDF_PATH):
        os.remove(PDF_PATH)

    tick = 1
    while True:
        for process in processes:
            process.tick()
            process.save_report(tick)

        last_process = next(p for p in processes if p.is_last)
        if (len(last_process.products) == len(builder.products)
                and all(product.state == 'D' for product in last_process.products)):
            break
        tick += 1

    return redirect(url_for('index'))


# ---------------------------------------------------------------------------
# Rutas de la página de reportes
# ---------------------------------------------------------------------------
@app.route('/reportes')
def reportes_page():
    """Renderiza la página de reportes (HTML)."""
    return render_template('reports.html')


@app.route('/api/reports')
def api_reports_list():
    """Devuelve la lista de reportes individuales en JSON."""
    files = _list_report_files()
    items = []
    for fname in files:
        # report_tick_001.json -> tick 1
        try:
            tick_num = int(fname.replace('report_tick_', '').replace('.json', ''))
        except ValueError:
            tick_num = None
        items.append({
            'filename': fname,
            'tick': tick_num,
            'url': url_for('report', filename=fname),
        })
    return jsonify({'count': len(items), 'reports': items})


@app.route('/informe', methods=['POST', 'GET'])
def informe():
    """Genera el PDF y lo devuelve.
       ?inline=1 → visualizar en iframe (no se fuerza descarga).
       Sin parámetro o inline=0 → descarga forzada.
       Acepta GET para que un iframe pueda cargarlo como URL."""
    if not _list_report_files():
        if request.method == 'POST':
            return redirect(url_for('reportes_page', error='no_reports'))
        abort(404)

    try:
        generate_pdf(reports_dir=REPORTS_DIR, output_path=PDF_PATH)
    except Exception as e:
        app.logger.error(f"Error generando informe: {e}")
        if request.method == 'POST':
            return redirect(url_for('reportes_page', error='pdf_error'))
        abort(500)

    inline = request.args.get('inline') == '1'
    return send_file(
        PDF_PATH,
        mimetype='application/pdf',
        as_attachment=not inline,
        download_name='informe_general.pdf',
    )


if __name__ == '__main__':
    app.run(debug=True)