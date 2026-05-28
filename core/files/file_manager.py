"""
Gestor de Archivos con Concurrencia y Control de Bloqueos.

Simula el acceso concurrente a archivos compartidos usando:
  - threading.Lock  (Mutex) para acceso exclusivo de escritura.
  - threading.Semaphore para controlar el número de lectores concurrentes.

Implementa el paradigma Readers-Writers:
  - Múltiples lectores pueden leer simultáneamente (sin conflicto).
  - Un escritor necesita acceso exclusivo (bloquea todos los demás).
  - Si un escritor espera, los nuevos lectores deben esperar también.
"""

import threading
import time
import random
from typing import List, Dict, Callable, Optional

from models.process      import Process
from models.file_resource import SimulatedFile, FileAccessEvent, FileOperation
from config.settings     import (SIMULATED_FILES, WRITE_DELAY_MS,
                                 READ_DELAY_MS, MAX_FILE_THREADS)


class FileManager:
    """
    Gestor de archivos simulados con control de concurrencia.

    Usa el patrón Readers-Writers con prioridad de escritores
    para garantizar consistencia de datos.
    """

    def __init__(self, filenames: List[str] = None):
        self.files       : Dict[str, SimulatedFile] = {}
        self.global_log  : List[FileAccessEvent]    = []
        self._sim_time   : int                      = 0
        self._lock       : threading.Lock           = threading.Lock()  # Lock global para log
        self._callbacks  : List[Callable]           = []   # Para notificar la UI

        # Crear archivos simulados
        names = filenames or SIMULATED_FILES
        for name in names:
            self.files[name] = SimulatedFile(name=name)

        # Por cada archivo: mutex de escritura + semáforo de lectores
        self._file_write_locks    : Dict[str, threading.Lock]      = {}
        self._file_read_semaphores: Dict[str, threading.Semaphore] = {}
        self._file_reader_counts  : Dict[str, int]                 = {}
        self._file_reader_locks   : Dict[str, threading.Lock]      = {}

        for name in self.files:
            self._file_write_locks[name]     = threading.Lock()
            self._file_read_semaphores[name] = threading.Semaphore(MAX_FILE_THREADS)
            self._file_reader_counts[name]   = 0
            self._file_reader_locks[name]    = threading.Lock()

    # ── Registro de callbacks para la UI ─────────────────────────────────

    def on_event(self, callback: Callable):
        """Registra una función que se llama cuando hay un evento nuevo."""
        self._callbacks.append(callback)

    def _notify(self, event: FileAccessEvent):
        """Notifica a todos los observadores registrados."""
        for cb in self._callbacks:
            try:
                cb(event)
            except Exception:
                pass

    # ── Operaciones de archivo ────────────────────────────────────────────

    def read_file(self, pid: int, filename: str) -> FileAccessEvent:
        """
        Simula una operación de LECTURA sobre un archivo.

        Implementa la parte lectora del problema Readers-Writers:
          1. Obtener el lock de conteo de lectores.
          2. Incrementar el contador.
          3. Si es el primer lector, bloquear escritores.
          4. Leer (simular con sleep).
          5. Decrementar contador; si último lector, liberar escritores.

        Returns:
            FileAccessEvent con el resultado de la operación.
        """
        sim_file = self.files.get(filename)
        if not sim_file:
            return self._create_error_event(pid, filename, FileOperation.READ,
                                             "Archivo no existe")

        t_start  = time.time()
        conflict = False
        success  = True
        msg      = ""

        reader_lock = self._file_reader_locks[filename]
        write_lock  = self._file_write_locks[filename]

        # Intentar obtener acceso de lectura
        reader_lock.acquire()
        self._file_reader_counts[filename] += 1
        sim_file.readers_count += 1

        if self._file_reader_counts[filename] == 1:
            # Primer lector: intentar bloquear escritores
            acquired = write_lock.acquire(timeout=2.0)
            if not acquired:
                # Hay un escritor activo → conflicto
                conflict = True
                success  = False
                msg      = f"PID {pid} no pudo leer '{filename}': escritor activo"
                self._file_reader_counts[filename] -= 1
                sim_file.readers_count -= 1
                reader_lock.release()

                event = self._make_event(pid, filename, FileOperation.READ,
                                          success, t_start, conflict, msg)
                self._log_event(sim_file, event)
                return event

        reader_lock.release()

        # Simular tiempo de lectura
        time.sleep(READ_DELAY_MS / 1000)

        # Leer contenido
        content = sim_file.content
        msg = f"PID {pid} leyó '{filename}': '{content[:30]}...'"

        # Liberar acceso de lectura
        reader_lock.acquire()
        self._file_reader_counts[filename] -= 1
        sim_file.readers_count -= 1
        if self._file_reader_counts[filename] == 0:
            write_lock.release()
        reader_lock.release()

        event = self._make_event(pid, filename, FileOperation.READ,
                                  success, t_start, conflict, msg)
        self._log_event(sim_file, event)
        return event

    def write_file(self, pid: int, filename: str,
                   new_content: str = None) -> FileAccessEvent:
        """
        Simula una operación de ESCRITURA sobre un archivo.

        Implementa la parte escritora del problema Readers-Writers:
          1. Obtener el lock de escritura (exclusivo).
          2. Si no se puede en 2 segundos → conflicto registrado.
          3. Escribir (simular con sleep).
          4. Liberar el lock.

        Returns:
            FileAccessEvent con el resultado de la operación.
        """
        sim_file = self.files.get(filename)
        if not sim_file:
            return self._create_error_event(pid, filename, FileOperation.WRITE,
                                             "Archivo no existe")

        t_start    = time.time()
        write_lock = self._file_write_locks[filename]
        conflict   = False
        success    = True
        msg        = ""

        # Intentar adquirir el lock de escritura
        acquired = write_lock.acquire(timeout=2.0)

        if not acquired:
            conflict = True
            success  = False
            msg      = f"PID {pid} no pudo escribir '{filename}': recurso ocupado (CONFLICTO)"
            event    = self._make_event(pid, filename, FileOperation.WRITE,
                                         success, t_start, conflict, msg)
            sim_file.writer_pid = None
            self._log_event(sim_file, event)
            return event

        # Escritura exclusiva obtenida
        sim_file.writer_pid = pid

        # Simular tiempo de escritura
        time.sleep(WRITE_DELAY_MS / 1000)

        content = new_content or f"[PID={pid}] escritura en t={self._sim_time}"
        sim_file.content    = content
        sim_file.writer_pid = None
        msg = f"PID {pid} escribió en '{filename}'"

        write_lock.release()

        event = self._make_event(pid, filename, FileOperation.WRITE,
                                  success, t_start, conflict, msg)
        self._log_event(sim_file, event)
        return event

    # ── Simulación concurrente ────────────────────────────────────────────

    def simulate_concurrent_access(self, processes: List[Process],
                                    callback: Callable = None) -> List[FileAccessEvent]:
        """
        Simula el acceso concurrente de múltiples procesos a archivos.

        Lanza un hilo por cada proceso que necesita acceso a archivos.
        Los resultados se registran en el log global.

        Args:
            processes : Lista de procesos que acceden a archivos.
            callback  : Función llamada con cada FileAccessEvent generado.

        Returns:
            Lista de todos los eventos de acceso registrados.
        """
        if callback:
            self.on_event(callback)

        threads    = []
        filenames  = list(self.files.keys())
        all_events = []
        events_lock = threading.Lock()

        def process_task(proc: Process):
            """Tarea de un proceso: realiza lecturas y escrituras."""
            # Número de operaciones proporcional al burst_time
            num_ops = max(2, proc.burst_time // 2)
            file_ops_local = []

            for i in range(num_ops):
                fname     = random.choice(filenames)
                operation = random.choices(
                    [FileOperation.READ, FileOperation.WRITE],
                    weights=[0.7, 0.3]  # 70% lectura, 30% escritura
                )[0]

                if operation == FileOperation.READ:
                    event = self.read_file(proc.pid, fname)
                else:
                    event = self.write_file(proc.pid, fname)

                file_ops_local.append(event)
                time.sleep(random.uniform(0.05, 0.15))   # Pausa entre operaciones

            with events_lock:
                all_events.extend(file_ops_local)

        # Lanzar hilos
        file_procs = [p for p in processes if p.accesses_files]
        if not file_procs:
            file_procs = processes[:min(len(processes), MAX_FILE_THREADS)]

        for proc in file_procs:
            t = threading.Thread(target=process_task, args=(proc,), daemon=True)
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        return all_events

    # ── Métricas y helpers ────────────────────────────────────────────────

    def get_all_events(self) -> List[FileAccessEvent]:
        """Retorna todos los eventos registrados (orden cronológico)."""
        all_ev = []
        for sf in self.files.values():
            all_ev.extend(sf.access_log)
        return sorted(all_ev, key=lambda e: e.time)

    def get_summary(self) -> List[Dict]:
        """Retorna un resumen por archivo."""
        return [f.get_summary() for f in self.files.values()]

    def get_conflicts(self) -> List[FileAccessEvent]:
        """Retorna solo los eventos que generaron conflicto."""
        return [e for e in self.get_all_events() if e.conflict]

    def _make_event(self, pid, filename, operation, success,
                     t_start, conflict, msg) -> FileAccessEvent:
        with self._lock:
            self._sim_time += 1
            t = self._sim_time

        wait_time = round((time.time() - t_start) * 1000, 2)   # ms
        return FileAccessEvent(
            time      = t,
            pid       = pid,
            filename  = filename,
            operation = operation,
            success   = success,
            wait_time = wait_time,
            conflict  = conflict,
            message   = msg,
        )

    def _log_event(self, sim_file: SimulatedFile, event: FileAccessEvent):
        sim_file.log_event(event)
        with self._lock:
            self.global_log.append(event)
        self._notify(event)

    def _create_error_event(self, pid, filename, op, msg) -> FileAccessEvent:
        return FileAccessEvent(time=0, pid=pid, filename=filename,
                                operation=op, success=False,
                                conflict=False, message=msg)

    def reset(self):
        """Reinicia todos los archivos."""
        for sf in self.files.values():
            sf.access_log     = []
            sf.readers_count  = 0
            sf.writer_pid     = None
            sf.total_reads    = 0
            sf.total_writes   = 0
            sf.total_conflicts= 0
        self.global_log = []
        self._sim_time  = 0
