"""
tools/preview_correo.py · Prueba del correo SIN enviar nada.

1) Genera el cuerpo HTML (reporte.cuerpo_correo) de una OT de muestra.
2) Lo guarda self-contained (imágenes en base64) en salida/_preview_correo.html
   para abrirlo en el navegador.
3) Simula correo.enviar_ot con un SMTP FALSO y verifica la estructura MIME:
   logo + foto como multipart/related (con Content-ID) y el PDF como adjunto.

Usa un contador de folios temporal (no gasta el folio real). No envía correo.

Uso:  .venv\\Scripts\\python tools\\preview_correo.py
"""

import base64
import json
import os
import smtplib
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import folios
_tmp = os.path.join(tempfile.gettempdir(), "zeus_preview_folios.json")
json.dump({"2026": 900}, open(_tmp, "w"))
folios._ARCHIVO = _tmp

import correo
import reporte
from modelos import Equipo, OrdenTrabajoMotor, Prioridad

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "salida")
os.makedirs(SALIDA, exist_ok=True)


def _ot_demo():
    eq = Equipo("M-015", "Motor de línea de envasado 2", marca="Siemens",
                modelo="1LE1003", area="Empaque", criticidad="alta",
                potencia="30 kW", clase_aislamiento="F")
    ot = OrdenTrabajoMotor(equipo=eq, cliente="Industria Alimenticia Hondureña S.A.",
                           planta="Planta de Producción SPS",
                           ubicacion="Línea de Envasado 2", prioridad=Prioridad.ALTA)
    ot.reporte_original = ("El motor M-015 recalienta, huele a quemado y el "
                           "guardamotor disparó dos veces hoy.")
    ot.descripcion_falla = "Sobrecalentamiento del devanado con disparo térmico recurrente."
    ot.tipo = "correctivo"
    return ot


# --- SMTP falso: captura el mensaje en vez de enviarlo -----------------------
class _FakeSMTP:
    capturado = {}

    def __init__(self, *a, **k): pass
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def starttls(self): pass
    def login(self, *a): pass
    def send_message(self, msg): _FakeSMTP.capturado["msg"] = msg


def main():
    ot = _ot_demo()
    cuerpo = reporte.cuerpo_correo(ot, "ABIERTA")

    # (2) Versión self-contained con imágenes en base64 para el navegador
    html_preview = cuerpo
    for cid, ruta in reporte.imagenes_inline_correo(ot):
        b64 = base64.b64encode(open(ruta, "rb").read()).decode()
        html_preview = html_preview.replace(f"cid:{cid}", f"data:image/png;base64,{b64}")
    ruta_html = os.path.join(SALIDA, "_preview_correo.html")
    open(ruta_html, "w", encoding="utf-8").write(html_preview)
    print("HTML self-contained:", os.path.relpath(ruta_html))

    # (3) Simular el envío y auditar el MIME
    ruta_pdf = reporte.generar_pdf(ot, os.path.join(SALIDA, f"_preview_correo_{ot.folio}.pdf"))
    smtplib.SMTP = _FakeSMTP          # parche: NO se envía nada de verdad
    destino = correo.enviar_ot(
        ruta_pdf,
        asunto=f"[{ot.cliente}] Orden de trabajo {ot.folio} - ABIERTA",
        cuerpo_html=cuerpo,
        cuerpo_texto="Resumen de la OT (respaldo en texto).",
        imagenes_inline=reporte.imagenes_inline_correo(ot),
    )
    msg = _FakeSMTP.capturado.get("msg")
    print("\n--- Auditoría del MIME (destino:", destino, ") ---")
    print("Estructura:")
    for parte in msg.walk():
        ct = parte.get_content_type()
        cid = parte.get("Content-ID")
        disp = parte.get_content_disposition()
        extra = []
        if cid: extra.append(f"Content-ID={cid}")
        if disp: extra.append(disp)
        fn = parte.get_filename()
        if fn: extra.append(f"file={fn}")
        print(f"   {ct:28s} {' '.join(extra)}")

    tipos = [p.get_content_type() for p in msg.walk()]
    cids = [p.get("Content-ID") for p in msg.walk() if p.get("Content-ID")]
    refs = ["cid:" + c.strip("<>") in cuerpo for c in cids]
    print("\nChequeos:")
    print("  text/plain        :", "OK" if "text/plain" in tipos else "FALTA")
    print("  text/html         :", "OK" if "text/html" in tipos else "FALTA")
    print("  imágenes inline   :", tipos.count("image/png"), "(esperadas 2)")
    print("  multipart/related :", "OK" if "multipart/related" in tipos else "FALTA")
    print("  PDF adjunto       :", "OK" if "application/pdf" in tipos else "FALTA")
    print("  cids referenciados en el HTML:", "OK" if all(refs) and refs else "REVISAR", cids)


if __name__ == "__main__":
    main()
