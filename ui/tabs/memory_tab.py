"""
Pestaña de Gestión de Memoria.

Visualiza la paginación por demanda, los marcos de página
y las estadísticas de Page Hits / Page Faults para FIFO y LRU.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
import threading

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from services.simulation_service import SimulationService
from config.settings              import (THEME_BG, THEME_FG, THEME_ACCENT,
                                           THEME_SURFACE, THEME_SUCCESS,
                                           THEME_ERROR, TOTAL_FRAMES,
                                           GANTT_COLORS)


class MemoryTab(ttk.Frame):
    """Pestaña de gestión de memoria con paginación por demanda."""

    def __init__(self, parent, service: SimulationService, status_cb: Callable):
        super().__init__(parent)
        self.service   = service
        self.status_cb = status_cb
        self.configure(style="Dark.TFrame")
        self._build_ui()

    def _build_ui(self):
        # ── Panel de control ─────────────────────────────────────────────
        ctrl = tk.Frame(self, bg=THEME_SURFACE, width=240)
        ctrl.pack(side="left", fill="y", padx=(10, 5), pady=10)
        ctrl.pack_propagate(False)

        ttk.Label(ctrl, text="Gestión de Memoria",
                   style="Subtitle.TLabel",
                   background=THEME_SURFACE).pack(anchor="w", padx=12, pady=(12, 4))
        ttk.Separator(ctrl).pack(fill="x", padx=10, pady=(0, 10))

        # Algoritmo
        tk.Label(ctrl, text="Algoritmo de Reemplazo:",
                  bg=THEME_SURFACE, fg=THEME_FG, font=("Segoe UI", 9)).pack(
            anchor="w", padx=12)
        self._algo_var = tk.StringVar(value="LRU")
        ttk.Combobox(ctrl, textvariable=self._algo_var, state="readonly",
                      values=["FIFO", "LRU"],
                      font=("Segoe UI", 10)).pack(fill="x", padx=12, pady=(2, 10))

        # Número de marcos
        tk.Label(ctrl, text="Marcos de RAM:", bg=THEME_SURFACE, fg=THEME_FG,
                  font=("Segoe UI", 9)).pack(anchor="w", padx=12)
        self._frames_var = tk.IntVar(value=TOTAL_FRAMES)
        tk.Spinbox(ctrl, from_=2, to=16, textvariable=self._frames_var,
                    bg=THEME_BG, fg=THEME_FG,
                    buttonbackground=THEME_SURFACE,
                    relief="flat", font=("Segoe UI", 10)).pack(
            fill="x", padx=12, pady=(2, 10))

        ttk.Separator(ctrl).pack(fill="x", padx=10, pady=6)

        ttk.Button(ctrl, text="▶ Ejecutar Simulación",
                    style="Accent.TButton",
                    command=self._run_simulation).pack(fill="x", padx=12, pady=(0, 10))

        # Panel de estadísticas
        ttk.Label(ctrl, text="Estadísticas Globales:",
                   background=THEME_SURFACE, foreground=THEME_ACCENT,
                   font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(4, 4))

        self._stats_text = tk.Text(ctrl, height=14, bg=THEME_BG, fg=THEME_FG,
                                    font=("Consolas", 8), relief="flat",
                                    state="disabled", wrap="word")
        self._stats_text.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        # Leyenda
        leg = tk.Frame(ctrl, bg=THEME_SURFACE)
        leg.pack(fill="x", padx=12, pady=(0, 10))
        for color, txt in [(THEME_SUCCESS, "Page Hit"),
                            (THEME_ERROR,   "Page Fault")]:
            row = tk.Frame(leg, bg=THEME_SURFACE)
            row.pack(anchor="w")
            tk.Label(row, text="■", fg=color, bg=THEME_SURFACE,
                      font=("Segoe UI", 12)).pack(side="left")
            tk.Label(row, text=txt, bg=THEME_SURFACE, fg=THEME_FG,
                      font=("Segoe UI", 8)).pack(side="left", padx=4)

        # ── Panel principal ───────────────────────────────────────────────
        main = tk.Frame(self, bg=THEME_BG)
        main.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)

        # Gráfica de barras: hits vs faults por proceso
        ttk.Label(main, text="Comparativa Hit/Fault por Proceso",
                   style="Title.TLabel").pack(anchor="w", pady=(0, 4))

        self._fig, self._ax = plt.subplots(figsize=(8, 3))
        self._fig.patch.set_facecolor("#1e1e2e")
        self._ax.set_facecolor("#313244")
        self._canvas = FigureCanvasTkAgg(self._fig, master=main)
        self._canvas.get_tk_widget().pack(fill="x", pady=(0, 8))

        # Tabla de marcos actuales
        ttk.Label(main, text="Estado de Marcos de Página",
                   style="Title.TLabel").pack(anchor="w", pady=(4, 4))

        frame_cols = ("Marco", "PID", "Página", "Estado")
        self._frame_tree = ttk.Treeview(main, columns=frame_cols,
                                          show="headings", height=5)
        for c in frame_cols:
            self._frame_tree.heading(c, text=c)
            self._frame_tree.column(c, width=100, anchor="center")
        self._frame_tree.pack(fill="x", pady=(0, 8))

        # Tabla de eventos de Page Fault
        ttk.Label(main, text="Registro de Fallos de Página",
                   style="Title.TLabel").pack(anchor="w", pady=(4, 4))

        ev_cols = ("Tiempo", "PID", "Página", "Expulsó PID", "Expulsó Pág", "Alg.")
        self._ev_tree = ttk.Treeview(main, columns=ev_cols, show="headings", height=5)
        ws = [60, 50, 65, 90, 90, 60]
        for c, w in zip(ev_cols, ws):
            self._ev_tree.heading(c, text=c)
            self._ev_tree.column(c, width=w, anchor="center")

        vsb = ttk.Scrollbar(main, orient="vertical", command=self._ev_tree.yview)
        self._ev_tree.configure(yscrollcommand=vsb.set)
        ef = tk.Frame(main, bg=THEME_BG)
        ef.pack(fill="both", expand=True)
        self._ev_tree.pack(side="left", in_=ef, fill="both", expand=True)
        vsb.pack(side="right", in_=ef, fill="y")

    # ── Simulación ────────────────────────────────────────────────────────

    def _run_simulation(self):
        if not self.service.processes:
            messagebox.showwarning("Sin procesos",
                                    "Agrega procesos en la pestaña 'Procesos'.")
            return
        self.status_cb("⏳ Simulando gestión de memoria...")
        threading.Thread(target=self._do_simulate, daemon=True).start()

    def _do_simulate(self):
        try:
            result = self.service.run_memory_simulation(
                algorithm  = self._algo_var.get(),
                num_frames = self._frames_var.get(),
            )
            self.after(0, self._update_results, result)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))

    def _update_results(self, result: dict):
        """Actualiza todos los elementos visuales."""
        self._draw_chart(result["results"])
        self._update_stats(result["stats"])
        self._update_frame_table(result["frames"])
        self._update_events_table(result["events"])
        s = result["stats"]
        self.status_cb(
            f"✅ Memoria {result['algorithm']} │ "
            f"Hits: {s.get('page_hits',0)} │ "
            f"Faults: {s.get('page_faults',0)} │ "
            f"Hit Ratio: {round(s.get('hit_ratio',0)*100,1)}%"
        )

    def _draw_chart(self, results: list):
        """Dibuja la gráfica de barras de hits vs faults."""
        self._ax.clear()
        self._ax.set_facecolor("#313244")

        if not results:
            self._canvas.draw()
            return

        names  = [r["nombre"] for r in results]
        hits   = [r["page_hits"]   for r in results]
        faults = [r["page_faults"] for r in results]
        x      = range(len(names))

        bars1 = self._ax.bar([i - 0.2 for i in x], hits,   0.4,
                              label="Page Hits",   color=THEME_SUCCESS, alpha=0.85)
        bars2 = self._ax.bar([i + 0.2 for i in x], faults, 0.4,
                              label="Page Faults", color=THEME_ERROR,   alpha=0.85)

        self._ax.set_xticks(list(x))
        self._ax.set_xticklabels(names, color=THEME_FG, fontsize=8)
        self._ax.tick_params(colors=THEME_FG, labelsize=8)
        self._ax.set_ylabel("Accesos", color=THEME_FG, fontsize=8)
        self._ax.set_title(f"Hit vs Fault – Algoritmo {self._algo_var.get()}",
                            color=THEME_ACCENT, fontsize=9)
        self._ax.legend(loc="upper right", fontsize=7,
                         facecolor=THEME_SURFACE, edgecolor=THEME_SURFACE,
                         labelcolor=THEME_FG)

        for spine in self._ax.spines.values():
            spine.set_edgecolor("#45475a")
        self._ax.grid(axis="y", color="#45475a", alpha=0.4, linestyle="--")

        self._fig.tight_layout()
        self._canvas.draw()

    def _update_stats(self, stats: dict):
        self._stats_text.config(state="normal")
        self._stats_text.delete("1.0", "end")
        lines = [
            f"Algoritmo  : {stats.get('algoritmo','—')}",
            f"Marcos RAM : {stats.get('num_marcos','—')}",
            "─" * 28,
            f"Accesos    : {stats.get('total_accesos','—')}",
            f"Page Hits  : {stats.get('page_hits','—')}",
            f"Page Faults: {stats.get('page_faults','—')}",
            "─" * 28,
            f"Hit Ratio  : {round(stats.get('hit_ratio',0)*100,2)}%",
            f"Fault Ratio: {round(stats.get('fault_ratio',0)*100,2)}%",
        ]
        self._stats_text.insert("end", "\n".join(lines))
        self._stats_text.config(state="disabled")

    def _update_frame_table(self, frames: list):
        self._frame_tree.delete(*self._frame_tree.get_children())
        for f in frames:
            state = "LIBRE" if f.is_free else "OCUPADO"
            self._frame_tree.insert("", "end", values=(
                f.frame_number,
                f.pid if not f.is_free else "—",
                f.page_number if not f.is_free else "—",
                state,
            ))
            if not f.is_free:
                self._frame_tree.item(self._frame_tree.get_children()[-1],
                                       tags=("used",))
        self._frame_tree.tag_configure("used", foreground=THEME_ACCENT)

    def _update_events_table(self, events: list):
        self._ev_tree.delete(*self._ev_tree.get_children())
        for ev in events:
            self._ev_tree.insert("", "end", values=(
                ev.time,
                ev.pid,
                ev.page_number,
                ev.evicted_pid  if ev.evicted_pid  is not None else "—",
                ev.evicted_page if ev.evicted_page is not None else "—",
                ev.algorithm,
            ))
