"""
Modelos de memoria: Página y Marco de Página.

Representan las estructuras fundamentales del sistema de paginación:
  - Page  : Unidad lógica de memoria perteneciente a un proceso.
  - Frame : Marco físico de memoria RAM.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Page:
    """
    Página lógica de un proceso.

    Atributos:
        page_number : Número de página dentro del espacio del proceso.
        pid         : Identificador del proceso dueño.
        loaded      : True si la página está en un marco físico (RAM).
        frame_number: Marco donde se aloja la página (None si está en disco).
        access_count: Número de veces que fue accedida (para LRU).
        last_used   : Instante del último acceso (para LRU).
    """
    page_number  : int
    pid          : int
    loaded       : bool          = False
    frame_number : Optional[int] = None
    access_count : int           = 0
    last_used    : int           = 0   # Tiempo del último acceso

    def load_into_frame(self, frame_number: int, current_time: int):
        """Carga la página en un marco físico de RAM."""
        self.frame_number = frame_number
        self.loaded       = True
        self.last_used    = current_time
        self.access_count += 1

    def evict(self):
        """Saca la página de la RAM (page fault → swap)."""
        self.frame_number = None
        self.loaded       = False

    def access(self, current_time: int):
        """Registra un acceso a la página (actualiza LRU)."""
        self.last_used    = current_time
        self.access_count += 1

    def __repr__(self) -> str:
        estado = f"Marco {self.frame_number}" if self.loaded else "En disco"
        return f"Page(pid={self.pid}, pág={self.page_number}, {estado})"


@dataclass
class Frame:
    """
    Marco físico de memoria RAM.

    Atributos:
        frame_number : Identificador del marco.
        pid          : PID del proceso que ocupa el marco (None = libre).
        page_number  : Número de página alojada (None = libre).
        loaded_at    : Instante en que se cargó la página (para FIFO/LRU).
    """
    frame_number : int
    pid          : Optional[int] = None
    page_number  : Optional[int] = None
    loaded_at    : int           = 0

    @property
    def is_free(self) -> bool:
        """Retorna True si el marco está disponible."""
        return self.pid is None

    def allocate(self, pid: int, page_number: int, current_time: int):
        """Asigna el marco a una página de un proceso."""
        self.pid         = pid
        self.page_number = page_number
        self.loaded_at   = current_time

    def free(self):
        """Libera el marco."""
        self.pid         = None
        self.page_number = None
        self.loaded_at   = 0

    def __repr__(self) -> str:
        if self.is_free:
            return f"Frame({self.frame_number}: LIBRE)"
        return f"Frame({self.frame_number}: PID={self.pid}, Pág={self.page_number})"


@dataclass
class PageFaultEvent:
    """Registra un evento de fallo de página para métricas y reporte."""
    time         : int
    pid          : int
    page_number  : int
    evicted_pid  : Optional[int] = None
    evicted_page : Optional[int] = None
    algorithm    : str           = ""

    def __repr__(self) -> str:
        ev = (f"→ expulsó PID={self.evicted_pid}/Pág={self.evicted_page}"
              if self.evicted_pid is not None else "→ marco libre")
        return f"[t={self.time}] Page Fault PID={self.pid}/Pág={self.page_number} {ev}"
