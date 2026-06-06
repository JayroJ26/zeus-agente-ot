"""
correo.py · Canal de correo de Zeus.

LECTURA del reporte del operador por IMAP (leer_reportes) y ENVÍO de la OT en
PDF por SMTP (enviar_ot). El envío se usa SOLO al crear y al finalizar la OT.

Las credenciales se leen de .env (NUNCA escritas aquí). Ver .env.example.
"""

import os
import smtplib
from email.message import EmailMessage

import pyzmail
from dotenv import load_dotenv
from imapclient import IMAPClient

# Carga el .env desde la raíz del proyecto (funciona desde cualquier carpeta)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

EMAIL = os.getenv("ZEUS_EMAIL")
APP_PASSWORD = os.getenv("ZEUS_APP_PASSWORD")
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
# Responsable de mantenimiento que recibe la OT. Vacío = se envía a la propia
# cuenta de Zeus (útil para la demo).
OT_DESTINATARIO = os.getenv("OT_DESTINATARIO", "")


def _extraer_cuerpo(msg):
    """Devuelve el texto del correo: prefiere texto plano; si no, el HTML."""
    parte = msg.text_part or msg.html_part
    if parte is None:
        return ""
    crudo = parte.get_payload()
    if crudo is None:
        return ""
    return crudo.decode(parte.charset or "utf-8", errors="replace").strip()


def leer_reportes(solo_no_leidos=True, marcar_leidos=False):
    """Conecta a la bandeja de Zeus y devuelve los reportes recibidos.

    Parámetros:
        solo_no_leidos: si True, solo trae los correos sin leer (UNSEEN).
        marcar_leidos:  si True, marca como leídos los que procesa.

    Devuelve: lista de dicts {uid, de, asunto, cuerpo}.
    """
    if not EMAIL or not APP_PASSWORD:
        raise RuntimeError(
            "Faltan credenciales: define ZEUS_EMAIL y ZEUS_APP_PASSWORD en el "
            "archivo .env (copia .env.example a .env y rellénalo)."
        )

    reportes = []
    with IMAPClient(IMAP_HOST, ssl=True) as servidor:
        servidor.login(EMAIL, APP_PASSWORD)
        servidor.select_folder("INBOX")

        criterio = ["UNSEEN"] if solo_no_leidos else ["ALL"]
        uids = servidor.search(criterio)

        for uid in uids:
            # BODY.PEEK[] descarga el correo SIN marcarlo como leído todavía.
            datos = servidor.fetch([uid], ["BODY.PEEK[]"])
            crudo = datos[uid][b"BODY[]"]
            msg = pyzmail.PyzMessage.factory(crudo)

            remitentes = msg.get_addresses("from")
            reportes.append({
                "uid": uid,
                "de": remitentes[0][1] if remitentes else "(desconocido)",
                "asunto": msg.get_subject() or "(sin asunto)",
                "cuerpo": _extraer_cuerpo(msg),
            })

            if marcar_leidos:
                servidor.add_flags([uid], [b"\\Seen"])

    return reportes


def envio_configurado():
    """True si hay credenciales para enviar correo (ZEUS_EMAIL + App Password)."""
    return bool(EMAIL and APP_PASSWORD)


def enviar_ot(ruta_pdf, asunto, cuerpo_html="", cuerpo_texto="", destinatario=None,
              imagenes_inline=None):
    """Envía la OT (PDF adjunto) por SMTP al responsable de mantenimiento.

    Parámetros:
        ruta_pdf:        ruta al PDF de la OT a adjuntar.
        asunto:          asunto del correo.
        cuerpo_html:     cuerpo en HTML (p. ej. reporte.cuerpo_correo(ot)); opcional.
        cuerpo_texto:    cuerpo en texto plano (respaldo si el cliente no ve HTML).
        destinatario:    correo de destino; por defecto OT_DESTINATARIO o, si está
                         vacío, la propia cuenta de Zeus.
        imagenes_inline: lista [(cid, ruta_png), ...] de imágenes a EMBEBER en el
                         HTML (logo, foto del equipo). En el HTML se referencian
                         con src="cid:<cid>". Se ignoran las rutas que no existan.

    Devuelve el correo de destino. Lanza RuntimeError si faltan credenciales o
    el PDF no existe.
    """
    if not envio_configurado():
        raise RuntimeError(
            "Faltan credenciales SMTP: define ZEUS_EMAIL y ZEUS_APP_PASSWORD en .env."
        )
    destino = destinatario or OT_DESTINATARIO or EMAIL
    if not destino:
        raise RuntimeError("No hay destinatario: define OT_DESTINATARIO en .env.")
    if not os.path.exists(ruta_pdf):
        raise RuntimeError(f"No existe el PDF a enviar: {ruta_pdf}")

    msg = EmailMessage()
    msg["From"] = EMAIL
    msg["To"] = destino
    msg["Subject"] = asunto
    msg.set_content(cuerpo_texto or "Adjunto la orden de trabajo en PDF.")
    if cuerpo_html:
        msg.add_alternative(cuerpo_html, subtype="html")
        # Imágenes embebidas (logo, foto del equipo): van como multipart/related
        # de la parte HTML, así Gmail/Outlook las muestran sin bloquearlas.
        if imagenes_inline:
            parte_html = msg.get_payload()[-1]
            for cid, ruta_img in imagenes_inline:
                if not ruta_img or not os.path.exists(ruta_img):
                    continue
                with open(ruta_img, "rb") as f:
                    parte_html.add_related(f.read(), maintype="image",
                                           subtype="png", cid=f"<{cid}>")

    with open(ruta_pdf, "rb") as f:
        datos = f.read()
    msg.add_attachment(datos, maintype="application", subtype="pdf",
                       filename=os.path.basename(ruta_pdf))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as servidor:
        servidor.starttls()
        servidor.login(EMAIL, APP_PASSWORD)
        servidor.send_message(msg)

    return destino


# === PRUEBA: lista los reportes nuevos en la bandeja de Zeus =================
if __name__ == "__main__":
    print(f"Conectando a {IMAP_HOST} como {EMAIL} ...\n")
    try:
        reportes = leer_reportes(solo_no_leidos=True)
    except Exception as error:
        print("ERROR:", error)
        raise SystemExit(1)

    print(f"Reportes nuevos: {len(reportes)}\n")
    for i, r in enumerate(reportes, 1):
        print(f"--- Reporte {i} ---")
        print("De     :", r["de"])
        print("Asunto :", r["asunto"])
        print("Cuerpo :", r["cuerpo"][:400])
        print()
