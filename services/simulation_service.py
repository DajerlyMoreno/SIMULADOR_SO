"""
Servicio de Simulación – Orquestador Principal.

Coordina la ejecución de las tres fases de simulación:
  1. Planificación de procesos (scheduler)
  2. Gestión de memoria (paginación)
  3. Gestión de archivos (concurrencia)

Aplica el patrón Facade: expone una interfaz simple para la UI.
"""

import csv
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

from models.process       import Process, ProcessState
from core.scheduler.round_robin       import RoundRobinScheduler
from core.scheduler.sjf               import SJFScheduler
from core.scheduler.priority_scheduler import PriorityScheduler
from core.memory.memory_manager       import MemoryManager
from core.files.file_manager          import FileManager
from config.settings                  import (EXPORT_DIR, QUANTUM_DEFAULT,
                                               TOTAL_FRAMES)


class SimulationService:
    """
    Servicio orquestador de todas las simulaciones.

    Centraliza la lógica de negocio para que la UI no tenga
    dependencias directas con los algoritmos del núcleo.
    """

    SCHEDULERS = {
        "Round Robin" : lambda q: RoundRobinScheduler(quantum=q),
        "SJF"         : lambda q: SJFScheduler(),
        "Prioridad"   : lambda q: PriorityScheduler(),
    }

    def __init__(self):
        self.processes       : List[Process]   = []
        self.scheduler_result: List[Process]   = []
        self.scheduler_gantt : List[Dict]      = []
        self.scheduler_metrics: Dict           = {}
        self.memory_results  : List[Dict]      = []
        self.memory_stats    : Dict            = {}
        self.file_events     : List           = []
        self.file_summaries  : List[Dict]      = []
        self.current_algo    : str             = "Round Robin"
        self.current_quantum : int             = QUANTUM_DEFAULT
        self.memory_manager  : Optional[MemoryManager] = None
        self.file_manager    : Optional[FileManager]   = None

        # Asegurar que existan directorios de exportación
        os.makedirs(EXPORT_DIR, exist_ok=True)

    # ── Gestión de procesos ───────────────────────────────────────────────

    def set_processes(self, processes: List[Process]):
        """Establece la lista de procesos a simular."""
        self.processes = processes

    def add_process(self, process: Process):
        """Agrega un proceso a la lista."""
        self.processes.append(process)

    def clear_processes(self):
        """Limpia la lista de procesos."""
        self.processes = []

    # ── Simulación de planificación ───────────────────────────────────────

    def run_scheduler(self, algorithm: str = None,
                       quantum: int = None) -> Dict[str, Any]:
        """
        Ejecuta la simulación de planificación de procesos.

        Args:
            algorithm: "Round Robin", "SJF" o "Prioridad".
            quantum  : Quantum para Round Robin.

        Returns:
            Diccionario con procesos, Gantt y métricas.
        """
        algo    = algorithm or self.current_algo
        q       = quantum   or self.current_quantum
        factory = self.SCHEDULERS.get(algo, self.SCHEDULERS["Round Robin"])

        scheduler = factory(q)
        self.scheduler_result  = scheduler.run(self.processes)
        self.scheduler_gantt   = scheduler.get_gantt()
        self.scheduler_metrics = scheduler.get_metrics()
        self.current_algo      = algo
        self.current_quantum   = q

        return {
            "processes": self.scheduler_result,
            "gantt"    : self.scheduler_gantt,
            "metrics"  : self.scheduler_metrics,
            "algorithm": algo,
        }

    # ── Simulación de memoria ─────────────────────────────────────────────

    def run_memory_simulation(self, algorithm: str = "LRU",
                               num_frames: int = None) -> Dict[str, Any]:
        """
        Ejecuta la simulación de gestión de memoria.

        Args:
            algorithm : "FIFO" o "LRU".
            num_frames: Número de marcos de RAM.

        Returns:
            Diccionario con resultados por proceso y estadísticas globales.
        """
        frames = num_frames or TOTAL_FRAMES
        self.memory_manager = MemoryManager(num_frames=frames, algorithm=algorithm)

        results = []
        for proc in self.processes:
            res = self.memory_manager.simulate_process_accesses(proc)
            results.append(res)

        self.memory_results = results
        self.memory_stats   = self.memory_manager.get_global_stats()

        return {
            "results"   : self.memory_results,
            "stats"     : self.memory_stats,
            "frames"    : self.memory_manager.get_frame_states(),
            "events"    : self.memory_manager.get_page_fault_events(),
            "history"   : self.memory_manager.get_history(),
            "algorithm" : algorithm,
        }

    # ── Simulación de archivos ────────────────────────────────────────────

    def run_file_simulation(self, callback=None) -> Dict[str, Any]:
        """
        Ejecuta la simulación de acceso concurrente a archivos.

        Args:
            callback: Función opcional llamada en cada evento (para UI en tiempo real).

        Returns:
            Diccionario con eventos y resumen por archivo.
        """
        self.file_manager = FileManager()
        self.file_events  = self.file_manager.simulate_concurrent_access(
            self.processes, callback=callback
        )
        self.file_summaries = self.file_manager.get_summary()

        return {
            "events"   : self.file_events,
            "summaries": self.file_summaries,
            "conflicts": self.file_manager.get_conflicts(),
            "all_events": self.file_manager.get_all_events(),
        }

    # ── Exportación de resultados ─────────────────────────────────────────

    def export_metrics_csv(self) -> str:
        """
        Exporta las métricas de planificación a un archivo CSV.

        Returns:
            Ruta del archivo generado.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath  = os.path.join(EXPORT_DIR, f"metricas_{timestamp}.csv")

        if not self.scheduler_result:
            return ""

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.scheduler_result[0].to_dict().keys())
            writer.writeheader()
            for proc in self.scheduler_result:
                writer.writerow(proc.to_dict())

        return filepath

    def export_full_report_json(self) -> str:
        """
        Exporta un reporte completo en JSON con todas las simulaciones.

        Returns:
            Ruta del archivo generado.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath  = os.path.join(EXPORT_DIR, f"reporte_completo_{timestamp}.json")

        report = {
            "timestamp"         : timestamp,
            "algoritmo_usado"   : self.current_algo,
            "quantum"           : self.current_quantum,
            "num_procesos"      : len(self.processes),
            "metricas_scheduler": self.scheduler_metrics,
            "metricas_memoria"  : self.memory_stats,
            "resumen_archivos"  : self.file_summaries,
            "procesos"          : [p.to_dict() for p in self.scheduler_result],
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return filepath

    # ── Generación de procesos de ejemplo ─────────────────────────────────

    @staticmethod
    def generate_sample_processes(n: int = 6) -> List[Process]:
        """
        Genera procesos de muestra para demostración.

        Args:
            n: Número de procesos a generar.

        Returns:
            Lista de procesos con características variadas.
        """
        import random
        samples = [
            Process(pid=1, name="Sistema",    priority=1, burst_time=4,  arrival_time=0, memory_pages=3, accesses_files=False),
            Process(pid=2, name="Navegador",  priority=3, burst_time=6,  arrival_time=1, memory_pages=5, accesses_files=True),
            Process(pid=3, name="Editor",     priority=5, burst_time=3,  arrival_time=2, memory_pages=2, accesses_files=True),
            Process(pid=4, name="Compilador", priority=2, burst_time=8,  arrival_time=0, memory_pages=4, accesses_files=False),
            Process(pid=5, name="Base Datos", priority=1, burst_time=5,  arrival_time=3, memory_pages=6, accesses_files=True),
            Process(pid=6, name="Antivirus",  priority=8, burst_time=10, arrival_time=1, memory_pages=3, accesses_files=False),
            Process(pid=7, name="Multimedia", priority=6, burst_time=7,  arrival_time=4, memory_pages=5, accesses_files=True),
            Process(pid=8, name="Red",        priority=4, burst_time=2,  arrival_time=2, memory_pages=2, accesses_files=True),
        ]
        return samples[:min(n, len(samples))]
