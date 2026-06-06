# -*- coding: utf-8 -*-
"""
_build_demo_nb.py - Genera notebooks/demo.ipynb con nbformat.

El notebook recorre todo el pipeline de Zeus de punta a punta SIN depender de la
red de Telegram (es el "plan B" de la demo en vivo). Este script solo construye el
.ipynb; las salidas se incrustan despues ejecutandolo (nbclient / JupyterLab).

Correr:  .venv\\Scripts\\python notebooks\\_build_demo_nb.py
"""

import os
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

CELLS = []
def md(s):   CELLS.append(("md", s.strip("\n")))
def code(s): CELLS.append(("code", s.strip("\n")))


# ============================================================================
md(r'''
# Zeus ⚡ — Demo del agente generador de órdenes de trabajo

**Maestría en Automatización Industrial · UTH 2026.4** — Jayro Joel Rojas Avelar
Proyecto final · **Variante 3: generador de órdenes de trabajo (OT)**

Este notebook recorre **todo el pipeline de Zeus** de punta a punta, sin depender de la
red de Telegram (es el **plan B** de la demo en vivo). Cada paso corresponde a un
requisito de la rúbrica:

| Paso | Qué demuestra | Requisito |
|------|---------------|-----------|
| 1 | Clases POO (herencia + polimorfismo) | (1) |
| 2 | RAG sobre 2 manuales (WEG + ANSI/NETA) | (2) |
| 3 | Tool calling: detectar y pedir datos faltantes | (3) |
| 4 | Checklist de pruebas (el técnico reporta) | — |
| 5 | Salida 1: PDF profesional | (4) |
| 6 | Salida 2: correo SMTP | (4) |
| 7 | Ciclo de vida: ABIERTA → FINALIZADA | — |

> En la demo **en vivo**, todo esto entra y sale por **Telegram** (modo autónomo): el
> operador manda el reporte, Zeus razona y responde. Aquí lo corremos en local para
> verlo pieza por pieza, y como respaldo por si la red de Telegram falla.
''')

# ============================================================================
md(r'''
## 0 · Configuración

Dos interruptores controlan la demo:

- **`MODO_ENSAYO`** — en `True` usa folios y almacén **temporales**, así podés correr el
  notebook las veces que quieras **sin gastar folios reales** ni ensuciar `data/ordenes.json`.
  Para la demo "de verdad" ponelo en `False` (emite el folio real y lo guarda).
- **`ENVIAR_CORREO`** — en `True` envía la OT por SMTP de verdad. Para la demo ponelo en `True`
  (que llegue el correo a la bandeja); para ensayar, dejalo en `False`.
''')

code(r'''
import os, sys, json, tempfile
from IPython.display import display, HTML, Image

# ===================== INTERRUPTORES DE LA DEMO =====================
MODO_ENSAYO   = True     # True = folios/almacén temporales (no toca lo real). Demo real -> False
ENVIAR_CORREO = False    # True = envía el correo de verdad. Demo real -> True
# (Telegram no se usa aquí a propósito: este notebook es el plan B si la red de Telegram falla.)
# ===================================================================

# --- Localizar la raíz del proyecto (la carpeta que contiene 'src') y poner src/ en el path ---
raiz = os.getcwd()
while raiz and not os.path.isdir(os.path.join(raiz, "src")):
    padre = os.path.dirname(raiz)
    if padre == raiz:
        raise RuntimeError("No encontré la carpeta 'src'. Abrí el notebook dentro del proyecto.")
    raiz = padre
sys.path.insert(0, os.path.join(raiz, "src"))
print("Proyecto:", raiz)

# --- Módulos de Zeus (las 'tools' deterministas; el cerebro es la sesión de Claude) ---
import modelos, mensajes, rag, reporte, correo, almacen, folios, agente
from modelos import Equipo, OrdenTrabajoMotor, Prioridad

# --- En modo ensayo, redirigir folios y almacén a archivos temporales ---
if MODO_ENSAYO:
    demo_dir = os.path.join(tempfile.gettempdir(), "zeus_demo_ensayo")
    os.makedirs(demo_dir, exist_ok=True)
    folios._ARCHIVO  = os.path.join(demo_dir, "contador_ensayo.json")
    almacen._ARCHIVO = os.path.join(demo_dir, "ordenes_ensayo.json")
    json.dump({"2026": 8}, open(folios._ARCHIVO, "w"))   # arranca en 8 -> esta demo emite OT-2026-0009
    json.dump({}, open(almacen._ARCHIVO, "w"))
    print("MODO ENSAYO  -> folios y almacén temporales en:", demo_dir)
else:
    print("MODO REAL    -> usa folios y almacén de producción (gasta un folio).")

print("Último folio emitido:", folios.folio_actual(), " · el próximo será el de esta demo.")
''')

