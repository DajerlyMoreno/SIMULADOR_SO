"""
Pestaña de Gestión de Procesos.

Permite crear, editar y eliminar procesos, y visualiza
su lista con todas sus características (PCB).
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from models.process         import Process
from services.simulation_service import SimulationService
from config.settings         import (THEME_BG, THEME_FG, THEME_ACCENT,
                                      THEME_SURFACE, THEME_BORDER,
                                      PRIORITY_LEVELS, MAX_PAGES_PER_PROC)


class ProcessTab(ttk.Frame):
    """Pestaña para crear y gestionar procesos simulados."""

    COLUMNS = ("PID", "Nombre", "Prioridad", "Burst", "Llegada",
                "Páginas", "Archivos", "Estado")

    def __init__(self, parent, service: SimulationService, on_change: Callable):
        super().__init__(parent)
        self.service   = service
        self.on_change = on_change
        self._next_pid = 9   # PID autoincremental

        self.configure(style="Dark.TFrame")
        self._build_ui()

    def _build_ui(self):
        """Construye la interfaz de la pestaña."""
        # ── Panel izquierdo: tabla de procesos ─────────────────────────
        left = tk.Frame(self, bg=THEME_BG)
        left.pack(side="left", fill="both", expand=True, padx=(10, 5), pady=10)

        ttk.Label(left, text="Lista de Procesos (PCB)",
                   style="Title.TLabel").pack(anchor="w", pady=(0, 6))

        # Tabla
        tree_frame = tk.Frame(left, bg=THEME_BG)
        tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(tree_frame, columns=self.COLUMNS,
                                   show="headings", height=18)
        widths = [50, 110, 70, 60, 70, 65, 65, 90]
        for col, w in zip(self.COLUMNS, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",
                              command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Botones de acción
        btn_frame = tk.Frame(left, bg=THEME_BG)
        btn_frame.pack(fill="x", pady=(8, 0))

        ttk.Button(btn_frame, text="🗑 Eliminar seleccionado",
                    command=self._delete_selected).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="🔄 Cargar ejemplos",
                    command=self._load_samples).pack(side="left", padx=(0, 6))
        ttk.Button(btn_frame, text="🧹 Limpiar todo",
                    command=self._clear_all).pack(side="left")

        # ── Panel derecho: formulario de nuevo proceso ─────────────────
        right = tk.Frame(self, bg=THEME_SURFACE, width=270)
        right.pack(side="right", fill="y", padx=(5, 10), pady=10)
        right.pack_propagate(False)

        ttk.Label(right, text="Agregar Proceso",
                   style="Subtitle.TLabel",
                   background=THEME_SURFACE).pack(anchor="w", padx=12, pady=(12, 8))

        ttk.Separator(right).pack(fill="x", padx=10, pady=(0, 10))

        self._fields = {}
        field_defs = [
            ("Nombre",      "entry",   {"default": "Proceso"}),
            ("Prioridad",   "spin",    {"from_": 1, "to": PRIORITY_LEVELS, "default": 5}),
            ("Burst Time",  "spin",    {"from_": 1, "to": 30, "default": 5}),
            ("Llegada",     "spin",    {"from_": 0, "to": 20, "default": 0}),
            ("Páginas",     "spin",    {"from_": 1, "to": MAX_PAGES_PER_PROC, "default": 3}),
        ]

        for label, kind, opts in field_defs:
            row = tk.Frame(right, bg=THEME_SURFACE)
            row.pack(fill="x", padx=12, pady=4)

            tk.Label(row, text=label + ":", bg=THEME_SURFACE, fg=THEME_FG,
                      font=("Segoe UI", 9)).pack(anchor="w")

            if kind == "entry":
                var = tk.StringVar(value=opts.get("default", ""))
                w   = tk.Entry(row, textvariable=var,
                                bg=THEME_BG, fg=THEME_FG,
                                insertbackground=THEME_FG,
                                relief="flat",
                                font=("Segoe UI", 10))
            else:  # spin
                var = tk.IntVar(value=opts.get("default", 1))
                w   = tk.Spinbox(row,
                                  from_=opts["from_"], to=opts["to"],
                                  textvariable=var,
                                  bg=THEME_BG, fg=THEME_FG,
                                  buttonbackground=THEME_SURFACE,
                                  relief="flat",
                                  font=("Segoe UI", 10))
            w.pack(fill="x", pady=(2, 0))
            self._fields[label] = var

        # Checkbox archivos
        row = tk.Frame(right, bg=THEME_SURFACE)
        row.pack(fill="x", padx=12, pady=8)
        self._accesses_files = tk.BooleanVar(value=False)
        tk.Checkbutton(row, text="Accede a archivos",
                        variable=self._accesses_files,
                        bg=THEME_SURFACE, fg=THEME_FG,
                        selectcolor=THEME_BG,
                        activebackground=THEME_SURFACE,
                        font=("Segoe UI", 9)).pack(anchor="w")

        ttk.Separator(right).pack(fill="x", padx=10, pady=8)

        ttk.Button(right, text="➕ Agregar Proceso",
                    style="Accent.TButton",
                    command=self._add_process).pack(padx=12, pady=(0, 12), fill="x")

        # Info
        info = ("ℹ  Prioridad: 1 (más alta) – 10 (más baja)\n"
                "   Burst Time: unidades de tiempo de CPU\n"
                "   Páginas: bloques de memoria requeridos")
        tk.Label(right, text=info, bg=THEME_SURFACE, fg="#6c7086",
                  font=("Segoe UI", 8), justify="left",
                  wraplength=230).pack(padx=12, anchor="w")

    # ── Operaciones ────────────────────────────────────────────────────

    def _add_process(self):
        """Agrega un nuevo proceso a la simulación."""
        try:
            name  = str(self._fields["Nombre"].get()).strip() or f"P{self._next_pid}"
            prior = int(self._fields["Prioridad"].get())
            burst = int(self._fields["Burst Time"].get())
            arriv = int(self._fields["Llegada"].get())
            pages = int(self._fields["Páginas"].get())
            files = self._accesses_files.get()

            if burst < 1:
                messagebox.showwarning("Datos inválidos", "El Burst Time debe ser ≥ 1")
                return

            proc = Process(
                pid           = self._next_pid,
                name          = name,
                priority      = prior,
                burst_time    = burst,
                arrival_time  = arriv,
                memory_pages  = pages,
                accesses_files= files,
            )
            self.service.add_process(proc)
            self._next_pid += 1
            self.refresh_table()
            self.on_change()
        except (ValueError, tk.TclError) as e:
            messagebox.showerror("Error", f"Datos inválidos: {e}")

    def _delete_selected(self):
        """Elimina el proceso seleccionado en la tabla."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selección", "Selecciona un proceso primero.")
            return
        item   = self.tree.item(sel[0])
        pid    = int(item["values"][0])
        self.service.processes = [p for p in self.service.processes if p.pid != pid]
        self.refresh_table()
        self.on_change()

    def _clear_all(self):
        """Elimina todos los procesos."""
        if messagebox.askyesno("Confirmar", "¿Eliminar todos los procesos?"):
            self.service.clear_processes()
            self.refresh_table()
            self.on_change()

    def _load_samples(self):
        """Carga procesos de ejemplo."""
        sample = SimulationService.generate_sample_processes(6)
        self.service.set_processes(sample)
        self._next_pid = 9
        self.refresh_table()
        self.on_change()

    def refresh_table(self):
        """Actualiza la tabla con los procesos actuales."""
        self.tree.delete(*self.tree.get_children())
        for p in self.service.processes:
            tag = "running" if p.state.value == "Ejecutando" else ""
            self.tree.insert("", "end", values=(
                p.pid,
                p.name,
                p.priority,
                p.burst_time,
                p.arrival_time,
                p.memory_pages,
                "✅" if p.accesses_files else "❌",
                p.state.value,
            ), tags=(tag,))
        self.tree.tag_configure("running", foreground=THEME_ACCENT)
