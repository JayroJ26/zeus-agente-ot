"""
telegram_bot.py · Canal de Telegram de Zeus (ENTRADA y SALIDA de datos).

- ENTRADA: escucha los mensajes (reportes de los operadores) y los guarda en
  una bandeja  ->  data/bandeja_telegram.json
- SALIDA:  funciones para que Zeus responda al operador (texto y/o documento).

El CEREBRO (razonar el reporte y generar la OT) lo hace Zeus en la sesión de
Claude Code; este módulo solo MUEVE los datos de entrada y salida.

Token del bot: se lee de .env (TELEGRAM_BOT_TOKEN). Ver .env.example.
Crea tu bot y obtén el token con @BotFather en Telegram.
"""

import asyncio
import html
import json
import os
import unicodedata
from datetime import datetime, timezone

from dotenv import load_dotenv
from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

import almacen
import mensajes
import rag

# Carga el .env desde la raíz del proyecto (funciona desde cualquier carpeta)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Operadores autorizados: uno o varios chat_id separados por coma en .env
# (TELEGRAM_CHAT_ID). Si queda vacío, el bot acepta a CUALQUIERA (modo abierto).
_AUTORIZADOS = {
    s.strip() for s in (os.getenv("TELEGRAM_CHAT_ID") or "").split(",") if s.strip()
}


def _autorizado(chat_id):
    """True si el chat puede usar el bot. Sin lista configurada -> abierto a todos."""
    return not _AUTORIZADOS or str(chat_id) in _AUTORIZADOS

# Bandeja de reportes recibidos (el "buzón de entrada" de Zeus)
_BANDEJA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "bandeja_telegram.json",
)


# =========================== BANDEJA (buzón) ===============================
def _cargar_bandeja():
    if not os.path.exists(_BANDEJA):
        return []
    with open(_BANDEJA, encoding="utf-8") as f:
        return json.load(f)


def _guardar_bandeja(reportes):
    os.makedirs(os.path.dirname(_BANDEJA), exist_ok=True)
    with open(_BANDEJA, "w", encoding="utf-8") as f:
        json.dump(reportes, f, ensure_ascii=False, indent=2)


def guardar_reporte(chat_id, de, texto, fecha):
    reportes = _cargar_bandeja()
    reportes.append({
        "id": len(reportes) + 1,
        "chat_id": chat_id,
        "de": de,
        "texto": texto,
        "fecha": fecha,
        "procesado": False,
    })
    _guardar_bandeja(reportes)


def reportes_pendientes():
    """Devuelve los reportes que Zeus aún NO ha procesado."""
    return [r for r in _cargar_bandeja() if not r["procesado"]]


def marcar_procesado(id_reporte):
    reportes = _cargar_bandeja()
    for r in reportes:
        if r["id"] == id_reporte:
            r["procesado"] = True
    _guardar_bandeja(reportes)


# =================== SALIDA: enviar al operador ============================
def enviar_mensaje(chat_id, texto):
    """Envía un mensaje de texto a un chat. Acepta formato HTML de Telegram
    (<b>negrita</b>, <i>cursiva</i>, <code>...</code>)."""
    asyncio.run(_enviar_mensaje(chat_id, texto))


async def _enviar_mensaje(chat_id, texto):
    async with Bot(TOKEN) as bot:
        await bot.send_message(chat_id=chat_id, text=texto, parse_mode="HTML")


def enviar_documento(chat_id, ruta, caption=""):
    """Envía un archivo (p. ej. la OT en HTML o PDF) a un chat."""
    asyncio.run(_enviar_documento(chat_id, ruta, caption))


async def _enviar_documento(chat_id, ruta, caption):
    async with Bot(TOKEN) as bot:
        with open(ruta, "rb") as archivo:
            await bot.send_document(chat_id=chat_id, document=archivo, caption=caption)


# =================== ENTRADA: escuchar reportes ===========================
async def _on_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ Soy <b>Zeus</b>, tu asistente de mantenimiento industrial.\n\n"
        "Envíame el <b>reporte de la falla</b> (qué equipo y qué ocurre) y generaré "
        "la orden de trabajo.\n\n"
        "Comandos: /ayuda · /consulta · /pruebas · /pendientes · /id",
        parse_mode="HTML",
    )


async def _on_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚡ <b>Cómo usar a Zeus</b>\n\n"
        "1) Escribe el reporte tal cual: qué equipo, qué falla y dónde.\n"
        "   <i>Ej.: «Motor de la línea 2 con alta temperatura en Green Valley».</i>\n"
        "2) Zeus genera la orden de trabajo (OT) y te la devuelve aquí.\n\n"
        "<b>Comandos</b>\n"
        "/ayuda — esta ayuda\n"
        "/pruebas — registrar el checklist paso a paso (resultado, estado y observación de cada prueba)\n"
        "/cancelar — salir del llenado de pruebas\n"
        "/consulta — preguntar a la base técnica (manuales WEG y ANSI/NETA)\n"
        "/pendientes — reportes en cola por procesar\n"
        "/id — muestra tu chat_id (para darte de alta como operador)",
        parse_mode="HTML",
    )