# ============================================================================
md(r'''
## 1 · Programación orientada a objetos (POO)

Zeus modela cada activo como un objeto **`Equipo`** y cada orden como una **subclase** de
**`OrdenDeTrabajo`**. La clase base define todo lo común; cada tipo de equipo (motor,
generador, transformador) **hereda** eso y aporta lo suyo por **polimorfismo**: su
checklist, su tipo de equipo y sus campos obligatorios.

Acá creamos la OT de un **motor** a partir de un reporte real de un operador.
''')

code(r'''
# El operador reporta la falla en lenguaje natural (esto es lo que llegaría por Telegram):
reporte_operador = (
    "Buen día. El motor M-015 de la línea de envasado 2 está recalentando, "
    "huele a quemado y el guardamotor ya disparó dos veces hoy. Es un Siemens. Urge."
)

# Zeus razona el reporte y arma el Equipo. Deja en '(por confirmar)' lo que el operador NO dio:
motor = Equipo(
    tag="(por confirmar)",                  # el operador no dio el tag exacto
    nombre="Motor de línea de envasado 2",
    marca="Siemens",
    modelo="(por confirmar)",
    area="Empaque",
    criticidad="alta",
    clase_aislamiento="(por confirmar)",    # dato térmico clave del motor, aún sin confirmar
)

# La OT nace ABIERTA y toma un folio único y persistente:
ot = OrdenTrabajoMotor(
    equipo=motor,
    cliente="Industria Alimenticia Hondureña S.A.",
    planta="Planta de Producción SPS",
    ubicacion="Línea de Envasado 2",
    prioridad=Prioridad.ALTA,
)
ot.reporte_original = reporte_operador
ot.tipo = "correctivo"

# ----- Lo que demuestra la POO -----
print("Folio asignado            :", ot.folio)
print("Clase de la OT            :", type(ot).__name__)
print("¿Hereda de OrdenDeTrabajo? :", isinstance(ot, modelos.OrdenDeTrabajo))
print("tipo_equipo() [polimorf.] :", ot.tipo_equipo())
print("Pruebas del checklist     :", len(ot.checklist))
for p in ot.checklist:
    print("   -", p.nombre, (f"({p.unidad})" if p.unidad else ""))
print()
print(ot.resumen())
print("Equipo:", ot.equipo.descripcion())
''')

# ============================================================================
md(r'''
## 2 · RAG — conocimiento de los manuales

Zeus tiene una base de conocimiento ligera (por **palabras clave**, sin embeddings ni APIs)
con **2 manuales**: la *Guía de Especificación de Motores Eléctricos WEG* y el estándar
*ANSI/NETA ATS-2009*. El flujo es: **(1)** Zeus interpreta la falla, **(2)** con el equipo + la
falla recupera del manual los fragmentos pertinentes (**filtrados por tipo de equipo**) y
**(3)** los lee para redactar las acciones, los repuestos y el tiempo.
''')

code(r'''
# (1) Zeus interpreta el reporte y resume la falla -- es su primer razonamiento:
ot.descripcion_falla = (
    "Sobrecalentamiento del motor con disparos repetidos del guardamotor. "
    "Posible sobrecarga térmica, falla de ventilación o aislamiento degradado."
)
print("Falla interpretada por Zeus:")
print("  ", ot.descripcion_falla)
''')

code(r'''
# (2) Con el equipo + la falla, recupera del manual los fragmentos relevantes (filtrado por Motor):
print("Fragmentos en el RAG:", rag.contar())
for fuente, n in rag.fuentes().items():
    print(f"   · {fuente}: {n}")

contexto = agente.contexto_para(ot, k=4)
print("\n----- Contexto recuperado del manual (top-4, ordenado por relevancia) -----\n")
print(contexto[:1400] + ("..." if len(contexto) > 1400 else ""))
''')

md(r'''
**(3) Zeus lee ese contexto y redacta** las acciones recomendadas, los repuestos y el
tiempo estimado. (En vivo lo hace el modelo en la sesión; aquí queda escrito el resultado
de ese razonamiento, fundamentado en los fragmentos de arriba: protección térmica, clase
de aislamiento y ajuste del relé.)
''')

