"""
tools/preview_pdf.py · Genera un PDF de muestra de CADA tipo de OT y los
renderiza a PNG para revisar el membrete y la foto del equipo.

Usa un CONTADOR DE FOLIOS TEMPORAL (no toca data/contador_folios.json), así que
se puede correr las veces que sea sin gastar el folio real de producción.

Uso:  .venv\\Scripts\\python tools\\preview_pdf.py
Salida: salida/_preview_pdf.png  (+ los PDF de muestra en salida/)
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

import folios

# --- Redirigir el contador a un archivo temporal ANTES de crear ninguna OT ---
_tmp = os.path.join(tempfile.gettempdir(), "zeus_preview_folios.json")
json.dump({"2026": 900}, open(_tmp, "w"))   # los folios de prueba serán 0901+
folios._ARCHIVO = _tmp

import reporte
from modelos import (Equipo, OrdenTrabajoMotor, OrdenTrabajoGenerador,
                     OrdenTrabajoTransformador, Prioridad)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "salida")
os.makedirs(SALIDA, exist_ok=True)


def _ot_motor():
    eq = Equipo("M-015", "Motor de línea de envasado 2", marca="Siemens",
                modelo="1LE1003", area="Empaque", criticidad="alta",
                potencia="30 kW", clase_aislamiento="F")
    ot = OrdenTrabajoMotor(equipo=eq, cliente="Industria Alimenticia Hondureña S.A.",
                           planta="Planta de Producción SPS",
                           ubicacion="Línea de Envasado 2", prioridad=Prioridad.ALTA)
    ot.reporte_original = ("El motor M-015 recalienta, huele a quemado y el "
                           "guardamotor disparó dos veces hoy.")
    ot.descripcion_falla = "Sobrecalentamiento del devanado con disparo térmico recurrente."
    ot.acciones_recomendadas = ("Ajustar el relé térmico a In x FS, verificar ventilación "
                                "y limpiar polvo de empaque; instalar sensores Pt-100.")
    ot.tipo = "correctivo"
    ot.tecnico_asignado = "Ing. Jayro Rojas"
    ot.registrar_prueba("Medición de aislamiento", 480, "OK", "Mínimo aceptable 100 MΩ")
    ot.registrar_prueba("Temperatura", 96, "fuera de rango", "Clase F límite 155 °C; punto caliente")
    ot.registrar_prueba("Vibración", 3.1, "OK", "Límite ISO 4.5 mm/s")
    return ot


def _ot_generador():
    eq = Equipo("GEN-02", "Planta de emergencia", marca="Caterpillar", modelo="DE250",
                area="Subestación", criticidad="alta", serie="CAT-99812", potencia="250 KVA")
    ot = OrdenTrabajoGenerador(equipo=eq, cliente="Hospital Regional del Norte",
                               planta="Edificio Central", ubicacion="Casa de máquinas",
                               prioridad=Prioridad.MEDIA)
    ot.reporte_original = "Mantenimiento preventivo semestral de la planta de emergencia."
    ot.descripcion_falla = "Sin falla: rutina preventiva programada."
    ot.acciones_recomendadas = ("Cambio de aceite y filtros, prueba de baterías y "
                                "ensayo de transferencia automática (ATS) bajo carga.")
    ot.tipo = "preventivo"
    ot.tecnico_asignado = "Ing. Jayro Rojas"
    ot.registrar_prueba("Prueba de arranque", "", "OK", "Arranca en 3 s")
    return ot


def _ot_transformador():
    eq = Equipo("TR-07", "Transformador de distribución", marca="ABB", modelo="ONAN-500",
                area="Subestación", criticidad="alta", serie="ABB-44120",
                potencia="500 KVA", tension="13.8 kV")
    ot = OrdenTrabajoTransformador(equipo=eq, cliente="Parque Industrial Zip Norte",
                                   planta="Subestación 1", ubicacion="Patio de MT",
                                   prioridad=Prioridad.ALTA)
    ot.reporte_original = "Puesta en servicio de transformador nuevo de 500 KVA."
    ot.descripcion_falla = "Sin falla: pruebas de aceptación previas a energizar."
    ot.acciones_recomendadas = ("Medir relación de transformación (TTR), resistencia de "
                                "aislamiento y rigidez dieléctrica del aceite; verificar tierra.")
    ot.tipo = "preventivo"
    ot.tecnico_asignado = "Ing. Jayro Rojas"
    ot.registrar_prueba("Inspección de instalación", "", "N/A", "Montaje conforme a plano")
    ot.registrar_prueba("Resistencia de aislamiento", 2100, "OK", "> 1000 MΩ")
    return ot


def main():
    casos = [("motor", _ot_motor()), ("generador", _ot_generador()),
             ("transformador", _ot_transformador())]
    pdfs = []
    for nombre, ot in casos:
        ruta = os.path.join(SALIDA, f"_preview_{nombre}_{ot.folio}.pdf")
        reporte.generar_pdf(ot, ruta)
        pdfs.append((nombre, ruta))
        print("PDF:", os.path.relpath(ruta), "·", ot.tipo_equipo())

    # Render a PNG y montaje horizontal de las 3 primeras páginas
    try:
        import fitz
        from PIL import Image
    except ImportError as e:
        print("(sin render:", e, ")")
        return
    imgs = []
    for nombre, ruta in pdfs:
        pix = fitz.open(ruta)[0].get_pixmap(dpi=150)
        png = os.path.join(SALIDA, f"_preview_{nombre}.png")
        pix.save(png)
        imgs.append(Image.open(png).convert("RGB"))
    alto = 1150
    redim = [im.resize((int(im.width * alto / im.height), alto)) for im in imgs]
    sep = 16
    W = sum(im.width for im in redim) + sep * (len(redim) + 1)
    hoja = Image.new("RGB", (W, alto + sep * 2), (225, 230, 236))
    x = sep
    for im in redim:
        hoja.paste(im, (x, sep))
        x += im.width + sep
    destino = os.path.join(SALIDA, "_preview_pdf.png")
    hoja.save(destino)
    print("Montaje:", os.path.relpath(destino))


if __name__ == "__main__":
    main()
