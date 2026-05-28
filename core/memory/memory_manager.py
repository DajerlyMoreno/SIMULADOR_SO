"""
Gestor de Memoria – Paginación por Demanda.

Simula el sistema de memoria virtual con paginación por demanda:
  - Las páginas se cargan en RAM solo cuando se necesitan (demand paging).
  - Si no hay marcos libres, se aplica el algoritmo de reemplazo elegido.
  - Se registran todos los fallos de página (page faults).
"""

from typing import List, Dict, Tuple, Any
import random

from models.process    import Process
from models.memory_page import Page, Frame, PageFaultEvent
from core.memory.page_replacement import FIFOReplacement, LRUReplacement
from config.settings   import TOTAL_FRAMES, MAX_PAGES_PER_PROC


class MemoryManager:
    """
    Gestor de Memoria con Paginación por Demanda.

    Mantiene la tabla de páginas por proceso y delega el reemplazo
    al algoritmo seleccionado (FIFO o LRU).
    """

    def __init__(self, num_frames: int = TOTAL_FRAMES, algorithm: str = "LRU"):
        """
        Inicializa el gestor.

        Args:
            num_frames : Número de marcos físicos de RAM.
            algorithm  : Algoritmo de reemplazo ("FIFO" o "LRU").
        """
        self.num_frames  = num_frames
        self.algorithm   = algorithm.upper()
        self._build_replacer()

        # Tabla de páginas: {pid: [Page, Page, ...]}
        self.page_table  : Dict[int, List[Page]] = {}
        self.time        : int                   = 0
        self.access_log  : List[Dict]            = []   # Log de todos los accesos

    def _build_replacer(self):
        """Instancia el algoritmo de reemplazo elegido."""
        if self.algorithm == "FIFO":
            self.replacer = FIFOReplacement(self.num_frames)
        else:
            self.algorithm = "LRU"
            self.replacer  = LRUReplacement(self.num_frames)

    # ── Registro y simulación ─────────────────────────────────────────────

    def register_process(self, process: Process):
        """
        Registra un proceso y crea su tabla de páginas.

        Las páginas comienzan en disco (not loaded); se cargan
        bajo demanda cuando el proceso las referencia.
        """
        pages = [
            Page(page_number=i, pid=process.pid)
            for i in range(process.memory_pages)
        ]
        self.page_table[process.pid] = pages

    def access_page(self, pid: int, page_num: int) -> Tuple[bool, Any]:
        """
        Simula el acceso a una página por un proceso.

        Si la página no está en RAM → Page Fault → reemplazo si necesario.

        Args:
            pid     : PID del proceso solicitante.
            page_num: Número de página que se accede.

        Returns:
            (hit, event) – hit=True si page hit, event=PageFaultEvent o None.
        """
        self.time += 1
        hit, event = self.replacer.access_page(pid, page_num, self.time)

        # Actualizar tabla de páginas interna
        if pid in self.page_table and page_num < len(self.page_table[pid]):
            page = self.page_table[pid][page_num]
            if hit:
                page.access(self.time)
            else:
                # Encontrar el marco donde se cargó
                for frame in self.replacer.frames:
                    if frame.pid == pid and frame.page_number == page_num:
                        page.load_into_frame(frame.frame_number, self.time)
                        break

        # Registrar el acceso en el log
        self.access_log.append({
            "tiempo"   : self.time,
            "pid"      : pid,
            "pagina"   : page_num,
            "resultado": "HIT" if hit else "FAULT",
            "algoritmo": self.algorithm,
        })
        return hit, event

    def simulate_process_accesses(self, process: Process,
                                   access_pattern: List[int] = None) -> Dict:
        """
        Simula una serie de accesos a páginas para un proceso.

        Args:
            process       : Proceso simulado.
            access_pattern: Lista de números de página a acceder.
                            Si None, genera un patrón aleatorio.

        Returns:
            Diccionario con métricas de la simulación del proceso.
        """
        self.register_process(process)

        if access_pattern is None:
            # Generar patrón de accesos aleatorio con localidad de referencia
            access_pattern = self._generate_access_pattern(process.memory_pages)

        hits   = 0
        faults = 0
        events = []

        for page_num in access_pattern:
            if page_num < process.memory_pages:
                hit, event = self.access_page(process.pid, page_num)
                if hit:
                    hits += 1
                else:
                    faults += 1
                    if event:
                        events.append(event)

        total = hits + faults
        return {
            "pid"         : process.pid,
            "nombre"      : process.name,
            "paginas"     : process.memory_pages,
            "accesos"     : total,
            "page_hits"   : hits,
            "page_faults" : faults,
            "hit_ratio"   : round(hits / total, 4) if total > 0 else 0,
            "eventos"     : events,
            "patron"      : access_pattern,
        }

    def _generate_access_pattern(self, num_pages: int, accesses: int = 15) -> List[int]:
        """
        Genera un patrón de accesos con localidad de referencia.

        Los sistemas reales muestran localidad: los procesos tienden a acceder
        repetidamente a un conjunto pequeño de páginas durante períodos cortos.
        """
        if num_pages == 0:
            return []

        pattern = []
        current = random.randint(0, num_pages - 1)

        for _ in range(accesses):
            # 70% probabilidad de acceder a página cercana (localidad)
            if random.random() < 0.7:
                delta   = random.randint(-1, 1)
                current = max(0, min(num_pages - 1, current + delta))
            else:
                # 30% acceso aleatorio (salto)
                current = random.randint(0, num_pages - 1)
            pattern.append(current)

        return pattern

    # ── Métricas y reportes ───────────────────────────────────────────────

    def get_global_stats(self) -> Dict:
        """Retorna estadísticas globales de memoria."""
        return {
            "algoritmo"    : self.algorithm,
            "num_marcos"   : self.num_frames,
            "page_hits"    : self.replacer.page_hits,
            "page_faults"  : self.replacer.page_faults,
            "hit_ratio"    : self.replacer.get_hit_ratio(),
            "fault_ratio"  : self.replacer.get_fault_ratio(),
            "total_accesos": self.replacer.page_hits + self.replacer.page_faults,
        }

    def get_frame_states(self) -> List[Frame]:
        """Retorna el estado actual de todos los marcos."""
        return self.replacer.frames

    def get_page_fault_events(self) -> List[PageFaultEvent]:
        """Retorna todos los eventos de fallo de página."""
        return self.replacer.events

    def get_history(self) -> List[List[str]]:
        """Retorna el historial de snapshots de marcos."""
        return self.replacer.history

    def reset(self, algorithm: str = None):
        """Reinicia el gestor completo."""
        if algorithm:
            self.algorithm = algorithm.upper()
        self.page_table = {}
        self.time       = 0
        self.access_log = []
        self._build_replacer()