code(r'''
ot.acciones_recomendadas = (
    "Verificar carga y corriente contra placa; ajustar el relé térmico a In×FS. "
    "Revisar ventilación y acumulación de polvo de empaque en la carcasa. "
    "Medir aislamiento y resistencia de devanados; controlar temperatura con Pt-100/PTC. "
    "Confirmar la clase de aislamiento (límite térmico) antes de reenergizar."
)
ot.descripcion_trabajo = (
    "Inspección térmica y eléctrica del motor; ajuste de la protección y limpieza de ventilación."
)
ot.repuestos_utilizados = ["Relé térmico (según In)", "Limpiador dieléctrico", "Sensor Pt-100 (si aplica)"]
ot.tiempo_estimado = "3.5 h"
ot.tecnico_asignado = "Ing. Jayro Rojas"
print("Acciones, repuestos y tiempo redactados por Zeus a partir del manual.  ✓")
''')

# ============================================================================
md(r'''
## 3 · Tool calling — detectar y pedir los datos que faltan

Antes de poder cerrar la OT, Zeus comprueba qué **datos obligatorios** faltan (según el
tipo de equipo, vía `CAMPOS_OBLIGATORIOS`) y se los pide al operador. Es una de sus
herramientas deterministas.
''')

code(r'''
faltan = mensajes.campos_faltantes(ot)
print("Campos obligatorios que faltan:", [etq for _c, etq in faltan])

print("\n----- Mensaje que Zeus le manda al operador -----")
display(HTML(mensajes.solicitar_datos(ot)))

# El operador responde (esto llegaría por Telegram). Zeus vuelca las respuestas a la OT:
respuesta_operador = "Tag: M-015\nModelo: 1LE1003\nClase de aislamiento: F"
aplicados = mensajes.aplicar_datos(ot, respuesta_operador)
print("Datos aplicados:", aplicados)
print("¿Faltan datos ahora? ->", mensajes.campos_faltantes(ot) or "no, la OT está completa ✓")
''')

# ============================================================================
md(r'''
## 4 · Checklist de pruebas — el técnico reporta los resultados

En campo, el técnico registra cada prueba. Por Telegram lo hace con **`/pruebas`** (guiado,
una por una) o mandando `Prueba: valor | estado | observación`. Acá usamos el **mismo parser**
(`mensajes.aplicar_resultado`), tolerante a unidades y acentos. Incluimos un par de pruebas
**fuera de rango** para ver el coloreado del checklist.
''')

code(r'''
resultados_campo = [
    "Inspección visual: carcasa con polvo de empaque | OK | se limpió",
    "Medición de aislamiento: 480 MΩ | OK | aceptable (> 100 MΩ)",
    "Resistencia de devanados: 0.43 Ω | OK | equilibrada entre fases",
    "Vibración: 2.4 mm/s | OK | dentro de ISO 10816",
    "Temperatura: 96 °C | fuera de rango | excede el límite de la Clase F en carga",
    "Alineación: 0.05 mm | OK |",
    "Prueba en vacío: 12.1 A | OK |",
    "Prueba con carga: 51 A | fuera de rango | supera la In de placa, revisar carga",
]
for linea in resultados_campo:
    nombre = mensajes.aplicar_resultado(ot, linea)
    print("registrada:", nombre)

print("\n----- Checklist de la OT -----")
for p in ot.checklist:
    print("  ", p)
''')

# ============================================================================
md(r'''
## 5 · Salida 1 — PDF profesional de la OT

Zeus arma el PDF **directamente desde el objeto OT** (con `fpdf2`), con el diseño
corporativo: encabezado, badges de prioridad/estado, datos, checklist coloreado y firmas.
Lo renderizamos acá dentro para verlo.
''')

code(r'''
import fitz   # PyMuPDF: render del PDF a imagen para mostrarlo en el notebook

salida_dir = os.path.join(raiz, "salida")
os.makedirs(salida_dir, exist_ok=True)
ruta_pdf = reporte.generar_pdf(ot, os.path.join(salida_dir, f"{ot.folio}.pdf"))
print("PDF generado:", ruta_pdf)

doc = fitz.open(ruta_pdf)
for i, pagina in enumerate(doc):
    pix = pagina.get_pixmap(dpi=110)
    png = os.path.join(tempfile.gettempdir(), f"_demo_{ot.folio}_p{i+1}.png")
    pix.save(png)
    display(Image(filename=png))
doc.close()
''')

