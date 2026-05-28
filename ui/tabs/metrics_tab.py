"""
Pestaña de Métricas y Reportes.

Consolida todos los resultados de las simulaciones y
permite exportarlos a CSV y JSON.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

from services.simulation_service import SimulationService
from config.settings              import (THEME_BG, THEME_FG, THEME_ACCENT,
                                           THEME_SURFACE, THEME_SUCCESS,
                                           THEME_ERROR, EXPORT_DIR)


class MetricsTab(ttk.Frame):
    """Pestaña de métricas globales y exportación de reportes."""

    def __init__(self, parent, service: SimulationService):
        super().__init__(parent)
        self.service = service
        self.configure(style="Dark.TFrame")
        self._build_ui()

    def _build_ui(self):
        # ── Cabecera ────────────────────────────────────────────────────
        top = tk.Frame(self, bg=THEME_BG)
        top.pack(fill="x", padx=10, pady=(10, 4))

        ttk.Label(top, text="Métricas Consolidadas y Reportes",
                   style="Title.TLabel").pack(side="left")

        ttk.Button(top, text="🔄 Actualizar",
                    command=self.refresh).pack(side="right", padx=4)
        ttk.Button(top, text="📥 Exportar CSV",
                    style="Accent.TButton",
                    command=self._export_csv).pack(side="right", padx=4)
        ttk.Button(top, text="📄 Exportar JSON",
                    command=self._export_json).pack(side="right", padx=4)

        ttk.Separator(self).pack(fill="x", padx=10, pady=4)

        # ── Tres columnas de métricas ────────────────────────────────────
        cols_frame = tk.Frame(self, bg=THEME_BG)
        cols_frame.pack(fill="x", padx=10, pady=4)

        self._sched_box  = self._make_card(cols_frame, "📋 Planificación")
        self._mem_box    = self._make_card(cols_frame, "💾 Memoria")
        self._files_box  = self._make_card(cols_frame, "📁 Archivos")

        for box in (self._sched_box, self._mem_box, self._files_box):
            box.pack(side="left", fill="both", expand=True, padx=4)

        ttk.Separator(self).pack(fill="x", padx=10, pady=8)

        # ── Tabla de procesos (resultados del planificador) ──────────────
        ttk.Label(self, text="Detalle por Proceso (última simulación de planificación)",
                   style="Title.TLabel").pack(anchor="w", padx=10, pady=(0, 4))

        cols = ("PID", "Nombre", "Prioridad", "Burst", "Espera",
                "Turnaround", "Respuesta", "Inicio", "Fin")
        self._proc_tree = ttk.Treeview(self, columns=cols, show="headings", height=8)
        ws = [45, 100, 65, 60, 65, 80, 75, 60, 60]
        for c, w in zip(cols, ws):
            self._proc_tree.heading(c, text=c)
            self._proc_tree.column(c, width=w, anchor="center")

        vsb = ttk.Scrollbar(self, orient="vertical",
                              command=self._proc_tree.yview)
        self._proc_tree.configure(yscrollcommand=vsb.set)
        pf = tk.Frame(self, bg=THEME_BG)
        pf.pack(fill="x", padx=10)
        self._proc_tree.pack(side="left", in_=pf, fill="x", expand=True)
        vsb.pack(side="right", in_=pf, fill="y")

        ttk.Separator(self).pack(fill="x", padx=10, pady=8)

        # ── Zona de exportación ──────────────────────────────────────────
        exp_frame = tk.Frame(self, bg=THEME_SURFACE)
        exp_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Label(exp_frame, text="📂 Archivos exportados:",
                   background=THEME_SURFACE, foreground=THEME_ACCENT,
                   font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=10, pady=(8, 4))

        self._export_log = tk.Text(exp_frame, height=5, bg=THEME_BG, fg=THEME_FG,
                                    font=("Consolas", 8), state="disabled",
                                    relief="flat")
        self._export_log.pack(fill="x", padx=10, pady=(0, 10))

    def _make_card(self, parent, title: str) -> tk.Text:
        """Crea una tarjeta de métricas."""
        card = tk.Frame(parent, bg=THEME_SURFACE, pady=8)
        tk.Label(card, text=title, bg=THEME_SURFACE, fg=THEME_ACCENT,
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10)
        text = tk.Text(card, height=8, bg=THEME_SURFACE, fg=THEME_FG,
                        font=("Consolas", 8), state="disabled",
                        relief="flat", wrap="word")
        text.pack(fill="both", expand=True, padx=8, pady=(4, 4))
        return text

    # ── Actualización ────────────────────────────────────────────────────

    def refresh(self):
        """Actualiza todas las métricas mostradas."""
        self._update_scheduler_metrics()
        self._update_memory_metrics()
        self._update_files_metrics()
        self._update_process_table()

    def _update_scheduler_metrics(self):
        m = self.service.scheduler_metrics
        self._set_text(self._sched_box, [
            f"Algoritmo : {m.get('algoritmo','—')}",
            f"Procesos  : {m.get('num_procesos','—')}",
            f"Makespan  : {m.get('makespan','—')} u.t.",
            "─" * 22,
            f"Esp. prom : {m.get('espera_promedio','—')}",
            f"Turnaround: {m.get('turnaround_promedio','—')}",
            f"Respuesta : {m.get('respuesta_promedio','—')}",
            f"Throughput: {m.get('throughput','—')}",
            f"CPU %     : {m.get('utilizacion_cpu','—')}%",
            f"Ctx Switch: {m.get('cambios_contexto','—')}",
        ])

    def _update_memory_metrics(self):
        s = self.service.memory_stats
        self._set_text(self._mem_box, [
            f"Algoritmo  : {s.get('algoritmo','—')}",
            f"Marcos     : {s.get('num_marcos','—')}",
            "─" * 22,
            f"Accesos    : {s.get('total_accesos','—')}",
            f"Page Hits  : {s.get('page_hits','—')}",
            f"Page Faults: {s.get('page_faults','—')}",
            f"Hit Ratio  : {round(s.get('hit_ratio',0)*100,2)}%",
            f"Fault Ratio: {round(s.get('fault_ratio',0)*100,2)}%",
        ])

    def _update_files_metrics(self):
        summaries = self.service.file_summaries
        if not summaries:
            self._set_text(self._files_box, ["Sin datos aún."])
            return
        lines = []
        total_r = total_w = total_c = 0
        for s in summaries:
            total_r += s.get("Total Lecturas",  0)
            total_w += s.get("Total Escrituras", 0)
            total_c += s.get("Conflictos",       0)
        lines = [
            f"Archivos   : {len(summaries)}",
            f"Total Lect.: {total_r}",
            f"Total Escr.: {total_w}",
            f"Conflictos : {total_c}",
            "─" * 22,
        ]
        for s in summaries:
            lines.append(f"{s['Archivo']}: L={s['Total Lecturas']} "
                          f"E={s['Total Escrituras']} C={s['Conflictos']}")
        self._set_text(self._files_box, lines)

    def _update_process_table(self):
        self._proc_tree.delete(*self._proc_tree.get_children())
        for p in self.service.scheduler_result:
            self._proc_tree.insert("", "end", values=(
                p.pid, p.name, p.priority, p.burst_time,
                p.waiting_time, p.turnaround_time, p.response_time,
                p.start_time, p.completion_time,
            ))

    # ── Exportación ───────────────────────────────────────────────────────

    def _export_csv(self):
        if not self.service.scheduler_result:
            messagebox.showwarning("Sin datos",
                                    "Ejecuta la simulación de planificación primero.")
            return
        path = self.service.export_metrics_csv()
        if path:
            self._log_export(f"CSV exportado: {path}")
            messagebox.showinfo("Exportado", f"CSV guardado en:\n{path}")

    def _export_json(self):
        path = self.service.export_full_report_json()
        if path:
            self._log_export(f"JSON exportado: {path}")
            messagebox.showinfo("Exportado", f"Reporte JSON guardado en:\n{path}")

    def _log_export(self, msg: str):
        self._export_log.config(state="normal")
        self._export_log.insert("end", f"✅ {msg}\n")
        self._export_log.config(state="disabled")

    @staticmethod
    def _set_text(widget: tk.Text, lines: list):
        widget.config(state="normal")
        widget.delete("1.0", "end")
        widget.insert("end", "\n".join(lines))
        widget.config(state="disabled")
