"""
Pestaña de Planificación de Procesos.

Visualiza el diagrama de Gantt y las métricas de los
algoritmos Round Robin, SJF y Prioridad.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
import threading

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services.simulation_service import SimulationService
from config.settings              import (THEME_BG, THEME_FG, THEME_ACCENT,
                                           THEME_SURFACE, THEME_BORDER,
                                           GANTT_COLORS, QUANTUM_DEFAULT)


class SchedulerTab(ttk.Frame):
    """Pestaña del planificador de procesos con diagrama de Gantt."""

    def __init__(self, parent, service: SimulationService, status_cb: Callable):
        super().__init__(parent)
        self.service   = service
        self.status_cb = status_cb
        self.configure(style="Dark.TFrame")
        self._build_ui()

    def _build_ui(self):
        # ── Panel de control (izquierda) ────────────────────────────────
        ctrl = tk.Frame(self, bg=THEME_SURFACE, width=230)
        ctrl.pack(side="left", fill="y", padx=(10, 5), pady=10)
        ctrl.pack_propagate(False)

        ttk.Label(ctrl, text="Planificación",
                   style="Subtitle.TLabel",
                   background=THEME_SURFACE).pack(anchor="w", padx=12, pady=(12, 4))
        ttk.Separator(ctrl).pack(fill="x", padx=10, pady=(0, 10))

        # Selector de algoritmo
        tk.Label(ctrl, text="Algoritmo:", bg=THEME_SURFACE, fg=THEME_FG,
                  font=("Segoe UI", 9)).pack(anchor="w", padx=12)
        self._algo_var = tk.StringVar(value="Round Robin")
        combo = ttk.Combobox(ctrl, textvariable=self._algo_var, state="readonly",
                              values=["Round Robin", "SJF", "Prioridad"],
                              font=("Segoe UI", 10))
        combo.pack(fill="x", padx=12, pady=(2, 10))
        combo.bind("<<ComboboxSelected>>", self._on_algo_change)

        # Quantum
        self._quantum_frame = tk.Frame(ctrl, bg=THEME_SURFACE)
        self._quantum_frame.pack(fill="x", padx=12, pady=(0, 10))
        tk.Label(self._quantum_frame, text="Quantum (q):", bg=THEME_SURFACE,
                  fg=THEME_FG, font=("Segoe UI", 9)).pack(anchor="w")
        self._quantum_var = tk.IntVar(value=QUANTUM_DEFAULT)
        tk.Spinbox(self._quantum_frame, from_=1, to=10,
                    textvariable=self._quantum_var,
                    bg=THEME_BG, fg=THEME_FG,
                    buttonbackground=THEME_SURFACE,
                    relief="flat",
                    font=("Segoe UI", 10)).pack(fill="x")

        ttk.Separator(ctrl).pack(fill="x", padx=10, pady=10)

        # Botón ejecutar
        ttk.Button(ctrl, text="▶ Ejecutar Simulación",
                    style="Accent.TButton",
                    command=self._run_simulation).pack(fill="x", padx=12, pady=(0, 8))

        # Panel de métricas
        ttk.Label(ctrl, text="Métricas Globales:",
                   background=THEME_SURFACE, foreground=THEME_ACCENT,
                   font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(8, 4))

        self._metrics_text = tk.Text(ctrl, height=12, bg=THEME_BG, fg=THEME_FG,
                                      font=("Consolas", 8), relief="flat",
                                      state="disabled", wrap="word",
                                      insertbackground=THEME_FG)
        self._metrics_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # ── Panel principal (derecha): usa PanedWindow vertical ─────────
        main = tk.Frame(self, bg=THEME_BG)
        main.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)

        # Dividimos el panel en dos secciones con PanedWindow para que
        # ambas tablas sean siempre visibles
        paned = tk.PanedWindow(main, orient=tk.VERTICAL,
                                bg=THEME_BG, sashwidth=6,
                                sashrelief="flat", bd=0)
        paned.pack(fill="both", expand=True)

        # ── Sección superior: Gantt ─────────────────────────────────────
        top_frame = tk.Frame(paned, bg=THEME_BG)
        paned.add(top_frame, minsize=200)

        ttk.Label(top_frame, text="Diagrama de Gantt",
                   style="Title.TLabel").pack(anchor="w", pady=(0, 4))

        self._fig, self._ax = plt.subplots(figsize=(8, 2.6))
        self._fig.patch.set_facecolor("#1e1e2e")
        self._ax.set_facecolor("#313244")
        self._fig.tight_layout(pad=1.0)

        self._canvas = FigureCanvasTkAgg(self._fig, master=top_frame)
        self._canvas.get_tk_widget().pack(fill="both", expand=True)

        # ── Sección inferior: tabla resultados ──────────────────────────
        bot_frame = tk.Frame(paned, bg=THEME_BG)
        paned.add(bot_frame, minsize=160)

        ttk.Label(bot_frame, text="Resultados por Proceso",
                   style="Title.TLabel").pack(anchor="w", pady=(6, 4))

        cols = ("PID", "Nombre", "Espera", "Turnaround", "Respuesta",
                "Inicio", "Fin", "Estado")
        widths = [45, 110, 65, 80, 75, 60, 60, 95]

        # Crear frame contenedor y árbol directamente dentro de él
        tree_frame = tk.Frame(bot_frame, bg=THEME_BG)
        tree_frame.pack(fill="both", expand=True)

        vsb2 = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb2.pack(side="right", fill="y")

        self._res_tree = ttk.Treeview(tree_frame, columns=cols,
                                       show="headings", height=6,
                                       yscrollcommand=vsb2.set)
        vsb2.config(command=self._res_tree.yview)
        for c, w in zip(cols, widths):
            self._res_tree.heading(c, text=c)
            self._res_tree.column(c, width=w, anchor="center")
        self._res_tree.pack(side="left", fill="both", expand=True)

    # ── Lógica de simulación ─────────────────────────────────────────────

    def _on_algo_change(self, _=None):
        if self._algo_var.get() == "Round Robin":
            self._quantum_frame.pack(fill="x", padx=12, pady=(0, 10))
        else:
            self._quantum_frame.pack_forget()

    def _run_simulation(self):
        if not self.service.processes:
            messagebox.showwarning("Sin procesos",
                                    "Agrega procesos en la pestaña 'Procesos' primero.")
            return
        self.status_cb("⏳ Ejecutando simulación de planificación...")
        threading.Thread(target=self._do_simulate, daemon=True).start()

    def _do_simulate(self):
        try:
            result = self.service.run_scheduler(
                algorithm=self._algo_var.get(),
                quantum=self._quantum_var.get()
            )
            self.after(0, self._update_results, result)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
            self.after(0, lambda: self.status_cb(f"❌ Error: {e}"))

    def _update_results(self, result: dict):
        self._draw_gantt(result["gantt"], result["processes"])
        self._update_metrics(result["metrics"])
        self._update_table(result["processes"])
        algo    = result["algorithm"]
        metrics = result["metrics"]
        self.status_cb(
            f"✅ {algo} completado │ "
            f"Espera prom: {metrics.get('espera_promedio', 0)} │ "
            f"Turnaround: {metrics.get('turnaround_promedio', 0)} │ "
            f"CPU: {metrics.get('utilizacion_cpu', 0)}%"
        )

    def _draw_gantt(self, gantt: list, processes: list):
        self._ax.clear()
        self._ax.set_facecolor("#313244")

        if not gantt:
            self._canvas.draw()
            return

        pids   = sorted(set(g["pid"] for g in gantt))
        colors = {pid: GANTT_COLORS[i % len(GANTT_COLORS)]
                  for i, pid in enumerate(pids)}
        pid_names = {p.pid: p.name for p in processes}
        yticks    = {}
        y_pos     = 0

        for g in gantt:
            pid   = g["pid"]
            start = g["start"]
            end   = g["end"]
            color = colors[pid]

            if pid not in yticks:
                yticks[pid] = y_pos
                y_pos      += 1

            y = yticks[pid]
            self._ax.barh(y, end - start, left=start, height=0.55,
                           color=color, edgecolor="#11111b", linewidth=0.8)
            if end - start >= 1:
                self._ax.text(start + (end - start) / 2, y,
                               f"{start}–{end}",
                               ha="center", va="center",
                               fontsize=7, color="#1e1e2e", fontweight="bold")

        self._ax.set_yticks(list(yticks.values()))
        self._ax.set_yticklabels(
            [f"P{pid} {pid_names.get(pid,'')}" for pid in yticks],
            color=THEME_FG, fontsize=8)
        self._ax.set_xlabel("Tiempo (unidades)", color=THEME_FG, fontsize=8)
        self._ax.tick_params(colors=THEME_FG, labelsize=8)
        for spine in self._ax.spines.values():
            spine.set_edgecolor(THEME_BORDER)
        self._ax.spines["top"].set_visible(False)
        self._ax.spines["right"].set_visible(False)
        self._ax.grid(axis="x", color="#45475a", alpha=0.5, linestyle="--")
        self._ax.set_title(f"Diagrama de Gantt – {self._algo_var.get()}",
                            color=THEME_ACCENT, fontsize=9, pad=4)
        self._fig.tight_layout(pad=0.8)
        self._canvas.draw()

    def _update_metrics(self, metrics: dict):
        self._metrics_text.config(state="normal")
        self._metrics_text.delete("1.0", "end")
        lines = [
            f"Algoritmo : {metrics.get('algoritmo','—')}",
            f"Procesos  : {metrics.get('num_procesos','—')}",
            f"Makespan  : {metrics.get('makespan','—')} u.t.",
            "─" * 26,
            f"Esp. prom : {metrics.get('espera_promedio','—')} u.t.",
            f"Turnaround: {metrics.get('turnaround_promedio','—')} u.t.",
            f"Respuesta : {metrics.get('respuesta_promedio','—')} u.t.",
            "─" * 26,
            f"Throughput: {metrics.get('throughput','—')} proc/u.t.",
            f"Uso CPU   : {metrics.get('utilizacion_cpu','—')}%",
            f"Ctx Switch: {metrics.get('cambios_contexto','—')}",
        ]
        self._metrics_text.insert("end", "\n".join(lines))
        self._metrics_text.config(state="disabled")

    def _update_table(self, processes: list):
        self._res_tree.delete(*self._res_tree.get_children())
        for p in processes:
            self._res_tree.insert("", "end", values=(
                p.pid, p.name,
                p.waiting_time, p.turnaround_time, p.response_time,
                p.start_time, p.completion_time, p.state.value,
            ))