# ============================================================================
md(r'''
## 6 · Salida 2 — correo SMTP

La misma OT se envía por correo: el **cuerpo** es un cuadro-resumen profesional (estilos
inline, compatible con Gmail/Outlook) y el **PDF va adjunto**. Primero la vista previa del
cuerpo; luego el envío real (si `ENVIAR_CORREO=True`).
''')

code(r'''
# Vista previa del cuerpo del correo (el cuadro profesional que ve el responsable):
display(HTML(reporte.cuerpo_correo(ot, "ABIERTA")))

# Envío real (solo si ENVIAR_CORREO=True y hay credenciales en .env):
if ENVIAR_CORREO and correo.envio_configurado():
    destino = correo.enviar_ot(
        ruta_pdf,
        asunto=f"[{ot.cliente}] Orden de trabajo {ot.folio} - ABIERTA",
        cuerpo_html=reporte.cuerpo_correo(ot, "ABIERTA"),
        cuerpo_texto=f"Orden de trabajo {ot.folio} ({ot.cliente}). Se adjunta el PDF.",
    )
    print("✅ Correo enviado a:", destino)
elif ENVIAR_CORREO:
    print("⚠️ ENVIAR_CORREO=True pero faltan credenciales en .env (ZEUS_EMAIL / ZEUS_APP_PASSWORD).")
else:
    print("ℹ️ ENVIAR_CORREO=False (ensayo): no se envió. En la demo real ponelo en True.")
''')

# ============================================================================
md(r'''
## 7 · Ciclo de vida — finalizar la OT

Cuando el operador dice **«terminada»**, Zeus comprueba que no falten datos obligatorios,
marca la OT como **FINALIZADA** y regenera el PDF final (ahora con el **badge verde** de
finalizada). El folio es único y persistente: sobrevive al cierre del programa.
''')

code(r'''
# El almacén persiste la OT (igual que en producción), y la finalizamos:
almacen.guardar(ot)
ot.finalizar("Trabajo correctivo concluido; motor operativo dentro de parámetros.")
almacen.guardar(ot)
print("Estado de la OT:", ot.estado.value.upper(), "· cerrada el", ot.fecha_cierre.strftime("%d/%m/%Y %H:%M"))

# PDF final con el badge verde de FINALIZADA:
ruta_final = reporte.generar_pdf(ot, os.path.join(salida_dir, f"{ot.folio}.pdf"))
doc = fitz.open(ruta_final)
pix = doc[0].get_pixmap(dpi=110)
png = os.path.join(tempfile.gettempdir(), f"_demo_final_{ot.folio}.png")
pix.save(png); doc.close()
display(Image(filename=png))
''')

# ============================================================================
md(r'''
## ✓ Resumen

En este notebook Zeus llevó un **reporte en lenguaje natural** hasta una **orden de trabajo
profesional, finalizada y enviada**, demostrando:

- **POO** — `OrdenTrabajoMotor` hereda de `OrdenDeTrabajo` y define su checklist por polimorfismo.
- **RAG** — recuperó contexto de 2 manuales (WEG + ANSI/NETA) para el diagnóstico y las acciones.
- **Tool calling** — detectó y pidió los datos faltantes; registró el checklist con su parser.
- **Salida doble** — PDF profesional **+** correo SMTP con el PDF adjunto.
- **Ciclo de vida** — ABIERTA → FINALIZADA, con folio único y persistente.

> En la **demo en vivo**, este mismo flujo ocurre por **Telegram**, con Zeus razonando cada
> reporte de forma autónoma. Este notebook es el **plan B**: corre igual aunque la red de
> Telegram falle.
''')


# ============================================================================
nb = new_notebook()
nb.cells = [new_markdown_cell(s) if t == "md" else new_code_cell(s) for t, s in CELLS]
nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3 (venv Zeus)", "language": "python"}
nb.metadata["language_info"] = {"name": "python", "version": "3.11"}

aqui = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(aqui, "demo.ipynb")
nbformat.write(nb, out)
print("Notebook escrito:", out)
print("Celdas:", len(nb.cells), "(", sum(1 for t, _ in CELLS if t == "md"), "markdown /",
      sum(1 for t, _ in CELLS if t == "code"), "code )")
