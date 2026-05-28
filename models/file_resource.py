"""
Modelos de recursos de archivo simulados.

Representan archivos sobre los que los procesos realizan
operaciones concurrentes de lectura y escritura.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class FileOperation(Enum):
    """Tipo de operación sobre un archivo."""
    READ  = "Lectura"
    WRITE = "Escritura"


class LockState(Enum):
    """Estado del bloqueo del archivo."""
    FREE   = "Libre"
    LOCKED = "Bloqueado"


@dataclass
class FileAccessEvent:
    """
    Registra un evento de acceso a un archivo por un proceso.

    Atributos:
        time      : Instante en que ocurrió el evento.
        pid       : PID del proceso que realiza la operación.
        filename  : Nombre del archivo accedido.
        operation : Tipo de operación (lectura o escritura).
        success   : True si pudo acceder, False si hubo conflicto/bloqueo.
        wait_time : Tiempo que esperó antes de obtener acceso.
        conflict  : True si se detectó conflicto con otro proceso.
    """
    time      : int
    pid       : int
    filename  : str
    operation : FileOperation
    success   : bool           = True
    wait_time : float          = 0.0
    conflict  : bool           = False
    message   : str            = ""

    def __repr__(self) -> str:
        estado  = "OK" if self.success else "BLOQUEADO"
        conflicto = " ⚠ CONFLICTO" if self.conflict else ""
        return (f"[t={self.time}] {self.operation.value} '{self.filename}' "
                f"PID={self.pid} → {estado}{conflicto}")


@dataclass
class SimulatedFile:
    """
    Archivo simulado con control de concurrencia.

    Atributos:
        name         : Nombre del archivo.
        content      : Contenido textual simulado.
        readers_count: Número de lectores activos (permite múltiples lecturas).
        writer_pid   : PID del escritor activo (exclusión mutua).
        access_log   : Historial de accesos al archivo.
    """
    name          : str
    content       : str               = "Contenido inicial del archivo."
    readers_count : int               = 0
    writer_pid    : Optional[int]     = None
    access_log    : List[FileAccessEvent] = field(default_factory=list)
    total_reads   : int               = 0
    total_writes  : int               = 0
    total_conflicts: int              = 0

    @property
    def lock_state(self) -> LockState:
        """Determina el estado de bloqueo actual del archivo."""
        if self.writer_pid is not None:
            return LockState.LOCKED
        return LockState.FREE

    @property
    def is_being_written(self) -> bool:
        return self.writer_pid is not None

    @property
    def is_being_read(self) -> bool:
        return self.readers_count > 0

    def log_event(self, event: FileAccessEvent):
        """Registra un evento de acceso en el historial."""
        self.access_log.append(event)
        if event.operation == FileOperation.READ:
            self.total_reads += 1
        else:
            self.total_writes += 1
        if event.conflict:
            self.total_conflicts += 1

    def get_summary(self) -> dict:
        """Retorna un resumen estadístico del archivo."""
        return {
            "Archivo"         : self.name,
            "Total Lecturas"  : self.total_reads,
            "Total Escrituras": self.total_writes,
            "Conflictos"      : self.total_conflicts,
            "Eventos"         : len(self.access_log),
        }

    def __repr__(self) -> str:
        return (f"File('{self.name}', lectores={self.readers_count}, "
                f"escritor={self.writer_pid}, estado={self.lock_state.value})")
