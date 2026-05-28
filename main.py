"""
╔═══════════════════════════════════════════════════════════════════╗
║       SIMULADOR DE SISTEMA OPERATIVO – UPTC SO 2026-1            ║
║                                                                   ║
║  Autores : Equipo de trabajo                                      ║
║  Materia : Sistemas Operativos                                    ║
║  Lenguaje: Python 3.8+                                            ║
║                                                                   ║
║  Módulos implementados:                                           ║
║    • Planificación: Round Robin, SJF, Prioridad (con Aging)       ║
║    • Memoria: Paginación por demanda, FIFO, LRU                   ║
║    • Archivos: Concurrencia con Mutex y Semáforos                 ║
║                                                                   ║
║  Arquitectura: Capas (UI → Services → Core → Models)             ║
╚═══════════════════════════════════════════════════════════════════╝

Punto de entrada principal del simulador.
Ejecutar con:  python main.py
"""

import sys
import os

# ── Configurar ruta de búsqueda de módulos ─────────────────────────────────
# Necesario para que los imports relativos funcionen correctamente
# en Windows al ejecutar desde cualquier directorio.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ── Verificar dependencias antes de lanzar la UI ──────────────────────────
def check_dependencies() -> bool:
    """Verifica que las dependencias requeridas estén instaladas."""
    missing = []
    required = {
        "matplotlib": "pip install matplotlib",
    }
    for pkg, cmd in required.items():
        try:
            __import__(pkg)
        except ImportError:
            missing.append((pkg, cmd))

    if missing:
        print("\n❌ Dependencias faltantes:")
        for pkg, cmd in missing:
            print(f"   • {pkg}  →  ejecuta: {cmd}")
        print("\nInstala todas con:\n   pip install matplotlib\n")
        return False
    return True


def main():
    """Función principal: lanza la interfaz gráfica."""
    print("=" * 60)
    print("  Simulador de Sistema Operativo – UPTC SO 2026-1")
    print("=" * 60)

    if not check_dependencies():
        input("\nPresiona Enter para salir...")
        sys.exit(1)

    # Importar y lanzar la UI (después de verificar dependencias)
    try:
        from ui.app import launch
        print("✅ Iniciando interfaz gráfica...\n")
        launch()
    except Exception as e:
        print(f"\n❌ Error al iniciar la aplicación: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona Enter para salir...")
        sys.exit(1)


if __name__ == "__main__":
    main()
