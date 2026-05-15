"""
report_generator.py
-------------------
Genera un PDF general con las estadísticas de la simulación.

Usa ReportLab (Platypus) para producir un informe estructurado en secciones:
    1. Portada / resumen ejecutivo
    2. Métricas globales de la línea de producción
    3. Análisis por proceso (cuello de botella, colas, utilización)
    4. Análisis por tarea (espera, ocupación)
    5. Detalle por producto
"""

from __future__ import annotations

from typing import Optional
import datetime as _dt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)

from models.telemetry_analizer import TelemetryAnalyzer


# -- paleta ----------------------------------------------------------------
PRIMARY = colors.HexColor("#1F3A5F")
ACCENT = colors.HexColor("#3D7EA6")
LIGHT = colors.HexColor("#EAF1F8")
WARN = colors.HexColor("#C0392B")
MUTED = colors.HexColor("#6B7280")


def _styles():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(
        name="ReportTitle", parent=base["Title"],
        fontSize=22, textColor=PRIMARY, spaceAfter=6, alignment=1,
    ))
    base.add(ParagraphStyle(
        name="ReportSubtitle", parent=base["Normal"],
        fontSize=11, textColor=MUTED, alignment=1, spaceAfter=18,
    ))
    base.add(ParagraphStyle(
        name="Section", parent=base["Heading1"],
        fontSize=14, textColor=PRIMARY, spaceBefore=14, spaceAfter=8,
    ))
    base.add(ParagraphStyle(
        name="Sub", parent=base["Heading2"],
        fontSize=11, textColor=ACCENT, spaceBefore=8, spaceAfter=4,
    ))
    base.add(ParagraphStyle(
        name="Body", parent=base["Normal"], fontSize=10, leading=14,
    ))
    base.add(ParagraphStyle(
        name="Callout", parent=base["Normal"], fontSize=10, leading=14,
        textColor=PRIMARY, backColor=LIGHT, borderPadding=8, leftIndent=4,
    ))
    return base


def _fmt(value, suffix: str = "", n: int = 2) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:.{n}f}{suffix}"
    return f"{value}{suffix}"


# ---------------------------------------------------------------------------
# Construcción de las secciones
# ---------------------------------------------------------------------------

def _exec_summary(summary, styles):
    story = []
    story.append(Paragraph("Resumen Ejecutivo", styles["Section"]))

    finished = summary["products_finished"]
    total = summary["total_products"]
    bp = summary["bottleneck_process"]
    bt = summary["bottleneck_task"]

    bp_label = f"Proceso {bp.process_id}" if bp else "—"
    bt_label = (
        f"Proceso {bt.process_id} · Tarea {bt.task_id}"
        if bt else "—"
    )

    text = (
        f"La simulación se ejecutó durante <b>{summary['total_ticks']} ticks</b>, "
        f"procesando <b>{total} productos</b>, de los cuales "
        f"<b>{finished}</b> completaron la línea de producción "
        f"({(finished/total*100 if total else 0):.1f}%). "
        f"El primer producto terminó en el tick "
        f"<b>{_fmt(summary['first_finish_tick'])}</b>, mientras que el último lo hizo "
        f"en el tick <b>{_fmt(summary['last_finish_tick'])}</b>. "
        f"El cuello de botella principal se identificó en <b>{bp_label}</b>, "
        f"y la tarea con mayor tiempo total de espera fue <b>{bt_label}</b>."
    )
    story.append(Paragraph(text, styles["Callout"]))
    story.append(Spacer(1, 6))
    return story


