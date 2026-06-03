"""
folios.py · Memoria persistente del folio de las órdenes de trabajo.

¿Por qué existe este archivo?
El folio (p. ej. OT-2026-0007) es el número CORRELATIVO y ÚNICO de cada OT.
No puede repetirse ni volver a empezar en 0001 cada vez que arrancas el agente.
Antes el contador vivía en MEMORIA (un atributo de clase en modelos.py): al
cerrar el programa o la sesión de Claude se perdía y el folio se reiniciaba.

Solución: guardar el contador en DISCO -> data/contador_folios.json.
Así el correlativo "se acuerda" de cuántas OT van, aunque cierres todo.

El contador se reinicia SOLO al cambiar de año (OT-2026-0009 -> OT-2027-0001),
igual que en un sistema de mantenimiento (CMMS) real. Por eso guardamos un
contador POR AÑO:

    { "2026": 9, "2027": 1 }

Nota: para este proyecto (un solo usuario) el guardado simple basta. Si varios
procesos pidieran folios A LA VEZ habría que añadir un bloqueo de archivo.
"""

import json
import os
from datetime import datetime

# Ruta al archivo de memoria, SIEMPRE relativa a este módulo (no al cwd).
#   <proyecto>/data/contador_folios.json
_ARCHIVO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "contador_folios.json",
)


def _cargar():
    """Lee el contador de disco. Si no existe o está dañado, empieza vacío."""
    if not os.path.exists(_ARCHIVO):
        return {}
    try:
        with open(_ARCHIVO, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Nunca tumbamos al agente por un archivo corrupto: arrancamos limpio.
        return {}


def _guardar(contadores):
    """Escribe el contador en disco (crea la carpeta data/ si hace falta)."""
    os.makedirs(os.path.dirname(_ARCHIVO), exist_ok=True)
    with open(_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(contadores, f, ensure_ascii=False, indent=2)


def siguiente_folio(anio=None):
    """Reserva y devuelve el SIGUIENTE folio único, ej. 'OT-2026-0010'.

    Lee el último número del año, le suma 1, lo vuelve a guardar EN DISCO y
    devuelve el folio ya formateado. Al guardar ANTES de devolver, el folio
    sobrevive al cierre del programa y de la sesión de Claude.
    """
    anio = anio or datetime.now().year
    clave = str(anio)

    contadores = _cargar()
    siguiente = int(contadores.get(clave, 0)) + 1
    contadores[clave] = siguiente
    _guardar(contadores)

    return f"OT-{anio}-{siguiente:04d}"


def folio_actual(anio=None):
    """Devuelve el ÚLTIMO folio emitido (solo consulta, NO reserva uno nuevo).

    Útil para mostrar el estado sin gastar un número. Devuelve None si todavía
    no se ha emitido ninguna OT este año.
    """
    anio = anio or datetime.now().year
    contadores = _cargar()
    actual = int(contadores.get(str(anio), 0))
    return f"OT-{anio}-{actual:04d}" if actual else None


# === CONSULTA RÁPIDA (no consume folio): muestra el estado de la memoria =====
if __name__ == "__main__":
    anio_actual = datetime.now().year
    contadores = _cargar()
    n = int(contadores.get(str(anio_actual), 0))
    print(f"Archivo de memoria   : {_ARCHIVO}")
    print(f"OT emitidas en {anio_actual}  : {n}")
    print(f"Último folio          : {f'OT-{anio_actual}-{n:04d}' if n else '(ninguno todavía)'}")
    print(f"Próximo folio sería   : OT-{anio_actual}-{n + 1:04d}")
