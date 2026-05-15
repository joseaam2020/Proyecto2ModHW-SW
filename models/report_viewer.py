"""
report_viewer.py
----------------
Visualiza de manera clara y concisa los reportes individuales por tick.

Modos:
    * resumen        -> imprime una tabla en consola con el estado de cada proceso
                        en un tick específico (o varios).
    * timeline       -> imprime una línea de tiempo con el progreso de los productos.
    * tick           -> vista detallada de un tick (todos los procesos, tareas, colas).
"""

from __future__ import annotations

import json
import os
import re
from typing import List, Optional


REPORT_RE = re.compile(r"report_tick_(\d+)\.json$")


# ---------------------------------------------------------------------------
# Utilidades de presentación en consola
# ---------------------------------------------------------------------------
def _color(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def _state_badge(state: str) -> str:
    return {
        "P": _color(" P ", "1;42;97"),   # verde
        "Q": _color(" Q ", "1;43;30"),   # amarillo
        "NP": _color("NP ", "1;100;97"), # gris
        "D": _color(" D ", "1;44;97"),   # azul
    }.get(state, f" {state} ")


def _h_rule(width: int = 80, ch: str = "─") -> str:
    return ch * width


# ---------------------------------------------------------------------------
# Carga de reportes
# ---------------------------------------------------------------------------
def list_tick_files(reports_dir: str) -> List[int]:
    if not os.path.isdir(reports_dir):
        raise FileNotFoundError(reports_dir)
    ticks = []
    for name in os.listdir(reports_dir):
        m = REPORT_RE.match(name)
        if m:
            ticks.append(int(m.group(1)))
    return sorted(ticks)


def load_tick(reports_dir: str, tick: int) -> List[dict]:
    path = os.path.join(reports_dir, f"report_tick_{tick:03d}.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


# ---------------------------------------------------------------------------
# Vistas
# ---------------------------------------------------------------------------
def view_tick(reports_dir: str, tick: int) -> None:
    """Imprime una vista detallada del tick indicado."""
    snapshots = load_tick(reports_dir, tick)
    print(_h_rule())
    print(f" TICK {tick:>3}  -  {len(snapshots)} procesos".center(80))
    print(_h_rule())

    for snap in snapshots:
        pid = snap["process_id"]
        print(f"\n● Proceso {pid}")
        # productos
        if snap["products"]:
            states = " ".join(
                f"{p['product_id']}{_state_badge(p['state'])}"
                for p in snap["products"]
            )
            print(f"   Productos: {states}")
        else:
            print(f"   Productos: {_color('(ninguno)', '2')}")

        # tareas
        for t in snap["tasks"]:
            qlen = len(t["queue_product_ids"])
            in_proc = t["product_in_process_id"]
            state = _state_badge(t["state"])
            bar = _color("█" * min(qlen, 20), "33") if qlen else ""
            print(
                f"   ├─ Tarea {t['task_id']} [{state}] "
                f"t={t['task_time']:>2}  "
                f"cola={qlen:>2} {bar}  "
                f"procesando={in_proc if in_proc is not None else '—':<3} "
                f"prog={t['current_time']}/{t['task_time']}"
            )
    print()


def view_summary(reports_dir: str, ticks: Optional[List[int]] = None) -> None:
    """Tabla compacta con una fila por tick."""
    all_ticks = list_tick_files(reports_dir)
    if ticks is None:
        ticks = all_ticks
    else:
        ticks = [t for t in ticks if t in all_ticks]

    if not ticks:
        print("No hay ticks para mostrar.")
        return

    # determinar el número de procesos a partir del primer reporte
    first = load_tick(reports_dir, ticks[0])
    proc_ids = sorted({s["process_id"] for s in first})

    # encabezado
    header = f"{'TICK':>5} │ " + " │ ".join(
        f"P{pid} ({'colas / proc / done'})" for pid in proc_ids
    )
    print(header)
    print(_h_rule(len(header)))

    for tick in ticks:
        snaps = {s["process_id"]: s for s in load_tick(reports_dir, tick)}
        cells = []
        for pid in proc_ids:
            snap = snaps.get(pid)
            if not snap:
                cells.append("—".center(20))
                continue
            queues = sum(len(t["queue_product_ids"]) for t in snap["tasks"])
            processing = sum(1 for t in snap["tasks"] if t["state"] == "P")
            done = sum(1 for p in snap["products"] if p["state"] == "D")
            cells.append(f"{queues:>3} /{processing:>3} /{done:>3}".center(20))
        print(f"{tick:>5} │ " + " │ ".join(cells))


def view_timeline(reports_dir: str) -> None:
    """Línea de tiempo: una fila por producto mostrando su recorrido."""
    all_ticks = list_tick_files(reports_dir)
    if not all_ticks:
        print("No hay ticks.")
        return

    # encontrar todos los product_ids
    product_ids = set()
    for tick in all_ticks:
        for snap in load_tick(reports_dir, tick):
            for p in snap["products"]:
                product_ids.add(p["product_id"])

    last_pid = max(
        s["process_id"]
        for s in load_tick(reports_dir, all_ticks[0])
    )

    print(f"\nLeyenda: {_state_badge('Q')}cola  {_state_badge('P')}procesando  "
          f"{_state_badge('D')}done\n")

    header = f"{'PROD':>4} │ " + "".join(
        str(t % 10) for t in all_ticks
    )
    print(header)
    print(_h_rule(len(header)))

    for pid in sorted(product_ids):
        row = [f"{pid:>4} │ "]
        for tick in all_ticks:
            found_state = None
            found_pid = None
            for snap in load_tick(reports_dir, tick):
                for p in snap["products"]:
                    if p["product_id"] == pid:
                        found_state = p["state"]
                        found_pid = snap["process_id"]
                        break
                if found_state:
                    break
            if found_state is None:
                row.append(" ")
            elif found_state == "D" and found_pid == last_pid:
                row.append(_color("■", "1;34"))
            elif found_state == "D":
                row.append(_color("▣", "34"))
            elif found_state == "P":
                row.append(_color("▶", "1;32"))
            else:
                row.append(_color("·", "33"))
        print("".join(row))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Visualiza los reportes generados por la simulación."
    )
    parser.add_argument("--reports-dir", default="reports")
    sub = parser.add_subparsers(dest="cmd")

    p_tick = sub.add_parser("tick", help="Vista detallada de un tick")
    p_tick.add_argument("tick", type=int)

    sub.add_parser("summary", help="Tabla compacta de todos los ticks")
    sub.add_parser("timeline", help="Línea de tiempo por producto")

    args = parser.parse_args()
    if args.cmd == "tick":
        view_tick(args.reports_dir, args.tick)
    elif args.cmd == "summary":
        view_summary(args.reports_dir)
    elif args.cmd == "timeline":
        view_timeline(args.reports_dir)
    else:
        parser.print_help()