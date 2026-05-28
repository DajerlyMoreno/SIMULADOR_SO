"""
Modelo de Proceso (PCB - Process Control Block).

Representa la estructura de datos que el sistema operativo usa
para administrar cada proceso en ejecución.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class ProcessState(Enum):
    """Estados posibles de un proceso según el modelo clásico de SO."""
    NEW        = "Nuevo"
    READY      = "Listo"
    RUNNING    = "Ejecutando"
    WAITING    = "Esperando"
    TERMINATED = "Terminado"


@dataclass
class Process:
    """
    Bloque de Control de Proceso (PCB).

    Contiene toda la información que el planificador necesita para
    gestionar la ejecución de un proceso.

    Atributos:
        pid          : Identificador único del proceso.
        name         : Nombre descriptivo del proceso.
        priority     : Nivel de prioridad (1 = máxima, 10 = mínima).
        burst_time   : Tiempo de CPU total requerido (unidades de tiempo).
        arrival_time : Instante en que el proceso llega a la cola Ready.
        memory_pages : Número de páginas de memoria requeridas.
        accesses_files: True si el proceso realiza E/S de archivos.
    """
    pid           : int
    name          : str
    priority      : int          # 1 (alta) – 10 (baja)
    burst_time    : int          # Tiempo de ráfaga total
    arrival_time  : int          # Tiempo de llegada al sistema
    memory_pages  : int          # Páginas de memoria que necesita
    accesses_files: bool = False # ¿Accede a archivos?

    # ── Campos calculados en tiempo de ejecución ──────────────────────────
    state            : ProcessState = field(default=ProcessState.NEW,  compare=False)
    remaining_time   : int          = field(default=0,                 compare=False)
    waiting_time     : int          = field(default=0,                 compare=False)
    turnaround_time  : int          = field(default=0,                 compare=False)
    completion_time  : int          = field(default=0,                 compare=False)
    response_time    : int          = field(default=-1,                compare=False)
    start_time       : int          = field(default=-1,                compare=False)

    # Historial de ejecución para el diagrama de Gantt
    gantt_history: List[tuple] = field(default_factory=list,          compare=False)

    def __post_init__(self):
        """Inicializa el tiempo restante igual al burst total."""
        self.remaining_time = self.burst_time

    # ── Métodos de estado ────────────────────────────────────────────────

    def is_complete(self) -> bool:
        """Retorna True si el proceso terminó de ejecutarse."""
        return self.remaining_time <= 0

    def reset(self):
        """Restaura el proceso a su estado inicial (para re-simular)."""
        self.remaining_time  = self.burst_time
        self.state           = ProcessState.NEW
        self.waiting_time    = 0
        self.turnaround_time = 0
        self.completion_time = 0
        self.response_time   = -1
        self.start_time      = -1
        self.gantt_history   = []

    def record_gantt(self, start: int, end: int):
        """Registra un intervalo de ejecución para el diagrama de Gantt."""
        self.gantt_history.append((start, end))

    # ── Representación ────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return (f"Process(pid={self.pid}, name='{self.name}', "
                f"burst={self.burst_time}, priority={self.priority}, "
                f"state={self.state.value})")

    def to_dict(self) -> dict:
        """Serializa el proceso a diccionario (para exportar métricas)."""
        return {
            "PID"             : self.pid,
            "Nombre"          : self.name,
            "Prioridad"       : self.priority,
            "Burst Time"      : self.burst_time,
            "Llegada"         : self.arrival_time,
            "Páginas"         : self.memory_pages,
            "Accede Archivos" : self.accesses_files,
            "Tiempo Espera"   : self.waiting_time,
            "Turnaround"      : self.turnaround_time,
            "Finalización"    : self.completion_time,
            "Respuesta"       : self.response_time,
            "Estado"          : self.state.value,
        }
