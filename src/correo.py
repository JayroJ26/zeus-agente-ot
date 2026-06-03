"""
correo.py · Canal de correo de Zeus.

Por ahora: LECTURA del reporte del operador por IMAP.
Lee los correos NO LEÍDOS de la bandeja de Zeus, los desarma con pyzmail y
devuelve una lista de reportes {uid, de, asunto, cuerpo}.

Las credenciales se leen de .env (NUNCA escritas aquí). Ver .env.example.
Más adelante añadiremos el ENVÍO (SMTP) de la OT generada.
"""

import os

import pyzmail
from dotenv import load_dotenv
from imapclient import IMAPClient

# Carga el .env desde la raíz del proyecto (funciona desde cualquier carpeta)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

EMAIL = os.getenv("ZEUS_EMAIL")
APP_PASSWORD = os.getenv("ZEUS_APP_PASSWORD")
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")


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
