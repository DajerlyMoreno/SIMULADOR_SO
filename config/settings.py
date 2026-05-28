"""
Configuración global del simulador de Sistema Operativo.
Universidad Pedagógica y Tecnológica de Colombia - UPTC
Sistemas Operativos 2026-1
"""

# ─────────────────────────────────────────
#  Configuración del planificador
# ─────────────────────────────────────────
QUANTUM_DEFAULT = 2          # Quantum de tiempo para Round Robin (unidades)
MAX_PROCESSES   = 20         # Máximo número de procesos simultáneos
PRIORITY_LEVELS = 10         # Niveles de prioridad (1 = más alta, 10 = más baja)

# ─────────────────────────────────────────
#  Configuración de memoria
# ─────────────────────────────────────────
TOTAL_FRAMES       = 8       # Total de marcos de página físicos disponibles
PAGE_SIZE          = 4       # Tamaño de página en KB (simbólico)
MAX_PAGES_PER_PROC = 6       # Máximo de páginas que puede tener un proceso

# ─────────────────────────────────────────
#  Configuración de archivos simulados
# ─────────────────────────────────────────
SIMULATED_FILES   = ["archivo_A.txt", "archivo_B.txt", "archivo_C.txt",
                     "archivo_D.txt", "archivo_E.txt"]
MAX_FILE_THREADS  = 5        # Procesos que pueden acceder concurrentemente
WRITE_DELAY_MS    = 200      # Retardo simulado de escritura (ms)
READ_DELAY_MS     = 100      # Retardo simulado de lectura (ms)

# ─────────────────────────────────────────
#  Configuración de la interfaz
# ─────────────────────────────────────────
APP_TITLE       = "Simulador de Sistema Operativo – UPTC SO 2026-1"
APP_WIDTH       = 1200
APP_HEIGHT      = 780
THEME_BG        = "#1e1e2e"   # Fondo principal (oscuro)
THEME_FG        = "#cdd6f4"   # Texto principal
THEME_ACCENT    = "#89b4fa"   # Azul acento
THEME_SUCCESS   = "#a6e3a1"   # Verde éxito
THEME_WARNING   = "#f9e2af"   # Amarillo advertencia
THEME_ERROR     = "#f38ba8"   # Rojo error
THEME_SURFACE   = "#313244"   # Superficie de tarjetas
THEME_BORDER    = "#45475a"   # Bordes

# Colores para la gráfica Gantt (un color por proceso)
GANTT_COLORS = [
    "#89b4fa", "#a6e3a1", "#f9e2af", "#f38ba8",
    "#cba6f7", "#fab387", "#94e2d5", "#eba0ac",
    "#b4befe", "#a6adc8", "#89dceb", "#74c7ec",
]

# ─────────────────────────────────────────
#  Rutas de exportación
# ─────────────────────────────────────────
EXPORT_DIR = "exports"
LOG_DIR    = "logs"
