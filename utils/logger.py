"""
Módulo de logging centralizado del simulador.

Registra eventos del sistema en archivo y consola con formato estructurado.
"""

import logging
import os
from datetime import datetime
from config.settings import LOG_DIR


def get_logger(name: str = "SimuladorSO") -> logging.Logger:
    """
    Crea y retorna un logger configurado.

    Args:
        name: Nombre del logger (generalmente el módulo que lo usa).

    Returns:
        Logger configurado con handler de archivo y consola.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger  # Ya configurado

    logger.setLevel(logging.DEBUG)

    # Formato del log
    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )

    # Handler de archivo
    log_file = os.path.join(LOG_DIR, f"simulador_{datetime.now().strftime('%Y%m%d')}.log")
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    # Handler de consola
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


# Logger global del simulador
log = get_logger("SimuladorSO")
