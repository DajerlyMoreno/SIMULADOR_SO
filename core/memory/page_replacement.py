"""
Algoritmos de Reemplazo de Páginas.

Implementa FIFO (First In, First Out) y LRU (Least Recently Used).
Estos algoritmos determinan cuál página expulsar de la RAM cuando
todos los marcos están ocupados y se produce un Page Fault.
"""

from collections import deque, OrderedDict
from typing import List, Tuple, Optional
from models.memory_page import Frame, Page, PageFaultEvent


class FIFOReplacement:
    """
    Algoritmo FIFO – First In, First Out.

    Reemplaza la página que lleva más tiempo cargada en memoria.
    Simple pero puede sufrir la Anomalía de Bélády.
    """

    def __init__(self, num_frames: int):
        self.num_frames = num_frames
        self.frames     : List[Frame]       = [Frame(i) for i in range(num_frames)]
        self.queue      : deque             = deque()   # Orden de carga (FIFO)
        self.page_faults: int               = 0
        self.page_hits  : int               = 0
        self.events     : List[PageFaultEvent] = []
        self.history    : List[List[str]]   = []        # Snapshot de marcos por acceso

    def access_page(self, pid: int, page_num: int, current_time: int
                    ) -> Tuple[bool, Optional[PageFaultEvent]]:
        """
        Simula el acceso a una página.

        Args:
            pid         : PID del proceso.
            page_num    : Número de página accedida.
            current_time: Tiempo actual de simulación.

        Returns:
            (hit, event) – hit=True si la página ya estaba en RAM.
        """
        # Buscar si la página ya está en algún marco (HIT)
        for frame in self.frames:
            if frame.pid == pid and frame.page_number == page_num:
                self.page_hits += 1
                self._snapshot()
                return True, None   # Page Hit

        # PAGE FAULT – la página no está en RAM
        self.page_faults += 1
        evicted_pid  = None
        evicted_page = None

        # Buscar un marco libre
        free_frame = next((f for f in self.frames if f.is_free), None)

        if free_frame:
            # Marco disponible: cargar sin expulsar
            free_frame.allocate(pid, page_num, current_time)
            self.queue.append(free_frame.frame_number)
        else:
            # Todos los marcos ocupados: expulsar el más antiguo (FIFO)
            oldest_frame_num = self.queue.popleft()
            victim           = self.frames[oldest_frame_num]
            evicted_pid      = victim.pid
            evicted_page     = victim.page_number

            victim.free()
            victim.allocate(pid, page_num, current_time)
            self.queue.append(oldest_frame_num)

        event = PageFaultEvent(
            time         = current_time,
            pid          = pid,
            page_number  = page_num,
            evicted_pid  = evicted_pid,
            evicted_page = evicted_page,
            algorithm    = "FIFO",
        )
        self.events.append(event)
        self._snapshot()
        return False, event

    def _snapshot(self):
        """Guarda el estado actual de los marcos para visualización."""
        snap = []
        for f in self.frames:
            if f.is_free:
                snap.append("Libre")
            else:
                snap.append(f"P{f.pid}/p{f.page_number}")
        self.history.append(snap)

    def reset(self):
        """Reinicia el estado de los marcos."""
        self.frames      = [Frame(i) for i in range(self.num_frames)]
        self.queue       = deque()
        self.page_faults = 0
        self.page_hits   = 0
        self.events      = []
        self.history     = []

    def get_hit_ratio(self) -> float:
        total = self.page_hits + self.page_faults
        return round(self.page_hits / total, 4) if total > 0 else 0.0

    def get_fault_ratio(self) -> float:
        total = self.page_hits + self.page_faults
        return round(self.page_faults / total, 4) if total > 0 else 0.0

    def frames_snapshot(self) -> List[str]:
        """Estado actual legible de los marcos."""
        return [f"Marco {f.frame_number}: {'Libre' if f.is_free else f'PID={f.pid} Pág={f.page_number}'}"
                for f in self.frames]


class LRUReplacement:
    """
    Algoritmo LRU – Least Recently Used.

    Reemplaza la página que no ha sido accedida por más tiempo.
    Aproxima el comportamiento óptimo; más eficiente que FIFO.
    """

    def __init__(self, num_frames: int):
        self.num_frames  = num_frames
        self.frames      : List[Frame]       = [Frame(i) for i in range(num_frames)]
        self.lru_tracker : OrderedDict       = OrderedDict()  # {(pid,page): frame_num}
        self.page_faults : int               = 0
        self.page_hits   : int               = 0
        self.events      : List[PageFaultEvent] = []
        self.history     : List[List[str]]   = []

    def access_page(self, pid: int, page_num: int, current_time: int
                    ) -> Tuple[bool, Optional[PageFaultEvent]]:
        """
        Simula el acceso a una página con política LRU.

        Args:
            pid         : PID del proceso.
            page_num    : Número de página.
            current_time: Tiempo actual.

        Returns:
            (hit, event) – hit=True si fue page hit.
        """
        key = (pid, page_num)

        # PAGE HIT: la página ya está en RAM
        if key in self.lru_tracker:
            self.page_hits += 1
            # Mover al final del OrderedDict (más recientemente usado)
            self.lru_tracker.move_to_end(key)
            self._snapshot()
            return True, None

        # PAGE FAULT
        self.page_faults += 1
        evicted_pid  = None
        evicted_page = None

        # Buscar marco libre
        free_frame = next((f for f in self.frames if f.is_free), None)

        if free_frame:
            free_frame.allocate(pid, page_num, current_time)
            self.lru_tracker[key] = free_frame.frame_number
        else:
            # Expulsar la página menos recientemente usada (primer elemento)
            lru_key, lru_frame_num = next(iter(self.lru_tracker.items()))
            del self.lru_tracker[lru_key]

            victim       = self.frames[lru_frame_num]
            evicted_pid  = victim.pid
            evicted_page = victim.page_number

            victim.free()
            victim.allocate(pid, page_num, current_time)
            self.lru_tracker[key] = lru_frame_num

        event = PageFaultEvent(
            time         = current_time,
            pid          = pid,
            page_number  = page_num,
            evicted_pid  = evicted_pid,
            evicted_page = evicted_page,
            algorithm    = "LRU",
        )
        self.events.append(event)
        self._snapshot()
        return False, event

    def _snapshot(self):
        snap = []
        for f in self.frames:
            if f.is_free:
                snap.append("Libre")
            else:
                snap.append(f"P{f.pid}/p{f.page_number}")
        self.history.append(snap)

    def reset(self):
        self.frames      = [Frame(i) for i in range(self.num_frames)]
        self.lru_tracker = OrderedDict()
        self.page_faults = 0
        self.page_hits   = 0
        self.events      = []
        self.history     = []

    def get_hit_ratio(self) -> float:
        total = self.page_hits + self.page_faults
        return round(self.page_hits / total, 4) if total > 0 else 0.0

    def get_fault_ratio(self) -> float:
        total = self.page_hits + self.page_faults
        return round(self.page_faults / total, 4) if total > 0 else 0.0

    def frames_snapshot(self) -> List[str]:
        return [f"Marco {f.frame_number}: {'Libre' if f.is_free else f'PID={f.pid} Pág={f.page_number}'}"
                for f in self.frames]
