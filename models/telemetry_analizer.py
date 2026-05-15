"""
telemetry_analyzer.py
---------------------
Analiza los reportes JSON generados por la simulación tick a tick y produce
un conjunto de estadísticas agregadas sobre toda la línea de producción.

Los reportes tienen la forma:

    [
        {
            "process_id": int,
            "products": [ {product_id, state, pid, tid}, ... ],
            "tasks":    [ {task_id, task_time, queue_product_ids,
                           state, product_in_process_id, current_time}, ... ]
        },
        ...
    ]

Cada archivo `report_tick_XXX.json` representa el estado del sistema en un tick.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Estructuras de datos
# ---------------------------------------------------------------------------

@dataclass
class ProductTimeline:
    """Línea de tiempo de un producto a lo largo de la simulación."""
    product_id: int
    first_seen_tick: Optional[int] = None
    finish_tick: Optional[int] = None          # tick en el que terminó toda la línea
    ticks_queued: int = 0                      # ticks totales en estado 'Q'
    ticks_processing: int = 0                  # ticks totales en estado 'P'
    ticks_done: int = 0                        # ticks en estado 'D' (incluye estancia final)
    # detalle de espera por (process_id, task_id)
    wait_by_task: Dict[Tuple[int, int], int] = field(default_factory=lambda: defaultdict(int))


@dataclass
class TaskStats:
    """Estadísticas agregadas de una tarea concreta dentro de un proceso."""
    process_id: int
    task_id: int
    task_time: int
    total_queue_length: int = 0     # suma de longitudes de cola a lo largo de los ticks
    max_queue_length: int = 0
    ticks_observed: int = 0
    ticks_processing: int = 0       # ticks en estado 'P'
    ticks_idle: int = 0             # ticks en estado 'NP'
    total_wait_time: int = 0        # suma de espera de todos los productos en esta tarea

    @property
    def avg_queue_length(self) -> float:
        return self.total_queue_length / self.ticks_observed if self.ticks_observed else 0.0

    @property
    def utilization(self) -> float:
        return self.ticks_processing / self.ticks_observed if self.ticks_observed else 0.0


@dataclass
class ProcessStats:
    """Estadísticas agregadas de un proceso completo."""
    process_id: int
    tasks: Dict[int, TaskStats] = field(default_factory=dict)
    total_queue_across_tasks: int = 0   # suma de colas de todas las tareas en cada tick
    ticks_observed: int = 0

    @property
    def avg_total_queue(self) -> float:
        return self.total_queue_across_tasks / self.ticks_observed if self.ticks_observed else 0.0


# ---------------------------------------------------------------------------
# Analizador principal
# ---------------------------------------------------------------------------

class TelemetryAnalyzer:
    """Recorre los reportes y produce estadísticas agregadas."""

    REPORT_RE = re.compile(r"report_tick_(\d+)\.json$")

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = reports_dir
        # tick -> lista de snapshots (uno por proceso)
        self.snapshots_by_tick: Dict[int, List[dict]] = {}
        # ID del último proceso (lo último de la línea = producto terminado)
        self.last_process_id: Optional[int] = None
        # acumuladores
        self.products: Dict[int, ProductTimeline] = {}
        self.processes: Dict[int, ProcessStats] = {}
        self.total_ticks: int = 0

    # -----------------------------------------------------------------
    # Carga
    # -----------------------------------------------------------------
    def load(self) -> None:
        """Carga todos los archivos report_tick_*.json de la carpeta."""
        if not os.path.isdir(self.reports_dir):
            raise FileNotFoundError(
                f"No existe la carpeta de reportes: {self.reports_dir}"
            )

        files = []
        for name in os.listdir(self.reports_dir):
            m = self.REPORT_RE.match(name)
            if m:
                files.append((int(m.group(1)), name))

        if not files:
            raise RuntimeError(
                f"No se encontraron reportes con formato report_tick_NNN.json en "
                f"{self.reports_dir}"
            )

        files.sort(key=lambda t: t[0])

        for tick, name in files:
            path = os.path.join(self.reports_dir, name)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # El formato puede ser una lista de snapshots o un único dict.
            if isinstance(data, dict):
                data = [data]
            self.snapshots_by_tick[tick] = data

        self.total_ticks = max(self.snapshots_by_tick.keys())
        # asumimos que el último process_id es el final de la línea
        first_tick = min(self.snapshots_by_tick.keys())
        process_ids = [snap["process_id"] for snap in self.snapshots_by_tick[first_tick]]
        self.last_process_id = max(process_ids) if process_ids else None

    # -----------------------------------------------------------------
    # Análisis
    # -----------------------------------------------------------------
    def analyze(self) -> None:
        """Recorre los snapshots tick por tick y rellena las estadísticas."""
        # Para detectar la finalización de un producto comparamos su estado
        # entre dos ticks consecutivos en el último proceso.
        prev_states_in_last_process: Dict[int, str] = {}

        for tick in sorted(self.snapshots_by_tick.keys()):
            snapshots = self.snapshots_by_tick[tick]

            current_states_in_last_process: Dict[int, str] = {}

            for snap in snapshots:
                pid = snap["process_id"]
                pstats = self.processes.setdefault(pid, ProcessStats(process_id=pid))
                pstats.ticks_observed += 1

                queue_sum_this_tick = 0

                # --- tareas ---
                for tdata in snap["tasks"]:
                    tid = tdata["task_id"]
                    tstats = pstats.tasks.setdefault(
                        tid,
                        TaskStats(
                            process_id=pid,
                            task_id=tid,
                            task_time=tdata["task_time"],
                        ),
                    )
                    qlen = len(tdata["queue_product_ids"])
                    tstats.total_queue_length += qlen
                    tstats.max_queue_length = max(tstats.max_queue_length, qlen)
                    tstats.ticks_observed += 1
                    if tdata["state"] == "P":
                        tstats.ticks_processing += 1
                    else:
                        tstats.ticks_idle += 1
                    queue_sum_this_tick += qlen

                    # cada producto en cola en este task espera un tick más
                    for product_id in tdata["queue_product_ids"]:
                        ptl = self.products.setdefault(
                            product_id, ProductTimeline(product_id=product_id)
                        )
                        ptl.wait_by_task[(pid, tid)] += 1
                        tstats.total_wait_time += 1

                pstats.total_queue_across_tasks += queue_sum_this_tick

                # --- productos ---
                for prod in snap["products"]:
                    pidp = prod["product_id"]
                    ptl = self.products.setdefault(
                        pidp, ProductTimeline(product_id=pidp)
                    )
                    if ptl.first_seen_tick is None:
                        ptl.first_seen_tick = tick

                    state = prod["state"]
                    if state == "Q":
                        ptl.ticks_queued += 1
                    elif state == "P":
                        ptl.ticks_processing += 1
                    elif state == "D":
                        ptl.ticks_done += 1

                    if pid == self.last_process_id:
                        current_states_in_last_process[pidp] = state

            # Detectar finalización: producto pasa a 'D' en el último proceso.
            for pidp, state in current_states_in_last_process.items():
                prev = prev_states_in_last_process.get(pidp)
                if state == "D" and prev != "D":
                    ptl = self.products[pidp]
                    if ptl.finish_tick is None:
                        ptl.finish_tick = tick

            prev_states_in_last_process = current_states_in_last_process

    # -----------------------------------------------------------------
    # Estadísticas agregadas
    # -----------------------------------------------------------------
    def summary(self) -> dict:
        finished = [p for p in self.products.values() if p.finish_tick is not None]
        all_products = list(self.products.values())

        first_finish = min((p.finish_tick for p in finished), default=None)
        last_finish = max((p.finish_tick for p in finished), default=None)
        avg_finish = (
            sum(p.finish_tick for p in finished) / len(finished)
            if finished else None
        )

        # Lead time por producto (desde que entró hasta que terminó)
        lead_times = [
            p.finish_tick - p.first_seen_tick + 1
            for p in finished
            if p.first_seen_tick is not None
        ]
        avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else None
        min_lead_time = min(lead_times, default=None)
        max_lead_time = max(lead_times, default=None)

        # Cuello de botella por proceso (mayor cola promedio total)
        bottleneck_process = None
        if self.processes:
            bottleneck_process = max(
                self.processes.values(), key=lambda p: p.avg_total_queue
            )

        # Cuello de botella por tarea (mayor tiempo total de espera)
        bottleneck_task = None
        all_tasks: List[TaskStats] = [
            t for p in self.processes.values() for t in p.tasks.values()
        ]
        if all_tasks:
            bottleneck_task = max(all_tasks, key=lambda t: t.total_wait_time)

        # Tiempo promedio de espera por producto (en ticks 'Q')
        avg_wait_per_product = (
            sum(p.ticks_queued for p in all_products) / len(all_products)
            if all_products else 0.0
        )

        # Tiempo total de procesamiento de todos los productos (suma de ticks 'P')
        total_processing_ticks = sum(p.ticks_processing for p in all_products)

        # Throughput (productos terminados / ticks totales)
        throughput = (
            len(finished) / self.total_ticks if self.total_ticks else 0.0
        )

        return {
            "total_ticks": self.total_ticks,
            "total_products": len(all_products),
            "products_finished": len(finished),
            "products_unfinished": len(all_products) - len(finished),
            "first_finish_tick": first_finish,
            "last_finish_tick": last_finish,
            "avg_finish_tick": avg_finish,
            "avg_lead_time": avg_lead_time,
            "min_lead_time": min_lead_time,
            "max_lead_time": max_lead_time,
            "avg_wait_per_product": avg_wait_per_product,
            "total_processing_ticks": total_processing_ticks,
            "throughput": throughput,
            "bottleneck_process": bottleneck_process,
            "bottleneck_task": bottleneck_task,
            "processes": self.processes,
            "products": self.products,
            "last_process_id": self.last_process_id,
        }