async def _on_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Devuelve el chat_id del usuario. Útil para llenar TELEGRAM_CHAT_ID en .env."""
    chat_id = update.effective_chat.id
    estado = "✅ autorizado" if _autorizado(chat_id) else "🚫 no autorizado"
    await update.message.reply_text(
        f"Tu <b>chat_id</b> es <code>{chat_id}</code> ({estado}).",
        parse_mode="HTML",
    )


async def _on_pendientes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _autorizado(update.effective_chat.id):
        await update.message.reply_text("🚫 No estás autorizado para usar este comando.")
        return
    pendientes = reportes_pendientes()
    if not pendientes:
        await update.message.reply_text("✅ No hay reportes pendientes.")
        return
    lineas = "\n".join(
        f"• #{r['id']} — {html.escape(r['de'])}: {html.escape(r['texto'][:60])}"
        for r in pendientes[:10]
    )
    await update.message.reply_text(
        f"📋 <b>{len(pendientes)} reporte(s) en cola:</b>\n{lineas}",
        parse_mode="HTML",
    )


# =================== CONSULTA al RAG (/consulta) ==========================
# Mapa de palabras clave -> tipo_equipo, para filtrar la búsqueda si el operador
# menciona el tipo en su consulta (mejora la relevancia; opcional).
_TIPOS_RAG = {
    "motor": "Motor",
    "generador": "Generador eléctrico",
    "transformador": "Transformador",
}


def _tipo_en_consulta(texto):
    """Detecta si la consulta menciona un tipo de equipo para filtrar el RAG."""
    t = _sin_acentos(texto)
    for clave, tipo in _TIPOS_RAG.items():
        if clave in t:
            return tipo
    return None


async def _on_consulta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Consulta libre a la base de conocimiento (RAG): manuales WEG y ANSI/NETA.
    Uso: /consulta <pregunta>   p. ej.  /consulta tolerancia TTR transformador"""
    if not _autorizado(update.effective_chat.id):
        await update.message.reply_text("🚫 No estás autorizado para usar este comando.")
        return
    pregunta = " ".join(context.args).strip()
    if not pregunta:
        await update.message.reply_text(
            "📚 <b>Consulta a la base técnica</b> (manuales WEG y ANSI/NETA).\n"
            "Uso: <code>/consulta &lt;tu pregunta&gt;</code>\n"
            "<i>Ej.: /consulta tolerancia TTR transformador</i>",
            parse_mode="HTML",
        )
        return

    tipo = _tipo_en_consulta(pregunta)
    resultados = rag.buscar(pregunta, k=3, tipo_equipo=tipo)
    if not resultados:
        await update.message.reply_text(
            "🔍 No encontré nada relevante en la base técnica para esa consulta. "
            "Prueba con otras palabras clave (equipo, prueba, norma)."
        )
        return

    bloques = []
    for f in resultados:
        texto = " ".join(f["texto"].split())
        if len(texto) > 700:
            texto = texto[:700].rsplit(" ", 1)[0] + "…"
        bloques.append(
            f"📄 <b>{html.escape(f['fuente'])}</b>\n{html.escape(texto)}"
        )
    filtro = f" (tipo: {tipo})" if tipo else ""
    respuesta = (
        f"📚 <b>Base técnica</b> — {len(resultados)} fragmento(s) para "
        f"«{html.escape(pregunta)}»{filtro}:\n\n" + "\n\n".join(bloques)
    )
    await update.message.reply_text(respuesta, parse_mode="HTML")


# ============ Llenado GUIADO del checklist (/pruebas, /cancelar) ============
# Conversación con estado: por cada prueba pregunta resultado -> estado ->
# observación (una respuesta a la vez) y guarda en la OT ABIERTA del operador.
# El estado vive en memoria (se pierde si se reinicia el bot).
_pruebas = {}   # chat_id -> {"folio", "i", "campo", "valor", "estado"}


def _sin_acentos(texto):
    t = unicodedata.normalize("NFD", (texto or "").strip().casefold())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _prompt_prueba(ot, st):
    """Texto del prompt para la prueba/campo actual."""
    p = ot.checklist[st["i"]]
    cab = f"Prueba {st['i'] + 1}/{len(ot.checklist)}: {html.escape(p.nombre)}"
    if getattr(p, "solo_observacion", False):
        return f"📝 <b>{cab}</b>\nEscribe la <b>observación</b> (inspección sin medición) o «ninguna»:"
    if st["campo"] == "valor":
        u = f" (en {html.escape(p.unidad)})" if p.unidad else ""
        return f"🔧 <b>{cab}</b>\n¿<b>Resultado / medición</b>{u}?"
    if st["campo"] == "estado":
        return f"📊 <b>{html.escape(p.nombre)}</b>\n¿<b>Estado</b>? (OK / fuera de rango)"
    return f"🗒️ <b>{html.escape(p.nombre)}</b>\n¿<b>Observación</b>? (o «ninguna»)"


