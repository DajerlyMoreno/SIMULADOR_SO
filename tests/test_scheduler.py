"""
Pruebas unitarias para los algoritmos de planificación.

Casos de prueba:
  1. Round Robin con quantum 2
  2. SJF con llegadas distintas
  3. Prioridad con procesos de igual prioridad
  4. Verificación de métricas (turnaround, waiting time)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from models.process                    import Process, ProcessState
from core.scheduler.round_robin        import RoundRobinScheduler
from core.scheduler.sjf                import SJFScheduler
from core.scheduler.priority_scheduler import PriorityScheduler


def make_procs():
    """Crea un conjunto fijo de procesos para pruebas reproducibles."""
    return [
        Process(pid=1, name="P1", priority=2, burst_time=5,
                arrival_time=0, memory_pages=2),
        Process(pid=2, name="P2", priority=1, burst_time=3,
                arrival_time=1, memory_pages=1),
        Process(pid=3, name="P3", priority=3, burst_time=4,
                arrival_time=2, memory_pages=3),
        Process(pid=4, name="P4", priority=5, burst_time=2,
                arrival_time=0, memory_pages=1),
    ]


class TestRoundRobin(unittest.TestCase):

    def test_all_processes_complete(self):
        """Todos los procesos deben terminar."""
        sched  = RoundRobinScheduler(quantum=2)
        result = sched.run(make_procs())
        self.assertEqual(len(result), 4)
        for p in result:
            self.assertEqual(p.state, ProcessState.TERMINATED)

    def test_waiting_time_non_negative(self):
        """El tiempo de espera no puede ser negativo."""
        sched  = RoundRobinScheduler(quantum=2)
        result = sched.run(make_procs())
        for p in result:
            self.assertGreaterEqual(p.waiting_time, 0,
                f"P{p.pid} tiene waiting_time={p.waiting_time} (debe ser ≥ 0)")

    def test_turnaround_equals_burst_plus_wait(self):
        """Turnaround = burst_time + waiting_time."""
        sched  = RoundRobinScheduler(quantum=2)
        result = sched.run(make_procs())
        for p in result:
            self.assertEqual(p.turnaround_time, p.burst_time + p.waiting_time,
                f"P{p.pid}: turnaround={p.turnaround_time} ≠ burst+wait="
                f"{p.burst_time + p.waiting_time}")

    def test_gantt_covers_all_bursts(self):
        """La suma de los intervalos Gantt por proceso debe igualar su burst."""
        sched  = RoundRobinScheduler(quantum=2)
        result = sched.run(make_procs())
        for p in result:
            gantt_time = sum(end - start for start, end in p.gantt_history)
            self.assertEqual(gantt_time, p.burst_time,
                f"P{p.pid}: tiempo Gantt={gantt_time} ≠ burst={p.burst_time}")

    def test_metrics_calculated(self):
        """Las métricas globales deben estar calculadas."""
        sched  = RoundRobinScheduler(quantum=2)
        sched.run(make_procs())
        m = sched.get_metrics()
        self.assertIn("espera_promedio",     m)
        self.assertIn("turnaround_promedio", m)
        self.assertIn("utilizacion_cpu",     m)
        self.assertGreater(m["utilizacion_cpu"], 0)

    def test_quantum_1(self):
        """Con quantum=1 debe funcionar igual de correcto."""
        sched  = RoundRobinScheduler(quantum=1)
        result = sched.run(make_procs())
        self.assertEqual(len(result), 4)

    def test_single_process(self):
        """Un único proceso se ejecuta completo."""
        proc   = [Process(pid=1, name="Solo", priority=1, burst_time=7,
                           arrival_time=0, memory_pages=2)]
        sched  = RoundRobinScheduler(quantum=3)
        result = sched.run(proc)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].waiting_time, 0)
        self.assertEqual(result[0].turnaround_time, 7)


class TestSJF(unittest.TestCase):

    def test_all_complete(self):
        """Todos los procesos deben terminar."""
        sched  = SJFScheduler()
        result = sched.run(make_procs())
        self.assertEqual(len(result), 4)
        for p in result:
            self.assertEqual(p.state, ProcessState.TERMINATED)

    def test_shorter_job_runs_first(self):
        """El proceso más corto disponible se ejecuta primero."""
        procs = [
            Process(pid=1, name="Largo",  priority=1, burst_time=10,
                    arrival_time=0, memory_pages=1),
            Process(pid=2, name="Corto",  priority=1, burst_time=2,
                    arrival_time=0, memory_pages=1),
        ]
        sched  = SJFScheduler()
        result = sched.run(procs)
        # El proceso corto (pid=2) debe terminar antes
        p1 = next(p for p in result if p.pid == 1)
        p2 = next(p for p in result if p.pid == 2)
        self.assertLess(p2.completion_time, p1.completion_time)

    def test_waiting_non_negative(self):
        sched  = SJFScheduler()
        result = sched.run(make_procs())
        for p in result:
            self.assertGreaterEqual(p.waiting_time, 0)

    def test_metrics_ok(self):
        sched = SJFScheduler()
        sched.run(make_procs())
        m = sched.get_metrics()
        self.assertEqual(m["num_procesos"], 4)


class TestPriorityScheduler(unittest.TestCase):

    def test_all_complete(self):
        sched  = PriorityScheduler()
        result = sched.run(make_procs())
        self.assertEqual(len(result), 4)
        for p in result:
            self.assertEqual(p.state, ProcessState.TERMINATED)

    def test_high_priority_runs_first(self):
        """El proceso con prioridad 1 (más alta) debe terminar antes."""
        procs = [
            Process(pid=1, name="Baja",  priority=10, burst_time=4,
                    arrival_time=0, memory_pages=1),
            Process(pid=2, name="Alta",  priority=1,  burst_time=4,
                    arrival_time=0, memory_pages=1),
        ]
        sched  = PriorityScheduler()
        result = sched.run(procs)
        p1 = next(p for p in result if p.pid == 1)
        p2 = next(p for p in result if p.pid == 2)
        self.assertLessEqual(p2.response_time, p1.response_time)

    def test_no_negative_wait(self):
        sched  = PriorityScheduler()
        result = sched.run(make_procs())
        for p in result:
            self.assertGreaterEqual(p.waiting_time, 0)


if __name__ == "__main__":
    print("=" * 50)
    print("  Pruebas – Algoritmos de Planificación")
    print("=" * 50)
    unittest.main(verbosity=2)
