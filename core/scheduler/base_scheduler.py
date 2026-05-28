"""
Clase base abstracta para todos los algoritmos de planificación.

Define la interfaz común que deben implementar Round Robin, SJF y Prioridad.
Patrón: Template Method – la lógica común está aquí, el algoritmo en subclases.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from models.process import Process, ProcessState


class BaseScheduler(ABC):
    """
    Planificador abstracto base.

    Todos los algoritmos de planificación heredan de esta clase
    e implementan el método `run()`.
    """

    def __init__(self, name: str):
        self.name        = name          # Nombre del algoritmo
        self.time        = 0             # Reloj del sistema (unidades)
        self.gantt       : List[Dict]  = []  # Historial para Gantt
        self.metrics     : Dict        = {}  # Métricas finales
        self.context_switches: int     = 0   # Cambios de contexto

    # ── Método principal (a implementar en cada subclase) ─────────────────

    @abstractmethod
    def run(self, processes: List[Process]) -> List[Process]:
        """
        Ejecuta el algoritmo de planificación.

        Args:
            processes: Lista de procesos a planificar.

        Returns:
            Lista de procesos con métricas calculadas.
        """
        ...

    # ── Métodos de apoyo compartidos ──────────────────────────────────────

    def reset(self):
        """Reinicia el estado interno del planificador."""
        self.time             = 0
        self.gantt            = []
        self.metrics          = {}
        self.context_switches = 0

    def _record_gantt(self, pid: int, name: str, start: int, end: int):
        """Registra un intervalo en el diagrama de Gantt."""
        self.gantt.append({
            "pid"  : pid,
            "name" : name,
            "start": start,
            "end"  : end,
        })

    def _calculate_metrics(self, processes: List[Process]) -> Dict[str, Any]:
        """
        Calcula métricas globales de rendimiento del planificador.

        Métricas calculadas:
          - Tiempo de espera promedio
          - Turnaround time promedio
          - Tiempo de respuesta promedio
          - Throughput (procesos / unidad de tiempo total)
          - Utilización de CPU
        """
        n = len(processes)
        if n == 0:
            return {}

        total_wait        = sum(p.waiting_time    for p in processes)
        total_turnaround  = sum(p.turnaround_time for p in processes)
        total_response    = sum(p.response_time   for p in processes
                                if p.response_time >= 0)
        total_burst       = sum(p.burst_time      for p in processes)
        makespan          = max(p.completion_time for p in processes) if processes else 0

        self.metrics = {
            "algoritmo"             : self.name,
            "num_procesos"          : n,
            "makespan"              : makespan,
            "espera_promedio"       : round(total_wait / n, 2),
            "turnaround_promedio"   : round(total_turnaround / n, 2),
            "respuesta_promedio"    : round(total_response / n, 2) if n > 0 else 0,
            "throughput"            : round(n / makespan, 4) if makespan > 0 else 0,
            "utilizacion_cpu"       : round((total_burst / makespan) * 100, 2) if makespan > 0 else 0,
            "cambios_contexto"      : self.context_switches,
        }
        return self.metrics

    def get_gantt(self) -> List[Dict]:
        """Retorna el historial del diagrama de Gantt."""
        return self.gantt

    def get_metrics(self) -> Dict:
        """Retorna las métricas calculadas."""
        return self.metrics

    def __repr__(self) -> str:
        return f"Scheduler({self.name})"