def _global_metrics(summary, styles):
    story = []
    story.append(Paragraph("Métricas globales", styles["Section"]))

    rows = [
        ["Métrica", "Valor"],
        ["Total de ticks simulados", _fmt(summary["total_ticks"])],
        ["Productos totales", _fmt(summary["total_products"])],
        ["Productos finalizados", _fmt(summary["products_finished"])],
        ["Productos sin finalizar", _fmt(summary["products_unfinished"])],
        ["Tick del primer producto terminado", _fmt(summary["first_finish_tick"])],
        ["Tick del último producto terminado", _fmt(summary["last_finish_tick"])],
        ["Tick promedio de finalización", _fmt(summary["avg_finish_tick"])],
        ["Lead time promedio (ticks)", _fmt(summary["avg_lead_time"])],
        ["Lead time mínimo / máximo",
         f"{_fmt(summary['min_lead_time'])} / {_fmt(summary['max_lead_time'])}"],
        ["Espera promedio por producto (ticks en cola)",
         _fmt(summary["avg_wait_per_product"])],
        ["Tiempo total de procesamiento (suma ticks 'P')",
         _fmt(summary["total_processing_ticks"])],
        ["Throughput (productos / tick)", _fmt(summary["throughput"], n=4)],
    ]

    table = Table(rows, colWidths=[9.5*cm, 6.5*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D0D7DE")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    return story


def _bottleneck_section(summary, styles):
    story = []
    story.append(Paragraph("Cuellos de botella", styles["Section"]))

    bp = summary["bottleneck_process"]
    bt = summary["bottleneck_task"]

    if bp:
        story.append(Paragraph(
            f"<b>Proceso con mayor congestionamiento:</b> Proceso {bp.process_id}",
            styles["Body"],
        ))
        story.append(Paragraph(
            f"Cola promedio (suma de todas sus tareas): "
            f"<b>{bp.avg_total_queue:.2f}</b> productos por tick.",
            styles["Body"],
        ))

    if bt:
        story.append(Spacer(1, 4))
        story.append(Paragraph(
            f"<b>Tarea con mayor tiempo de espera:</b> "
            f"Proceso {bt.process_id}, Tarea {bt.task_id}",
            styles["Body"],
        ))
        story.append(Paragraph(
            f"Tiempo total de espera acumulado: "
            f"<b>{bt.total_wait_time}</b> ticks · "
            f"Cola promedio: <b>{bt.avg_queue_length:.2f}</b> · "
            f"Cola máxima: <b>{bt.max_queue_length}</b>.",
            styles["Body"],
        ))

    return story


def _process_breakdown(summary, styles):
    story = []
    story.append(Paragraph("Detalle por proceso", styles["Section"]))

    rows = [["Proceso", "Cola prom.", "Cola máx.", "Utiliz. prom.", "Espera total"]]
    for pid in sorted(summary["processes"].keys()):
        pstats = summary["processes"][pid]
        max_q = max((t.max_queue_length for t in pstats.tasks.values()), default=0)
        util = (
            sum(t.utilization for t in pstats.tasks.values()) / len(pstats.tasks)
            if pstats.tasks else 0.0
        )
        wait = sum(t.total_wait_time for t in pstats.tasks.values())
        rows.append([
            f"Proceso {pid}",
            f"{pstats.avg_total_queue:.2f}",
            str(max_q),
            f"{util*100:.1f}%",
            str(wait),
        ])

    table = Table(rows, colWidths=[3.5*cm, 3*cm, 3*cm, 3.2*cm, 3.3*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D0D7DE")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(table)
    return story


def _task_breakdown(summary, styles):
    story = []
    story.append(Paragraph("Detalle por tarea", styles["Section"]))

    rows = [["Proceso", "Tarea", "T. tarea", "Cola prom.", "Cola máx.",
             "Utiliz.", "Espera tot."]]

    all_tasks = []
    for pid, pstats in summary["processes"].items():
        for tid in sorted(pstats.tasks.keys()):
            all_tasks.append(pstats.tasks[tid])

    # ordenar para mostrar primero los más problemáticos
    all_tasks.sort(key=lambda t: (-t.total_wait_time, t.process_id, t.task_id))

    for t in all_tasks:
        rows.append([
            str(t.process_id),
            str(t.task_id),
            str(t.task_time),
            f"{t.avg_queue_length:.2f}",
            str(t.max_queue_length),
            f"{t.utilization*100:.0f}%",
            str(t.total_wait_time),
        ])

    table = Table(rows, colWidths=[2.2*cm, 2*cm, 2.2*cm, 2.6*cm, 2.4*cm, 2.2*cm, 2.4*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D0D7DE")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    # resaltar la fila del cuello de botella (la primera tras el ordenamiento)
    if len(rows) > 1:
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#FDECEA")),
            ("TEXTCOLOR", (0, 1), (-1, 1), WARN),
            ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ]))

    story.append(table)
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "<i>La fila resaltada en rojo corresponde a la tarea con mayor "
        "tiempo total de espera acumulado.</i>",
        ParagraphStyle("note", parent=styles["Body"],
                       fontSize=8.5, textColor=MUTED),
    ))
    return story


def _products_breakdown(summary, styles):
    story = []
    story.append(Paragraph("Detalle por producto", styles["Section"]))

    rows = [["ID", "Entró tick", "Terminó tick", "Lead time",
             "Ticks en cola", "Ticks procesando"]]

    products = sorted(summary["products"].values(), key=lambda p: p.product_id)
    for p in products:
        lead = (
            (p.finish_tick - p.first_seen_tick + 1)
            if p.finish_tick is not None and p.first_seen_tick is not None
            else None
        )
        rows.append([
            str(p.product_id),
            _fmt(p.first_seen_tick),
            _fmt(p.finish_tick) if p.finish_tick is not None
            else Paragraph(f"<font color='{WARN.hexval()}'>sin terminar</font>", styles["Body"]),
            _fmt(lead),
            str(p.ticks_queued),
            str(p.ticks_processing),
        ])

    table = Table(rows, colWidths=[1.5*cm, 2.5*cm, 2.8*cm, 2.5*cm, 3*cm, 3.5*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#D0D7DE")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    return story


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def generate_pdf(reports_dir: str = "reports",
                 output_path: str = "informe_general.pdf") -> str:
    """Lee los reportes, los analiza y produce el PDF general."""
    analyzer = TelemetryAnalyzer(reports_dir)
    analyzer.load()
    analyzer.analyze()
    summary = analyzer.summary()

    styles = _styles()
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="Informe general de simulación",
    )

    story = []
    story.append(Paragraph("Informe general de simulación", styles["ReportTitle"]))
    story.append(Paragraph(
        f"Línea de ensamblaje · Generado el "
        f"{_dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        styles["ReportSubtitle"],
    ))

    story.extend(_exec_summary(summary, styles))
    story.extend(_global_metrics(summary, styles))
    story.extend(_bottleneck_section(summary, styles))
    story.append(PageBreak())
    story.extend(_process_breakdown(summary, styles))
    story.append(Spacer(1, 10))
    story.extend(_task_breakdown(summary, styles))
    story.append(PageBreak())
    story.extend(_products_breakdown(summary, styles))

    doc.build(story)
    return output_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Genera el informe general en PDF.")
    parser.add_argument("--reports-dir", default="reports",
                        help="Carpeta con los report_tick_*.json")
    parser.add_argument("--output", default="informe_general.pdf",
                        help="Ruta del PDF de salida")
    args = parser.parse_args()

    path = generate_pdf(args.reports_dir, args.output)
    print(f"Informe generado: {path}")