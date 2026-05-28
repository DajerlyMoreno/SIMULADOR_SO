"""
Pestaña de Gestión de Archivos Concurrentes.

Simula y visualiza el acceso concurrente de procesos a archivos,
con control de bloqueo mediante mutex/semáforo.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable
import threading

from services.simulation_service import SimulationService
from models.file_resource         import FileOperation
from config.settings              import (THEME_BG, THEME_FG, THEME_ACCENT,
                                           THEME_SURFACE, THEME_SUCCESS,
                                           THEME_ERROR, THEME_WARNING)


class FilesTab(ttk.Frame):
    """Pestaña de acceso concurrente a archivos con mutex/semáforos."""

    def __init__(self, parent, service: SimulationService, status_cb: Callable):
        super().__init__(parent)
        self.service   = service
        self.status_cb = status_cb
        self.configure(style="Dark.TFrame")
        self._running = False
        self._build_ui()

    def _build_ui(self):
        # ── Panel de control (izquierda) ──────────────────────────────────
        ctrl = tk.Frame(self, bg=THEME_SURFACE, width=235)
        ctrl.pack(side="left", fill="y", padx=(10, 5), pady=10)
        ctrl.pack_propagate(False)

        ttk.Label(ctrl, text="Gestión de Archivos",
                   style="Subtitle.TLabel",
                   background=THEME_SURFACE).pack(anchor="w", padx=12, pady=(12, 4))
        ttk.Separator(ctrl).pack(fill="x", padx=10, pady=(0, 10))

        tk.Label(ctrl,
                  text="Simula lectura/escritura concurrente\n"
                       "con Mutex y Semáforos:\n\n"
                       "• Múltiples lectores simultáneos\n"
                       "• Un escritor exclusivo (Mutex)\n"
                       "• Conflictos detectados",
                  bg=THEME_SURFACE, fg="#a6adc8",
                  font=("Segoe UI", 8), justify="left",
                  wraplength=200).pack(padx=12, anchor="w", pady=(0, 10))

        ttk.Separator(ctrl).pack(fill="x", padx=10, pady=4)

        ttk.Button(ctrl, text="▶ Ejecutar Simulación",
                    style="Accent.TButton",
                    command=self._run_simulation).pack(fill="x", padx=12, pady=8)

        ttk.Button(ctrl, text="🗑 Limpiar Registro",
                    command=self._clear_log).pack(fill="x", padx=12, pady=(0, 8))

        # Resumen por archivo
        ttk.Label(ctrl, text="Resumen por Archivo:",
                   background=THEME_SURFACE, foreground=THEME_ACCENT,
                   font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(8, 4))

        # Treeview del resumen directamente en ctrl
        sum_frame = tk.Frame(ctrl, bg=THEME_SURFACE)
        sum_frame.pack(fill="x", padx=8, pady=(0, 8))

        self._summary_tree = ttk.Treeview(sum_frame,
                                           columns=("Archivo", "Lect", "Escr", "Conf"),
                                           show="headings", height=7)
        for c, w in [("Archivo", 85), ("Lect", 38), ("Escr", 38), ("Conf", 38)]:
            self._summary_tree.heading(c, text=c)
            self._summary_tree.column(c, width=w, anchor="center")
        self._summary_tree.pack(side="left", fill="x", expand=True)

        # Contadores
        self._count_frame = tk.Frame(ctrl, bg=THEME_SURFACE)
        self._count_frame.pack(fill="x", padx=12, pady=(4, 10))
        self._total_var    = tk.StringVar(value="Total: 0")
        self._conflict_var = tk.StringVar(value="Conflictos: 0")
        self._ok_var       = tk.StringVar(value="Exitosas: 0")

        for var, color in [(self._ok_var,       THEME_SUCCESS),
                            (self._conflict_var, THEME_ERROR),
                            (self._total_var,    THEME_ACCENT)]:
            tk.Label(self._count_frame, textvariable=var,
                      bg=THEME_SURFACE, fg=color,
                      font=("Segoe UI", 9, "bold")).pack(anchor="w")

        # ── Panel principal (derecha): registro de eventos ─────────────────
        main = tk.Frame(self, bg=THEME_BG)
        main.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)

        ttk.Label(main, text="Registro de Accesos Concurrentes",
                   style="Title.TLabel").pack(anchor="w", pady=(0, 6))

        # Leyenda de colores
        leg = tk.Frame(main, bg=THEME_BG)
        leg.pack(fill="x", pady=(0, 6))
        for color, txt in [(THEME_SUCCESS, "■ Lectura OK"),
                            (THEME_ACCENT,  "■ Escritura OK"),
                            (THEME_ERROR,   "■ Conflicto / Bloqueado")]:
            tk.Label(leg, text=txt, fg=color, bg=THEME_BG,
                      font=("Segoe UI", 8)).pack(side="left", padx=8)

        # Tabla de eventos — creada directamente dentro de un frame limpio
        ev_cols = ("T", "PID", "Archivo", "Operación", "Estado", "Tiempo(ms)", "Mensaje")
        col_widths = [40, 50, 110, 80, 90, 85, 320]

        ev_frame = tk.Frame(main, bg=THEME_BG)
        ev_frame.pack(fill="both", expand=True)

        # Scrollbar vertical
        vsb = ttk.Scrollbar(ev_frame, orient="vertical")
        vsb.pack(side="right", fill="y")

        # Scrollbar horizontal
        hsb = ttk.Scrollbar(main, orient="horizontal")
        hsb.pack(fill="x", side="bottom")

        # Treeview como hijo directo de ev_frame
        self._ev_tree = ttk.Treeview(ev_frame, columns=ev_cols, show="headings",
                                      yscrollcommand=vsb.set,
                                      xscrollcommand=hsb.set)
        vsb.config(command=self._ev_tree.yview)
        hsb.config(command=self._ev_tree.xview)

        for c, w in zip(ev_cols, col_widths):
            self._ev_tree.heading(c, text=c)
            self._ev_tree.column(c, width=w,
                                   anchor="center" if w < 200 else "w",
                                   minwidth=w)
        self._ev_tree.pack(side="left", fill="both", expand=True)

        # Tags de colores
        self._ev_tree.tag_configure("read",     foreground=THEME_SUCCESS)
        self._ev_tree.tag_configure("write",    foreground=THEME_ACCENT)
        self._ev_tree.tag_configure("conflict", foreground=THEME_ERROR)

    # ── Simulación ─────────────────────────────────────────────────────────

    def _run_simulation(self):
        if self._running:
            messagebox.showinfo("En progreso", "La simulación ya está en ejecución.")
            return
        if not self.service.processes:
            messagebox.showwarning("Sin procesos",
                                    "Agrega procesos en la pestaña 'Procesos'.")
            return

        self._running = True
        self.status_cb("⏳ Simulando acceso concurrente a archivos...")
        threading.Thread(target=self._do_simulate, daemon=True).start()

    def _do_simulate(self):
        try:
            result = self.service.run_file_simulation()
            self.after(0, self._update_all, result)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self._running = False

    def _update_all(self, result: dict):
        """Actualiza la tabla de eventos y el resumen de una sola vez."""
        all_ev    = result.get("all_events", [])
        conflicts = result.get("conflicts",  [])
        ok        = [e for e in all_ev if e.success]

        # ── Poblar tabla de eventos ────────────────────────────────────
        self._ev_tree.delete(*self._ev_tree.get_children())
        for ev in all_ev:
            op_str = ev.operation.value
            ok_str = "✅ OK" if ev.success else "❌ Bloqueado"
            tag    = ("conflict" if ev.conflict else
                      ("write" if ev.operation == FileOperation.WRITE else "read"))
            self._ev_tree.insert("", "end", values=(
                ev.time,
                f"P{ev.pid}",
                ev.filename,
                op_str,
                ok_str,
                f"{ev.wait_time:.1f} ms",
                ev.message or "—",
            ), tags=(tag,))

        # Hacer scroll al último evento
        children = self._ev_tree.get_children()
        if children:
            self._ev_tree.see(children[-1])

        # ── Actualizar resumen por archivo ─────────────────────────────
        self._summary_tree.delete(*self._summary_tree.get_children())
        for s in result.get("summaries", []):
            self._summary_tree.insert("", "end", values=(
                s["Archivo"],
                s["Total Lecturas"],
                s["Total Escrituras"],
                s["Conflictos"],
            ))

        # ── Actualizar contadores ──────────────────────────────────────
        self._total_var.set(f"Total: {len(all_ev)}")
        self._conflict_var.set(f"Conflictos: {len(conflicts)}")
        self._ok_var.set(f"Exitosas: {len(ok)}")

        self.status_cb(
            f"✅ Archivos │ Operaciones: {len(all_ev)} │ "
            f"Conflictos: {len(conflicts)} │ OK: {len(ok)}"
        )

    def _clear_log(self):
        """Limpia el registro de eventos."""
        self._ev_tree.delete(*self._ev_tree.get_children())
        self._summary_tree.delete(*self._summary_tree.get_children())
        self._total_var.set("Total: 0")
        self._conflict_var.set("Conflictos: 0")
        self._ok_var.set("Exitosas: 0")
