"""
Algoritmo de Planificación SJF – Shortest Job First (No Apropiativo).

Selecciona el proceso con el menor tiempo de ráfaga (burst time)
entre todos los procesos que ya llegaron y están en la cola Ready.

Características:
  - No apropiativo (non-preemptive)
  - Óptimo en tiempo de espera promedio para un conjunto dado de procesos
  - Puede causar inanición (starvation) en procesos largos
  - Difícil de implementar en sistemas reales (el burst no se conoce de antemano)
"""

from typing import List
import copy

from models.process import Process, ProcessState
from core.scheduler.base_scheduler import BaseScheduler


class SJFScheduler(BaseScheduler):
    """
    Planificador Shortest Job First (No Apropiativo).

    En cada punto de decisión se elige el proceso con menor burst_time
    entre los que ya han llegado al sistema.
    """

    def __init__(self):
        super().__init__(name="SJF – Shortest Job First")

    def run(self, processes: List[Process]) -> List[Process]:
        """
        Ejecuta la simulación SJF no apropiativa.

        Algoritmo:
          1. Ordenar procesos por tiempo de llegada.
          2. Mantener un pool de procesos listos (arrived).
          3. En cada decisión: elegir el de menor burst_time del pool.
          4. Ejecutar completamente ese proceso (no hay desalojo).
          5. Actualizar métricas y continuar.

        Returns:
            Procesos con métricas calculadas.
        """
        self.reset()

        procs = [copy.copy(p) for p in processes]
        for p in procs:
            p.reset()

        procs.sort(key=lambda p: p.arrival_time)

        completed  = []
        self.time  = 0
        remaining  = list(procs)  # Procesos que aún no terminaron

        while remaining:
            # Procesos que ya llegaron y están listos
            arrived = [p for p in remaining if p.arrival_time <= self.time]

            if not arrived:
                # CPU idle: saltar al próximo proceso que llega
                self.time = min(p.arrival_time for p in remaining)
                continue

            # Seleccionar el proceso con menor burst_time (SJF)
            current = min(arrived, key=lambda p: p.burst_time)
            remaining.remove(current)

            # Primera ejecución
            if current.response_time == -1:
                current.response_time = self.time - current.arrival_time
            current.start_time = self.time
            current.state      = ProcessState.RUNNING

            start_t = self.time

            # Ejecutar completamente (no apropiativo)
            self.time             += current.burst_time
            current.remaining_time = 0

            # Registrar en Gantt
            self._record_gantt(current.pid, current.name, start_t, self.time)
            current.record_gantt(start_t, self.time)

            # Calcular métricas del proceso
            current.state           = ProcessState.TERMINATED
            current.completion_time = self.time
            current.turnaround_time = self.time - current.arrival_time
            current.waiting_time    = current.turnaround_time - current.burst_time
            self.context_switches  += 1

            completed.append(current)

        self._calculate_metrics(completed)
        return completed
