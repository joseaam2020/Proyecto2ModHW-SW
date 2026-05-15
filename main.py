import sys
import os

# Asegura que Python encuentre los módulos del proyecto y de telemetría
sys.path.insert(0, os.path.dirname(__file__))

from models.process import Process
from models.task import Task
from models.product import Product
from models.report_generator import generate_pdf


if __name__ == "__main__":

    # ------------------------------------------------------------------
    # 1. Construcción del proceso
    # ------------------------------------------------------------------
    process = Process(id=1)

    task1 = Task(id=1, task_time=1)
    task2 = Task(id=2, task_time=1)

    task1.set_next_task(task2)
    process.add_task(task1)
    process.add_task(task2)

    products = [Product(id=i + 1) for i in range(5)]
    for product in products:
        process.add_product(product)

    # El proceso único actúa como primero y último de la línea
    process.is_first = True
    process.is_last  = True

    process.setup()

    # ------------------------------------------------------------------
    # 2. Simulación tick a tick
    # ------------------------------------------------------------------
    REPORTS_DIR = "reports"
    NUM_TICKS   = 8

    for tick in range(1, NUM_TICKS + 1):
        print(f"\nTick {tick}")
        process.tick()
        report = process.generate_report()
        process.save_report(tick)   # guarda en reports/report_tick_NNN.json
        print(report)

    # ------------------------------------------------------------------
    # 3. Reporte general (PDF + resumen en consola)
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("Generando informe general de telemetría...")
    print("=" * 60)

    
    pdf_path = generate_pdf(
        reports_dir=REPORTS_DIR,
        output_path="informe_general.pdf",
    )
    print(f"✓ PDF generado: {pdf_path}")