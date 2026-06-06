"""
tools/enviar_prueba_3tipos.py · Envía un correo REAL de cada tipo de OT
(motor, generador, transformador) a la cuenta de Zeus, para revisar en Gmail
cómo se ven el membrete, el logo y la foto del equipo embebidos.

Reutiliza las OT de muestra y el CONTADOR DE FOLIOS TEMPORAL de preview_pdf
(importarlo ya redirige folios a un archivo temporal -> NO gasta el folio real).

Uso:  .venv\\Scripts\\python tools\\enviar_prueba_3tipos.py
"""

import os
import sys
import time

# Importar preview_pdf configura el contador temporal e importa src/.
from preview_pdf import _ot_motor, _ot_generador, _ot_transformador, SALIDA

import correo
import reporte


def enviar(ot, estado="ABIERTA"):
    """Genera el PDF y envía la OT por correo (con un reintento ante fallos de red)."""
    pdf = reporte.generar_pdf(ot, os.path.join(SALIDA, f"{ot.folio}.pdf"))
    asunto = f"[{ot.cliente}] Orden de trabajo {ot.folio} - {estado}"
    cuerpo_texto = (f"Orden de trabajo {ot.folio} ({estado})\n"
                    f"Cliente: {ot.cliente}\nEquipo: {ot.equipo.nombre} [{ot.equipo.tag}]")
    for intento in (1, 2):
        try:
            return correo.enviar_ot(
                pdf, asunto,
                cuerpo_html=reporte.cuerpo_correo(ot, estado),
                cuerpo_texto=cuerpo_texto,
                imagenes_inline=reporte.imagenes_inline_correo(ot),
            )
        except Exception as error:
            if intento == 2:
                raise
            print(f"   reintento ({error})")
            time.sleep(3)


def main():
    if not correo.envio_configurado():
        print("Correo NO configurado (faltan ZEUS_EMAIL/ZEUS_APP_PASSWORD en .env).")
        sys.exit(1)

    casos = [("Motor", _ot_motor()),
             ("Generador eléctrico", _ot_generador()),
             ("Transformador", _ot_transformador())]
    print("Enviando 3 correos de prueba (uno por tipo de equipo)...\n")
    for nombre, ot in casos:
        destino = enviar(ot)
        print(f"[OK] {nombre:20s} {ot.folio}  ->  {destino}")
    print("\nListo: 3 correos enviados. Revisá la bandeja de", destino)


if __name__ == "__main__":
    main()
