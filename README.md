# Simulador de Sistema Operativo — UPTC 2026-1

Proyecto final de la asignatura **Sistemas Operativos** — Ingeniería de Sistemas, UPTC.

Simulador interactivo que implementa los tres grandes subsistemas de un SO: planificación de procesos, gestión de memoria virtual y acceso concurrente a archivos.

---

## Características

| Módulo | Algoritmos / Técnicas |
|---|---|
| Planificación | Round Robin (preemptivo), SJF (no preemptivo), Prioridad con Aging |
| Memoria | Paginación por demanda — reemplazo FIFO y LRU |
| Archivos | Problema Lectores-Escritores con `threading.Lock` (Mutex) |
| Interfaz | GUI oscura con tkinter + ttk, diagrama de Gantt con matplotlib |
| Pruebas | 26 tests unitarios independientes de la UI |

---

## Requisitos

- Python 3.8 o superior
- tkinter (incluido en la instalación estándar de Python para Windows)
- matplotlib ≥ 3.5

```
pip install -r requirements.txt
```

---

## Ejecución

```bash
# Desde la carpeta simulador_so/
python main.py
```

El sistema verifica automáticamente que matplotlib esté instalado antes de abrir la ventana.

---

## Estructura del proyecto

```
simulador_so/
│
├── main.py                     # Punto de entrada
├── requirements.txt
│
├── config/
│   └── settings.py             # Constantes globales y tema visual
│
├── models/                     # Entidades del dominio (dataclasses)
│   ├── process.py              # PCB — Process Control Block
│   ├── memory_page.py          # Page, Frame, PageFaultEvent
│   └── file_resource.py        # FileAccessEvent, SimulatedFile
│
├── core/                       # Lógica de negocio (sin dependencias de UI)
│   ├── scheduler/
│   │   ├── base_scheduler.py   # Clase abstracta + cálculo de métricas
│   │   ├── round_robin.py
│   │   ├── sjf.py
│   │   └── priority_scheduler.py
│   ├── memory/
│   │   ├── page_replacement.py # FIFOReplacement, LRUReplacement
│   │   └── memory_manager.py   # Facade de memoria
│   └── files/
│       └── file_manager.py     # Readers-Writers con threading.Lock
│
├── services/
│   └── simulation_service.py   # Facade principal — conecta core con UI
│
├── ui/
│   ├── app.py                  # Ventana principal, notebook, estilos ttk
│   └── tabs/
│       ├── process_tab.py      # Alta/baja de procesos
│       ├── scheduler_tab.py    # Gantt + métricas de planificación
│       ├── memory_tab.py       # Gráfica de hits/faults + tabla de marcos
│       ├── files_tab.py        # Registro de accesos concurrentes
│       └── metrics_tab.py      # Resumen global + exportación
│
├── tests/
│   ├── test_scheduler.py       # 14 tests de planificación
│   └── test_memory.py          # 12 tests de memoria
│
├── utils/
│   └── logger.py
│
└── exports/                    # CSVs y JSONs generados al exportar
```

---

## Cómo usar el simulador

1. **Pestaña Procesos** — Agrega los procesos que deseas simular (mínimo 2). Puedes usar los procesos de ejemplo predefinidos.
2. **Pestaña Planificación** — Elige el algoritmo (Round Robin, SJF, Prioridad) y ejecuta. El diagrama de Gantt y las métricas se generan automáticamente.
3. **Pestaña Memoria** — Selecciona FIFO o LRU y el número de marcos. Ejecuta para ver los page faults y la tasa de aciertos.
4. **Pestaña Archivos** — Ejecuta la simulación de acceso concurrente. Los eventos se muestran con código de color (verde = lectura OK, azul = escritura OK, rojo = conflicto bloqueado).
5. **Pestaña Métricas** — Compara los resultados de los tres módulos y exporta los datos como CSV o JSON.

---

## Ejecutar los tests

```bash
# Desde la carpeta simulador_so/
python -m pytest tests/ -v

# O con unittest directamente:
python -m unittest discover tests
```

Salida esperada: **26 tests passed**.

---

## Patrones de diseño utilizados

- **Template Method** — `BaseScheduler` define el flujo; Round Robin, SJF y Prioridad implementan `run()`.
- **Facade** — `SimulationService` expone una interfaz simple a la UI ocultando la complejidad del core.
- **Strategy** — `FIFOReplacement` y `LRUReplacement` son intercambiables en `MemoryManager`.
- **Observer** — `FileManager` notifica eventos de acceso mediante callbacks registrables.

---

## Métricas clave

| Métrica | Descripción |
|---|---|
| Tiempo de espera | Tiempo que el proceso pasa en la cola de listos sin usar CPU |
| Turnaround | Tiempo total desde llegada hasta finalización |
| Tiempo de respuesta | Tiempo desde llegada hasta la primera asignación de CPU |
| Throughput | Procesos completados por unidad de tiempo |
| Utilización CPU | Porcentaje del tiempo total en que la CPU estuvo ocupada |
| Hit Ratio | Porcentaje de accesos a memoria que no generaron page fault |
| Page Fault Rate | Porcentaje de accesos que requirieron cargar una página desde disco |

---

## Autora

Jazmin Moreno — Ingeniería de Sistemas, UPTC — 2026-1
