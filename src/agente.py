"""
agente.py · Orquestador del CICLO DE VIDA de la orden de trabajo.

Une las herramientas para que la OT nazca ABIERTA, acumule los avances que manda
el operador, y se FINALICE (regenerando el PDF una última vez) solo cuando el
operador DUEÑO dice que terminó.

  crear_y_enviar(ot, chat_id)        -> registra la OT (ABIERTA) y envía PDF + solicitud + aviso.
  aplicar_actualizacion(chat_id, t)  -> aplica un dato o el resultado de una prueba a la OT abierta.
  finalizar_y_enviar(chat_id, obs)   -> finaliza, regenera el PDF y lo envía. None si no hay OT
                                        abierta; False si faltan datos obligatorios (NO la cierra y
                                        se los pide al operador).

El "cerebro" (razonar un reporte nuevo y construir la OT con la clase correcta)
lo hace Zeus en la sesión; estas funciones mueven el estado de forma determinista.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))   # ya estamos en src/

import almacen
import correo
import mensajes
import rag
import reporte
import telegram_bot as tb

_SALIDA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "salida")


def _pdf(ot):
    """Genera (o regenera) el PDF de la OT en salida/{folio}.pdf y devuelve la ruta."""
    os.makedirs(_SALIDA, exist_ok=True)
    return reporte.generar_pdf(ot, os.path.join(_SALIDA, f"{ot.folio}.pdf"))


def _enviar_correo(ot, ruta_pdf, estado):
    """Envía por correo el PDF de la OT (solo al crear y al finalizar). Es
    RESILIENTE: si el correo no está configurado o falla, NO rompe el flujo
    (Telegram sigue funcionando); solo deja un aviso en consola. Devuelve el
    destinatario si se envió, o None."""
    if not correo.envio_configurado():
        return None
    try:
        destino = correo.enviar_ot(
            ruta_pdf,
            asunto=f"Orden de trabajo {ot.folio} - {ot.cliente} ({estado})",
            cuerpo_html=reporte.generar_html(ot),
            cuerpo_texto=f"Adjunto la orden de trabajo {ot.folio} ({estado}) en PDF.",
        )
        print(f"[correo] OT {ot.folio} ({estado}) enviada a {destino}")
        return destino
    except Exception as error:
        print(f"[correo] No se pudo enviar la OT {ot.folio} por correo: {error}")
        return None


def contexto_para(ot, k=5):
    """Recupera del RAG el contexto de manual relevante a ESTA OT (equipo + falla
    + reporte), filtrado por su tipo de equipo. Devuelve texto (vacío si nada).
    Zeus lo LEE y redacta acciones/repuestos/tiempos; el RAG solo aporta."""
    consulta = f"{ot.equipo.nombre} {ot.descripcion_falla} {ot.reporte_original}"
    return rag.contexto(consulta, tipo_equipo=ot.tipo_equipo(), k=k)


def crear_y_enviar(ot, chat_id):
    """Registra la OT (nace ABIERTA, a nombre del operador) y le envía el PDF
    inicial, la solicitud de datos faltantes y el aviso del checklist."""
    ot.chat_id = chat_id
    almacen.guardar(ot)
    ruta = _pdf(ot)
    tb.enviar_documento(chat_id, ruta, caption=f"OT {ot.folio} — {ot.cliente} (ABIERTA)")
    _enviar_correo(ot, ruta, "ABIERTA")
    solicitud = mensajes.solicitar_datos(ot)
    if solicitud:
        tb.enviar_mensaje(chat_id, solicitud)
    tb.enviar_mensaje(chat_id, mensajes.aviso_ot(ot))
    return ot


def aplicar_actualizacion(chat_id, texto):
    """Aplica a la OT ABIERTA del operador un dato de cabecera o el resultado de
    una prueba. Devuelve (ot, detalle); (None, motivo) si no hay OT abierta."""
    ot = almacen.ot_abierta_de(chat_id)
    if ot is None:
        return None, "no hay OT abierta para este operador"

    # ¿El mensaje es el resultado de una prueba del checklist?
    nombre = texto.split(":", 1)[0] if ":" in texto else ""
    if mensajes._buscar_prueba(ot, nombre) is not None:
        try:
            prueba = mensajes.aplicar_resultado(ot, texto)
            almacen.guardar(ot)
            return ot, f"prueba registrada: {prueba}"
        except ValueError as error:
            return ot, f"no pude registrar la prueba: {error}"

    # Si no, lo tratamos como dato(s) de cabecera (Cliente, Planta, Serie, ...).
    aplicados = mensajes.aplicar_datos(ot, texto)
    if aplicados:
        almacen.guardar(ot)
        return ot, f"datos actualizados: {', '.join(aplicados)}"

    return ot, "no reconocí una prueba ni un dato en el mensaje"


def finalizar_y_enviar(chat_id, observaciones=""):
    """Finaliza la OT ABIERTA del operador: estado FINALIZADA, regenera el PDF
    una última vez y se lo envía.

    Devuelve:
        - la OT (FINALIZADA) si se cerró con éxito;
        - None si no hay OT abierta;
        - False si hay OT pero le faltan DATOS OBLIGATORIOS -> NO se cierra; se le
          piden al operador (no se puede finalizar una OT incompleta)."""
    ot = almacen.ot_abierta_de(chat_id)
    if ot is None:
        return None

    # No cerrar una OT a la que le faltan datos obligatorios: pedírselos primero.
    faltan = mensajes.campos_faltantes(ot)
    if faltan:
        etiquetas = ", ".join(etiq for _c, etiq in faltan)
        tb.enviar_mensaje(
            chat_id,
            f"⚠️ Aún no puedo cerrar la orden <b>{ot.folio}</b>: faltan datos "
            f"obligatorios (<b>{etiquetas}</b>). Agrégalos y luego dime que terminaste.",
        )
        solicitud = mensajes.solicitar_datos(ot)
        if solicitud:
            tb.enviar_mensaje(chat_id, solicitud)
        return False

    ot.finalizar(observaciones)
    almacen.guardar(ot)                       # ahora queda FINALIZADA en disco
    ruta = _pdf(ot)                           # regenera el PDF final
    tb.enviar_mensaje(
        chat_id,
        f"✅ Orden <b>{ot.folio}</b> marcada como <b>FINALIZADA</b>. Te envío la versión final.",
    )
    tb.enviar_documento(chat_id, ruta, caption=f"OT {ot.folio} — {ot.cliente} (FINALIZADA)")
    _enviar_correo(ot, ruta, "FINALIZADA")
    return ot


_FOLIO_RE = re.compile(r"OT-\d{4}-\d{4}", re.IGNORECASE)


def reenviar_ot(chat_id, texto=""):
    """Reenvía el PDF de la OT solicitada: por folio si el mensaje lo menciona,
    si no, la OT más reciente del operador. Devuelve la OT o None."""
    m = _FOLIO_RE.search(texto or "")
    ot = almacen.cargar(m.group(0).upper()) if m else almacen.ot_de(chat_id)
    if ot is None:
        return None
    ruta = _pdf(ot)
    tb.enviar_documento(chat_id, ruta,
                        caption=f"OT {ot.folio} — {ot.cliente} ({ot.estado.value.upper()})")
    return ot


def procesar_mensaje(chat_id, texto):
    """Despacha el mensaje del operador aplicando la REGLA del PDF: solo se manda
    el PDF al CREAR la OT, al FINALIZARLA y cuando el operador la SOLICITA. Los
    avances (datos / resultados de pruebas) se confirman con texto, SIN PDF.

    Devuelve (accion, info). 'nuevo_reporte' = Zeus debe razonar un reporte nuevo.
    """
    # 1) ¿Dice que terminó? -> finalizar y enviar el PDF final.
    #    Si faltan datos obligatorios, finalizar_y_enviar NO cierra (devuelve False)
    #    y ya le pidió los datos al operador.
    if mensajes.es_finalizar(texto):
        ot = finalizar_y_enviar(chat_id)
        if ot is None:
            return ("sin_ot_abierta", None)
        if ot is False:
            return ("faltan_datos", None)
        return ("finalizada", ot)

    # 2) ¿Pide su OT? -> reenviar el PDF.
    if mensajes.es_solicitud_ot(texto):
        ot = reenviar_ot(chat_id, texto)
        return ("reenviada", ot) if ot is not None else ("sin_ot_abierta", None)

    # 3) ¿Avance sobre su OT abierta? -> confirmación de TEXTO, sin PDF.
    if almacen.ot_abierta_de(chat_id) is not None:
        _ot, detalle = aplicar_actualizacion(chat_id, texto)
        if not detalle.startswith("no reconoc"):
            tb.enviar_mensaje(chat_id, f"✅ {detalle[:1].upper()}{detalle[1:]}.")
            return ("actualizada", detalle)

    # 4) Nada de lo anterior -> es un reporte NUEVO (lo razona Zeus y llama crear_y_enviar).
    return ("nuevo_reporte", None)