async def _on_pruebas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inicia el llenado guiado del checklist de la OT abierta del operador."""
    chat_id = update.effective_chat.id
    if not _autorizado(chat_id):
        await update.message.reply_text("🚫 No estás autorizado.")
        return
    ot = almacen.ot_abierta_de(chat_id)
    if ot is None:
        await update.message.reply_text("No tienes una orden ABIERTA. Manda primero el reporte de la falla.")
        return
    if not ot.checklist:
        await update.message.reply_text("Esta orden no tiene checklist de pruebas.")
        return
    _pruebas[chat_id] = {"folio": ot.folio, "i": 0, "campo": "valor", "valor": "", "estado": ""}
    await update.message.reply_text(
        f"📋 Registremos las <b>{len(ot.checklist)} pruebas</b> de la <b>{ot.folio}</b>, una por una. "
        "Responde cada mensaje. (/cancelar para salir.)",
        parse_mode="HTML",
    )
    await update.message.reply_text(_prompt_prueba(ot, _pruebas[chat_id]), parse_mode="HTML")


async def _on_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if _pruebas.pop(update.effective_chat.id, None):
        await update.message.reply_text("Llenado de pruebas cancelado.")
    else:
        await update.message.reply_text("No hay un llenado en curso.")


async def _avanzar_prueba(update: Update, chat_id):
    """Procesa la respuesta del operador dentro del llenado guiado."""
    st = _pruebas[chat_id]
    ot = almacen.ot_abierta_de(chat_id)
    if ot is None or ot.folio != st["folio"]:
        _pruebas.pop(chat_id, None)
        await update.message.reply_text("Se perdió la orden en curso. Reinicia con /pruebas.")
        return
    p = ot.checklist[st["i"]]
    resp = (update.message.text or "").strip()
    ninguna = _sin_acentos(resp) in ("ninguna", "ninguno", "no", "n/a", "na", "-", "sin")

    completa = False
    try:
        if getattr(p, "solo_observacion", False):
            mensajes.aplicar_resultado(ot, f"{p.nombre}: {'' if ninguna else resp}")
            completa = True
        elif st["campo"] == "valor":
            st["valor"], st["campo"] = resp, "estado"
        elif st["campo"] == "estado":
            st["estado"], st["campo"] = resp, "observacion"
        else:  # observacion -> ya tenemos los 3 datos
            obs = "" if ninguna else resp
            mensajes.aplicar_resultado(ot, f"{p.nombre}: {st['valor']} | {st['estado']} | {obs}")
            completa = True
    except ValueError as error:
        await update.message.reply_text(f"⚠️ {error}\n\n" + _prompt_prueba(ot, st), parse_mode="HTML")
        return

    if completa:
        almacen.guardar(ot)
        st["i"] += 1
        st["campo"], st["valor"], st["estado"] = "valor", "", ""
        if st["i"] >= len(ot.checklist):
            _pruebas.pop(chat_id, None)
            await update.message.reply_text(
                f"✅ Checklist completo de la <b>{ot.folio}</b> "
                f"({len(ot.checklist)}/{len(ot.checklist)}). Para cerrar la orden escribe «terminada».",
                parse_mode="HTML",
            )
            return
    await update.message.reply_text(_prompt_prueba(ot, st), parse_mode="HTML")


async def _on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    chat_id = update.effective_chat.id

    # --- Filtro de operadores autorizados ---
    if not _autorizado(chat_id):
        await msg.reply_text(
            "🚫 No estás autorizado para enviar reportes a Zeus.\n"
            f"Pide al administrador que registre tu chat_id: {chat_id}"
        )
        return

    # --- ¿Está llenando el checklist guiado (/pruebas)? ---
    if chat_id in _pruebas:
        await _avanzar_prueba(update, chat_id)
        return

    guardar_reporte(
        chat_id=chat_id,
        de=update.effective_user.full_name,
        texto=msg.text,
        fecha=msg.date.astimezone(timezone.utc).isoformat(timespec="minutes"),
    )
    await msg.reply_text(
        "✅ Reporte recibido. Zeus lo está procesando y te enviará la orden de "
        "trabajo por aquí."
    )


def escuchar():
    """Arranca el bot en modo escucha (polling). Ctrl+C para detener."""
    if not TOKEN:
        raise RuntimeError(
            "Falta TELEGRAM_BOT_TOKEN en .env (créalo con @BotFather y "
            "cópialo en .env). Ver .env.example."
        )
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", _on_start))
    app.add_handler(CommandHandler("ayuda", _on_ayuda))
    app.add_handler(CommandHandler("help", _on_ayuda))      # alias en inglés
    app.add_handler(CommandHandler("pendientes", _on_pendientes))
    app.add_handler(CommandHandler("consulta", _on_consulta))
    app.add_handler(CommandHandler("id", _on_id))
    app.add_handler(CommandHandler("pruebas", _on_pruebas))
    app.add_handler(CommandHandler("cancelar", _on_cancelar))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _on_message))

    modo = (f"restringido a {len(_AUTORIZADOS)} operador(es)" if _AUTORIZADOS
            else "ABIERTO a todos — define TELEGRAM_CHAT_ID en .env para restringir")
    print(f"Zeus escuchando en Telegram...  [{modo}]  (Ctrl+C para detener)")
    app.run_polling()


if __name__ == "__main__":
    escuchar()
