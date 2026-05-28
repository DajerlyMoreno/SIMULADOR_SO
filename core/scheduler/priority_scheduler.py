"""
Algoritmo de Planificación por Prioridad (Apropiativo).

Selecciona siempre el proceso de mayor prioridad en la cola Ready.
Si llega un proceso con mayor prioridad, desaloja al actual.

Convención: prioridad 1 = más alta, 10 = más baja.

Características:
  - Apropiativo (preemptive)
  - Responde inmediatamente a procesos críticos
  - Puede causar inanición: se mitiga con envejecimiento (aging)
"""

from typing import List
import copy

from models.process import Process, ProcessState
from core.scheduler.base_scheduler import BaseScheduler


class PriorityScheduler(BaseScheduler):
    """
    Planificador por Prioridad Apropiativo con Envejecimiento (Aging).

    El envejecimiento incrementa la prioridad de los procesos que
    llevan mucho tiempo esperando, evitando la inanición.

    Parámetros:
        aging_threshold : Unidades de tiempo de espera antes de mejorar prioridad.
    """

    def __init__(self, aging_threshold: int = 5):
        super().__init__(name="Prioridad Apropiativa (con Aging)")
        self.aging_threshold = aging_threshold

    def run(self, processes: List[Process]) -> List[Process]:
        """
        Ejecuta la simulación por prioridad apropiativa.

        Algoritmo (simulado unidad por unidad):
          1. En cada unidad de tiempo, construir la cola de procesos listos.
          2. Elegir el proceso con MENOR número de prioridad (= más urgente).
          3. Si el proceso actual tiene menor prioridad que el nuevo candidato,
             desalojar al actual (preemption).
          4. Aplicar aging: si un proceso esperó ≥ aging_threshold, mejorar prioridad.
          5. Continuar hasta que todos terminen.

        Returns:
            Procesos con métricas calculadas.
        """
        self.reset()

        procs = [copy.copy(p) for p in processes]
        for p in procs:
            p.reset()
            p._effective_priority = p.priority   # Prioridad dinámica (aging)
            p._wait_streak        = 0             # Tiempo consecutivo esperando

        procs.sort(key=lambda p: p.arrival_time)

        completed       = []
        current_process = None
        self.time       = 0
        max_time        = sum(p.burst_time for p in procs) + max(p.arrival_time for p in procs) + 10

        gantt_start = 0  # Inicio del bloque Gantt actual

        while len(completed) < len(procs) and self.time < max_time:
            # Procesos disponibles (llegaron y no terminaron)
            ready = [p for p in procs
                     if p.arrival_time <= self.time
                     and not p.is_complete()
                     and p.state != ProcessState.TERMINATED]

            if not ready:
                self.time += 1
                continue

            # Aplicar aging: mejorar prioridad de los que esperan mucho
            for p in ready:
                if p != current_process:
                    p._wait_streak += 1
                    if p._wait_streak >= self.aging_threshold:
                        p._effective_priority = max(1, p._effective_priority - 1)
                        p._wait_streak = 0
                else:
                    p._wait_streak = 0

            # Elegir el proceso de mayor prioridad efectiva (menor número)
            best = min(ready, key=lambda p: (p._effective_priority, p.arrival_time))

            # ¿Hay preempción? (cambia el proceso activo)
            if current_process is not None and best.pid != current_process.pid:
                # Registrar el bloque Gantt del proceso saliente
                if self.time > gantt_start:
                    self._record_gantt(current_process.pid, current_process.name,
                                       gantt_start, self.time)
                    current_process.record_gantt(gantt_start, self.time)
                current_process.state = ProcessState.READY
                self.context_switches += 1
                gantt_start = self.time

            if current_process is None or best.pid != current_process.pid:
                current_process = best
                gantt_start     = self.time
                if current_process.response_time == -1:
                    current_process.response_time = self.time - current_process.arrival_time
                if current_process.start_time == -1:
                    current_process.start_time = self.time

            current_process.state          = ProcessState.RUNNING
            current_process.remaining_time -= 1
            self.time                      += 1

            # ¿Terminó?
            if current_process.is_complete():
                self._record_gantt(current_process.pid, current_process.name,
                                   gantt_start, self.time)
                current_process.record_gantt(gantt_start, self.time)

                current_process.state           = ProcessState.TERMINATED
                current_process.completion_time = self.time
                current_process.turnaround_time = self.time - current_process.arrival_time
                current_process.waiting_time    = (current_process.turnaround_time
                                                    - current_process.burst_time)
                completed.append(current_process)
                self.context_switches += 1
                current_process = None
                gantt_start     = self.time

        # Calcular tiempo de espera para procesos en la cola Ready
        for p in procs:
            if p not in completed and p.state != ProcessState.TERMINATED:
                p.waiting_time = 0

        self._calculate_metrics(completed)
        return completed
