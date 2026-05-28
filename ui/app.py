"""
Ventana Principal de la Aplicación – Simulador de SO.

Construida con tkinter + ttk. Organiza las cuatro pestañas:
  1. Planificación de Procesos
  2. Gestión de Memoria
  3. Gestión de Archivos
  4. Métricas y Reportes
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Asegurar que el directorio raíz del proyecto esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings         import (APP_TITLE, APP_WIDTH, APP_HEIGHT,
                                      THEME_BG, THEME_FG, THEME_ACCENT,
                                      THEME_SURFACE, THEME_BORDER)
from services.simulation_service import SimulationService
from ui.tabs.process_tab         import ProcessTab
from ui.tabs.scheduler_tab       import SchedulerTab
from ui.tabs.memory_tab          import MemoryTab
from ui.tabs.files_tab           import FilesTab
from ui.tabs.metrics_tab         import MetricsTab


class SimulatorApp(tk.Tk):
    """
    Ventana raíz de la aplicación.

    Gestiona el ciclo de vida de la GUI y distribuye el servicio
    de simulación a todas las pestañas.
    """

    def __init__(self):
        super().__init__()

        # ── Servicio compartido entre pestañas ─────────────────────────
        self.service = SimulationService()

        # ── Configuración de la ventana principal ──────────────────────
        self.title(APP_TITLE)
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.configure(bg=THEME_BG)
        self.resizable(True, True)
        self.minsize(900, 600)

        # Centrar en pantalla
        self._center_window()

        # ── Estilo ttk ────────────────────────────────────────────────
        self._configure_styles()

        # ── Layout ────────────────────────────────────────────────────
        self._build_header()
        self._build_notebook()
        self._build_statusbar()

        # Cargar procesos de ejemplo al iniciar
        self._load_sample_data()

    # ── Construcción de la UI ─────────────────────────────────────────

    def _center_window(self):
        """Centra la ventana en el monitor."""
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - APP_WIDTH)  // 2
        y  = (sh - APP_HEIGHT) // 2
        self.geometry(f"{APP_WIDTH}x{APP_HEIGHT}+{x}+{y}")

    def _configure_styles(self):
        """Configura el tema visual de la aplicación."""
        style = ttk.Style(self)
        style.theme_use("clam")

        # Notebook (pestañas)
        style.configure("TNotebook",
                         background=THEME_BG,
                         borderwidth=0)
        style.configure("TNotebook.Tab",
                         background=THEME_SURFACE,
                         foreground=THEME_FG,
                         padding=[16, 8],
                         font=("Segoe UI", 10, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", THEME_ACCENT)],
                  foreground=[("selected", "#1e1e2e")])

        # Frames
        style.configure("Dark.TFrame", background=THEME_BG)
        style.configure("Card.TFrame", background=THEME_SURFACE,
                         relief="flat", borderwidth=1)

        # Labels
        style.configure("TLabel", background=THEME_BG, foreground=THEME_FG,
                         font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=THEME_BG,
                         foreground=THEME_ACCENT,
                         font=("Segoe UI", 13, "bold"))
        style.configure("Subtitle.TLabel", background=THEME_SURFACE,
                         foreground=THEME_FG,
                         font=("Segoe UI", 10, "bold"))
        style.configure("Small.TLabel", background=THEME_BG, foreground="#a6adc8",
                         font=("Segoe UI", 9))

        # Botones
        style.configure("Accent.TButton",
                         background=THEME_ACCENT,
                         foreground="#1e1e2e",
                         font=("Segoe UI", 10, "bold"),
                         padding=[12, 6],
                         relief="flat")
        style.map("Accent.TButton",
                  background=[("active", "#74c7ec")])

        style.configure("TButton",
                         background=THEME_SURFACE,
                         foreground=THEME_FG,
                         font=("Segoe UI", 10),
                         padding=[10, 5],
                         relief="flat")

        # Scrollbars
        style.configure("TScrollbar",
                         background=THEME_SURFACE,
                         troughcolor=THEME_BG,
                         borderwidth=0,
                         arrowcolor=THEME_FG)

        # Treeview (tablas)
        style.configure("Treeview",
                         background=THEME_SURFACE,
                         foreground=THEME_FG,
                         fieldbackground=THEME_SURFACE,
                         rowheight=26,
                         font=("Consolas", 9))
        style.configure("Treeview.Heading",
                         background=THEME_BG,
                         foreground=THEME_ACCENT,
                         font=("Segoe UI", 9, "bold"))
        style.map("Treeview",
                  background=[("selected", THEME_ACCENT)],
                  foreground=[("selected", "#1e1e2e")])

        # Entry / Spinbox
        style.configure("TEntry",
                         fieldbackground=THEME_SURFACE,
                         foreground=THEME_FG,
                         insertcolor=THEME_FG,
                         borderwidth=1)
        style.configure("TSpinbox",
                         fieldbackground=THEME_SURFACE,
                         foreground=THEME_FG,
                         background=THEME_SURFACE)
        style.configure("TCombobox",
                         fieldbackground=THEME_SURFACE,
                         foreground=THEME_FG,
                         background=THEME_SURFACE)

        # Separator
        style.configure("TSeparator", background=THEME_BORDER)

    def _build_header(self):
        """Crea el encabezado superior de la ventana."""
        header = tk.Frame(self, bg="#11111b", height=60)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # Logo / Título
        tk.Label(header,
                  text="⚙  Simulador de Sistema Operativo",
                  bg="#11111b", fg=THEME_ACCENT,
                  font=("Segoe UI", 14, "bold")).pack(side="left", padx=20, pady=15)

        tk.Label(header,
                  text="UPTC – Sistemas Operativos 2026-1",
                  bg="#11111b", fg="#6c7086",
                  font=("Segoe UI", 10)).pack(side="right", padx=20, pady=15)

    def _build_notebook(self):
        """Crea el Notebook con todas las pestañas."""
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=(4, 0))

        # ── Pestaña 1: Procesos ────────────────────────────────────────
        self.process_tab = ProcessTab(self.notebook, self.service,
                                       self._on_processes_changed)
        self.notebook.add(self.process_tab, text="  📋 Procesos  ")

        # ── Pestaña 2: Planificación ───────────────────────────────────
        self.scheduler_tab = SchedulerTab(self.notebook, self.service,
                                           self._update_status)
        self.notebook.add(self.scheduler_tab, text="  🔄 Planificación  ")

        # ── Pestaña 3: Memoria ─────────────────────────────────────────
        self.memory_tab = MemoryTab(self.notebook, self.service,
                                     self._update_status)
        self.notebook.add(self.memory_tab, text="  💾 Memoria  ")

        # ── Pestaña 4: Archivos ────────────────────────────────────────
        self.files_tab = FilesTab(self.notebook, self.service,
                                   self._update_status)
        self.notebook.add(self.files_tab, text="  📁 Archivos  ")

        # ── Pestaña 5: Métricas ────────────────────────────────────────
        self.metrics_tab = MetricsTab(self.notebook, self.service)
        self.notebook.add(self.metrics_tab, text="  📊 Métricas  ")

    def _build_statusbar(self):
        """Crea la barra de estado inferior."""
        self.statusbar_var = tk.StringVar(value="✅ Listo. Cargados procesos de ejemplo.")
        bar = tk.Frame(self, bg="#11111b", height=28)
        bar.pack(fill="x", side="bottom")
        tk.Label(bar,
                  textvariable=self.statusbar_var,
                  bg="#11111b", fg="#6c7086",
                  font=("Segoe UI", 9),
                  anchor="w").pack(side="left", padx=12, pady=4)

        tk.Label(bar,
                  text="Python 3 | tkinter | matplotlib",
                  bg="#11111b", fg="#45475a",
                  font=("Segoe UI", 8)).pack(side="right", padx=12)

    # ── Eventos y callbacks ────────────────────────────────────────────

    def _on_processes_changed(self):
        """Se llama cuando la lista de procesos cambia."""
        n = len(self.service.processes)
        self._update_status(f"✅ {n} proceso(s) cargado(s). Listo para simular.")

    def _update_status(self, msg: str):
        """Actualiza la barra de estado."""
        self.statusbar_var.set(msg)
        self.update_idletasks()

    def _load_sample_data(self):
        """Carga procesos de ejemplo al iniciar la aplicación."""
        sample = SimulationService.generate_sample_processes(6)
        self.service.set_processes(sample)
        self.process_tab.refresh_table()
        self._on_processes_changed()


def launch():
    """Punto de entrada de la interfaz gráfica."""
    app = SimulatorApp()
    app.mainloop()


if __name__ == "__main__":
    launch()
