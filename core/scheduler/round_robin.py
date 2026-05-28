"""
Algoritmo de Planificación Round Robin (RR).

Asigna a cada proceso un quantum de tiempo fijo (time slice).
Si el proceso no termina en ese quantum, regresa al final de la cola.

Características:
  - Apropiativo (preemptive)
  - Justo: todos los procesos reciben el mismo tiempo de CPU
  - Tiempo de respuesta predecible
  - Adecuado para sistemas de tiempo compartido
"""

from collections import deque
from typing import List
import copy

from models.process import Process, ProcessState
from core.scheduler.base_scheduler import BaseScheduler


class RoundRobinScheduler(BaseScheduler):
    """
    Planificador Round Robin.

    Parámetros:
        quantum: Número de unidades de tiempo que cada proceso puede
                 usar la CPU antes de ser desalojado.
    """

    def __init__(self, quantum: int = 2):
        super().__init__(name=f"Round Robin (q={quantum})")
        self.quantum = quantum

    def run(self, processes: List[Process]) -> List[Process]:
        """
        Ejecuta la simulación Round Robin.

        Algoritmo:
          1. Ordenar procesos por tiempo de llegada.
          2. Agregar procesos a la cola Ready conforme llegan.
          3. Tomar el primer proceso de la cola.
          4. Ejecutarlo por min(quantum, remaining_time) unidades.
          5. Si terminó → marcar como Terminado.
             Si no → reinsertar al final de la cola.
          6. Repetir hasta vaciar la cola.

        Returns:
            Procesos con métricas de tiempo calculadas.
        """
        self.reset()

        # Trabajar con copias para no modificar los originales
        procs = [copy.copy(p) for p in processes]
        for p in procs:
            p.reset()

        # Ordenar por tiempo de llegada
        procs.sort(key=lambda p: p.arrival_time)

        ready_queue  = deque()
        completed    = []
        self.time    = 0
        idx          = 0   # Puntero a los procesos pendientes de llegar

        # Agregar procesos que llegan en t=0
        while idx < len(procs) and procs[idx].arrival_time <= self.time:
            procs[idx].state = ProcessState.READY
            ready_queue.append(procs[idx])
            idx += 1

        while ready_queue or idx < len(procs):
            if not ready_queue:
                # CPU idle: avanzar al próximo proceso que llega
                self.time = procs[idx].arrival_time
                while idx < len(procs) and procs[idx].arrival_time <= self.time:
                    procs[idx].state = ProcessState.READY
                    ready_queue.append(procs[idx])
                    idx += 1
                continue

            current = ready_queue.popleft()

            # Primera vez que el proceso obtiene CPU
            if current.response_time == -1:
                current.response_time = self.time - current.arrival_time
            if current.start_time == -1:
                current.start_time = self.time

            current.state = ProcessState.RUNNING

            # Determinar cuánto tiempo ejecuta en este ciclo
            exec_time = min(self.quantum, current.remaining_time)
            start_t   = self.time

            self.time           += exec_time
            current.remaining_time -= exec_time

            # Registrar en Gantt
            self._record_gantt(current.pid, current.name, start_t, self.time)
            current.record_gantt(start_t, self.time)

            # Agregar procesos que llegaron durante esta ejecución
            while idx < len(procs) and procs[idx].arrival_time <= self.time:
                procs[idx].state = ProcessState.READY
                ready_queue.append(procs[idx])
                idx += 1

            if current.is_complete():
                # Proceso terminado
                current.state           = ProcessState.TERMINATED
                current.completion_time = self.time
                current.turnaround_time = self.time - current.arrival_time
                current.waiting_time    = current.turnaround_time - current.burst_time
                completed.append(current)
                self.context_switches  += 1
            else:
                # Proceso no terminó: vuelve a la cola (apropiativo)
                current.state = ProcessState.READY
                ready_queue.append(current)
                self.context_switches += 1

        self._calculate_metrics(completed)
        return completed
