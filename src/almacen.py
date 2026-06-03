"""
almacen.py · Persistencia de las órdenes de trabajo (su CICLO DE VIDA).

Cada OT se guarda en disco (data/ordenes.json) indexada por su folio, con su
estado (abierta / finalizada) y su dueño (chat_id de Telegram). Así la OT
"recuerda" su estado entre mensajes y entre sesiones: se queda ABIERTA hasta que
el operador dueño dice que terminó, y entonces pasa a FINALIZADA.

    guardar(ot)            -> guarda o actualiza la OT (por folio).
    cargar(folio)          -> reconstruye la OT guardada (o None).
    ot_abierta_de(chat_id) -> la OT ABIERTA más reciente de ese operador (o None).
    listar()               -> dict crudo {folio: datos} de todas las OT.
"""

import json
import os

from modelos import crear_desde_dict

_ARCHIVO = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "ordenes.json",
)


def _cargar_todo():
    if not os.path.exists(_ARCHIVO):
        return {}
    try:
        with open(_ARCHIVO, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _guardar_todo(ordenes):
    os.makedirs(os.path.dirname(_ARCHIVO), exist_ok=True)
    with open(_ARCHIVO, "w", encoding="utf-8") as f:
        json.dump(ordenes, f, ensure_ascii=False, indent=2)


def guardar(ot):
    """Guarda o actualiza la OT (clave = folio)."""
    ordenes = _cargar_todo()
    ordenes[ot.folio] = ot.to_dict()
    _guardar_todo(ordenes)


def cargar(folio):
    """Reconstruye la OT guardada con ese folio (o None si no existe)."""
    ordenes = _cargar_todo()
    return crear_desde_dict(ordenes[folio]) if folio in ordenes else None


def ot_abierta_de(chat_id):
    """Devuelve la OT ABIERTA más reciente de ese operador (chat), o None."""
    ordenes = _cargar_todo()
    abiertas = [d for d in ordenes.values()
                if d.get("chat_id") == chat_id and d.get("estado") == "ABIERTA"]
    if not abiertas:
        return None
    abiertas.sort(key=lambda d: d["fecha_creacion"], reverse=True)
    return crear_desde_dict(abiertas[0])


def ot_de(chat_id):
    """La OT más reciente de ese operador (cualquier estado), o None."""
    ordenes = _cargar_todo()
    suyas = [d for d in ordenes.values() if d.get("chat_id") == chat_id]
    if not suyas:
        return None
    suyas.sort(key=lambda d: d["fecha_creacion"], reverse=True)
    return crear_desde_dict(suyas[0])


def listar():
    """Dict crudo {folio: datos} de todas las OT guardadas."""
    return _cargar_todo()


# === CONSULTA RÁPIDA: muestra el estado de las OT guardadas =================
if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    ordenes = _cargar_todo()
    print(f"OT guardadas: {len(ordenes)}")
    for folio, d in ordenes.items():
        print(f"  {folio} · {d.get('estado')} · chat {d.get('chat_id')} · {d.get('cliente')}")
