"""
_procesar_reporte_demo.py · Orquestación del flujo de Zeus (prueba del Paso 2).

Toma el reporte pendiente de la bandeja de Telegram, construye la OT que Zeus
razonó, genera el PDF (con el checklist EN BLANCO) y responde al operador por
Telegram:
  1) el documento de la OT,
  2) si faltan datos obligatorios -> los SOLICITA (mensajes.solicitar_datos),
  3) un AVISO de que el checklist va vacío + ejemplo de cómo reportar cada
     prueba (mensajes.aviso_ot).
Por último marca el reporte como procesado.

Ejecutar:
    .venv\\Scripts\\python _procesar_reporte_demo.py
    .venv\\Scripts\\python _procesar_reporte_demo.py --sin-enviar   (no usa Telegram)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from modelos import Equipo, OrdenTrabajoMotor, Prioridad
from reporte import generar_pdf
import mensajes
import telegram_bot as tb


def construir_ot(reporte):
    """Lo que Zeus RAZONA a partir del texto del reporte (demo: Green Valley).

    Los datos que el reporte NO da se dejan en '(por confirmar)' para que el
    flujo los pida después: Zeus NO inventa marca, modelo ni tag.
    """
    motor = Equipo(
        tag="(por confirmar)",
        nombre="Motor de línea 2",
        marca="(por confirmar)",
        modelo="",
        area="Línea 2",
        criticidad="media",
    )
    ot = OrdenTrabajoMotor(
        equipo=motor,
        cliente="Green Valley",
        planta="(por confirmar)",
        ubicacion="Línea 2",
        prioridad=Prioridad.ALTA,
        tipo="correctivo",
    )
    ot.reporte_original = reporte["texto"]
    ot.descripcion_falla = (
        "Alerta de alta temperatura en el motor de la línea 2. Posible "
        "sobrecalentamiento por sobrecarga, falla de ventilación/refrigeración, "
        "desgaste de rodamientos o problema en devanados (por diagnosticar)."
    )
    ot.acciones_recomendadas = (
        "Verificar carga y corriente de operación; revisar ventilación y limpieza "
        "de aletas; medir temperatura de carcasa y rodamientos; inspeccionar "
        "lubricación; medir aislamiento de devanados. (Pendiente de enriquecer con "
        "el manual del equipo vía RAG.)"
    )
    # El checklist se deja EN BLANCO: lo llenará el técnico tras el diagnóstico.
    return ot


def generar_documento(ot):
    """Genera el PDF de la OT en salida/ y devuelve la ruta."""
    salida_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "salida")
    os.makedirs(salida_dir, exist_ok=True)
    ruta = os.path.join(salida_dir, f"{ot.folio}.pdf")
    return generar_pdf(ot, ruta)


def responder_operador(chat_id, ot, ruta):
    """Responde al operador por Telegram: OT + (solicitud de datos) + aviso."""
    # 1) El documento de la OT.
    tb.enviar_documento(chat_id, ruta, caption=f"OT {ot.folio} — {ot.cliente}")

    # 2) Si faltan datos obligatorios, se los pedimos (no se inventan).
    solicitud = mensajes.solicitar_datos(ot)
    if solicitud:
        tb.enviar_mensaje(chat_id, solicitud)

    # 3) Aviso de checklist en blanco + ejemplo de cómo reportar cada prueba.
    tb.enviar_mensaje(chat_id, mensajes.aviso_ot(ot))


def main(enviar=True):
    pendientes = tb.reportes_pendientes()
    if not pendientes:
        print("No hay reportes pendientes en la bandeja.")
        return

    reporte = pendientes[0]
    print(f"Procesando reporte #{reporte['id']} de {reporte['de']}:")
    print(f"  «{reporte['texto']}»\n")

    ot = construir_ot(reporte)
    ruta = generar_documento(ot)
    print("OT generada:", ot.resumen())
    print("PDF:", ruta)
    faltan = [etq for _clave, etq in mensajes.campos_faltantes(ot)]
    print("Datos por confirmar:", ", ".join(faltan) if faltan else "ninguno")

    if enviar:
        responder_operador(reporte["chat_id"], ot, ruta)
        tb.marcar_procesado(reporte["id"])
        print(f"\nReporte #{reporte['id']} respondido por Telegram y marcado como procesado.")
    else:
        print("\n[--sin-enviar] No se usó Telegram; OT y mensajes se generaron localmente.")


if __name__ == "__main__":
    main(enviar="--sin-enviar" not in sys.argv)
