"""
reporte.py · Presentación profesional de una OrdenDeTrabajo en HTML.

Separa la PRESENTACIÓN (cómo se ve) de los DATOS (modelos.py). La misma OT
puede mostrarse en consola, HTML, PDF... sin tocar la lógica de las clases.

El HTML usa estilos 'inline' en los elementos clave para que se vea bien tanto
en el navegador como dentro de un correo (muchos clientes de correo ignoran las
hojas de estilo externas, pero respetan el style="..." de cada etiqueta).
"""

import html
import os

from modelos import Equipo, OrdenTrabajoMotor, Prioridad


# --- Datos del PRESTADOR del servicio (tu empresa / taller). EDITA ESTO ------
EMPRESA = {
    "nombre": "Servicios de Mantenimiento Industrial S. de R.L.",
    "eslogan": "Confiabilidad que mueve tu planta",
    "contacto": "servicio@mantenimiento.hn  ·  +504 0000-0000",
}

# --- Paletas de color --------------------------------------------------------
_COLOR_PRIORIDAD = {
    "crítica": "#c0392b",
    "alta": "#e67e22",
    "media": "#b7950b",
    "baja": "#27ae60",
}
# Color del estado de la OT (abierta -> gris; finalizada -> verde).
_COLOR_ESTADO_OT = {
    "abierta": "#34495e",
    "en proceso": "#e67e22",
    "finalizada": "#1e7e34",
}
_COLOR_ESTADO_PRUEBA = {
    "OK": ("#1e7e34", "#e8f5e9"),            # (color de texto, color de fondo)
    "fuera de rango": ("#a12622", "#fdecea"),
    "N/A": ("#6c757d", "#f1f3f5"),
}

# Marco general (clases para el navegador; lo crítico va inline más abajo).
_ESTILO = '''
<style>
  body { margin:0; padding:24px; background:#eef1f5;
         font-family:Arial,Helvetica,sans-serif; color:#1a2b3c; }
  .hoja { max-width:800px; margin:0 auto; background:#ffffff;
          border-top:6px solid #1f3a5f; box-shadow:0 2px 14px rgba(0,0,0,.12); }
  table { width:100%; border-collapse:collapse; }
  @media print { body { background:#fff; padding:0; }
                 .hoja { box-shadow:none; max-width:100%; } }
</style>
'''


def _badge(texto, fondo, color="#ffffff"):
    return (f"<span style='display:inline-block;padding:4px 12px;border-radius:14px;"
            f"background:{fondo};color:{color};font-size:12px;font-weight:bold;"
            f"letter-spacing:.4px;text-transform:uppercase;'>{texto}</span>")


def _seccion(titulo):
    return (f"<tr><td colspan='2' style='padding:9px 12px;background:#1f3a5f;"
            f"color:#ffffff;font-size:12.5px;font-weight:bold;letter-spacing:.6px;"
            f"text-transform:uppercase;'>{titulo}</td></tr>")


def _fila(etiqueta, valor):
    val = valor if valor not in (None, "", []) else "—"
    return (f"<tr>"
            f"<td style='padding:7px 12px;width:30%;background:#f5f8fb;font-weight:bold;"
            f"color:#33475b;border:1px solid #e3e8ee;vertical-align:top;'>{etiqueta}</td>"
            f"<td style='padding:7px 12px;color:#1a2b3c;border:1px solid #e3e8ee;'>{val}</td>"
            f"</tr>")


def _tabla_checklist(ot):
    th = ("padding:8px 10px;font-size:12px;color:#ffffff;text-align:left;"
          "background:#33475b;letter-spacing:.3px;")
    filas = (f"<tr><td style='{th}'>Prueba</td><td style='{th}'>Resultado</td>"
             f"<td style='{th};text-align:center;'>Estado</td>"
             f"<td style='{th}'>Observación</td></tr>")
    celda = "padding:7px 10px;border:1px solid #e3e8ee;font-size:13px;"
    for p in ot.checklist:
        casilla = "☑" if p.realizada else "☐"
        nombre = html.escape(p.nombre)

        if getattr(p, "solo_observacion", False):
            # Sin medición: una celda de observación que abarca Resultado+Estado+Observación.
            obs = html.escape(p.observacion) if (p.realizada and p.observacion) else "&nbsp;"
            filas += (
                f"<tr>"
                f"<td style='{celda}'>{casilla}&nbsp; {nombre}</td>"
                f"<td style='{celda}color:#566573;' colspan='3'>{obs}</td>"
                f"</tr>"
            )
            continue

        if p.realizada:
            # Prueba ya ejecutada: medición, estado (con color) y observación.
            color_txt, color_bg = _COLOR_ESTADO_PRUEBA.get(p.estado, ("#6c757d", "#f1f3f5"))
            resultado = html.escape(f"{p.valor} {p.unidad}".strip())
            estado_celda = (f"<td style='{celda}background:{color_bg};color:{color_txt};"
                            f"font-weight:bold;text-align:center;'>{html.escape(p.estado)}</td>")
            observacion = html.escape(p.observacion) if p.observacion else "&nbsp;"
        else:
            # Prueba PENDIENTE: columnas EN BLANCO para que el técnico las llene en campo.
            resultado = "&nbsp;"
            estado_celda = f"<td style='{celda}'>&nbsp;</td>"
            observacion = "&nbsp;"

        filas += (
            f"<tr>"
            f"<td style='{celda}'>{casilla}&nbsp; {nombre}</td>"
            f"<td style='{celda}'>{resultado}</td>"
            f"{estado_celda}"
            f"<td style='{celda}color:#566573;'>{observacion}</td>"
            f"</tr>"
        )
    return f"<table>{filas}</table>"


def _firmas():
    cel = ("padding-top:46px;text-align:center;width:33%;font-size:12px;color:#33475b;")
    linea = "border-top:1px solid #33475b;margin:0 14px;padding-top:6px;"
    def col(rol):
        return f"<td style='{cel}'><div style='{linea}'>{rol}</div></td>"
    return ("<table><tr>"
            + col("Técnico responsable")
            + col("Supervisor de mantenimiento")
            + col("Recibido por (cliente)")
            + "</tr></table>")


def generar_html(ot):
    """Devuelve el documento HTML completo y profesional de la orden de trabajo."""
    fecha = ot.fecha_creacion.strftime("%d/%m/%Y %H:%M")
    badge_prioridad = _badge(f"Prioridad {ot.prioridad.value}",
                             _COLOR_PRIORIDAD.get(ot.prioridad.value, "#7f8c8d"))
    badge_estado = _badge(ot.estado.value, _COLOR_ESTADO_OT.get(ot.estado.value, "#34495e"))

    if ot.repuestos_utilizados:
        repuestos = "<br>".join(f"•&nbsp; {r}" for r in ot.repuestos_utilizados)
    else:
        repuestos = "—"

    # Encabezado corporativo
    encabezado = f"""
    <div style="background:#1f3a5f;color:#ffffff;padding:20px 28px;">
      <table><tr>
        <td style="vertical-align:middle;">
          <div style="font-size:19px;font-weight:bold;letter-spacing:.3px;">{EMPRESA['nombre']}</div>
          <div style="font-size:12px;color:#c8d6e5;margin-top:2px;">{EMPRESA['eslogan']}</div>
        </td>
        <td style="text-align:right;vertical-align:middle;">
          <div style="font-size:17px;font-weight:bold;letter-spacing:1px;">ORDEN DE TRABAJO</div>
          <div style="font-size:13px;color:#c8d6e5;margin-top:2px;">N.º {ot.folio}</div>
        </td>
      </tr></table>
    </div>
    <div style="padding:12px 28px;background:#eef3f8;border-bottom:1px solid #d6e0ea;">
      <table><tr>
        <td style="font-size:12.5px;color:#33475b;vertical-align:middle;">
          Fecha de emisión: <b>{fecha}</b></td>
        <td style="text-align:right;vertical-align:middle;">{badge_prioridad}&nbsp;&nbsp;{badge_estado}</td>
      </tr></table>
    </div>
    """

    # Tabla principal de datos
    datos = "<table>"
    datos += _seccion("Cliente y ubicación")
    datos += _fila("Cliente", ot.cliente)
    datos += _fila("Planta", ot.planta)
    datos += _fila("Ubicación", ot.ubicacion)
    datos += _seccion("Equipo")
    datos += _fila("Tag / identificador", ot.equipo.tag)
    datos += _fila("Equipo", ot.equipo.nombre)
    datos += _fila("Marca / modelo", f"{ot.equipo.marca} {ot.equipo.modelo}".strip())
    if getattr(ot.equipo, "serie", ""):
        datos += _fila("Serie", ot.equipo.serie)
    if getattr(ot.equipo, "potencia", ""):
        datos += _fila("Potencia", ot.equipo.potencia)
    if getattr(ot.equipo, "tension", ""):
        datos += _fila("Tensión", ot.equipo.tension)
    if getattr(ot.equipo, "clase_aislamiento", ""):
        datos += _fila("Clase de aislamiento", ot.equipo.clase_aislamiento)
    datos += _fila("Área", ot.equipo.area)
    datos += _fila("Criticidad", ot.equipo.criticidad)
    datos += _seccion("Falla y diagnóstico")
    datos += _fila("Reporte del operador", ot.reporte_original)
    datos += _fila("Descripción de la falla", ot.descripcion_falla)
    datos += _fila("Acciones recomendadas", ot.acciones_recomendadas)
    datos += _seccion("Trabajo ejecutado")
    datos += _fila("Tipo de mantenimiento", ot.tipo)
    datos += _fila("Descripción del trabajo", ot.descripcion_trabajo)
    datos += _fila("Repuestos utilizados", repuestos)
    datos += _fila("Tiempo estimado", ot.tiempo_estimado)
    datos += _fila("Técnico asignado", ot.tecnico_asignado)
    datos += "</table>"

    # Checklist (el título usa tipo_equipo() -> polimorfismo)
    titulo_check = (f"<div style='background:#1f3a5f;color:#ffffff;padding:9px 12px;"
                    f"font-size:12.5px;font-weight:bold;letter-spacing:.6px;"
                    f"text-transform:uppercase;'>Checklist de pruebas — {ot.tipo_equipo()}</div>")

    pie = f"""
    <div style="padding:14px 28px;background:#f5f8fb;border-top:1px solid #e3e8ee;
                text-align:center;font-size:11px;color:#8a99a8;">
      Documento generado por <b>Zeus</b> · Agente de mantenimiento industrial &nbsp;·&nbsp; {EMPRESA['contacto']}
    </div>
    """

    cuerpo = (
        encabezado
        + "<div style='padding:22px 28px 6px;'>" + datos + "</div>"
        + "<div style='padding:10px 28px;'>" + titulo_check + _tabla_checklist(ot) + "</div>"
        + "<div style='padding:24px 28px 6px;'>" + _firmas() + "</div>"
        + pie
    )

    return ("<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
            "<title>Orden de trabajo " + ot.folio + "</title>" + _ESTILO + "</head>"
            "<body><div class='hoja'>" + cuerpo + "</div></body></html>")


# === PDF (fpdf2) ============================================================
# Mismo contenido y colores que el HTML, pero como PDF listo para enviar por
# Telegram o imprimir. Se construye DIRECTO desde la OT (no convierte HTML), así
# que no necesita binarios externos: solo la librería fpdf2.

def _hex_a_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _color_estado_pdf(estado):
    return {
        "OK": ((30, 126, 52), (232, 245, 233)),
        "fuera de rango": ((161, 38, 34), (253, 236, 234)),
    }.get(estado, ((108, 117, 125), (241, 243, 245)))


def _pdf_barra(pdf, titulo, ancho):
    """Barra de sección azul a todo lo ancho."""
    from fpdf.enums import XPos, YPos
    pdf.ln(1.5)
    pdf.set_fill_color(31, 58, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("ot", "B", 9.5)
    pdf.cell(ancho, 6.5, "  " + titulo.upper(), fill=True,
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(26, 43, 60)
    pdf.set_fill_color(255, 255, 255)   # evita que el azul de la barra "manche" la tabla siguiente


def _pdf_datos(pdf, filas, ancho):
    """Tabla de 2 columnas (etiqueta | valor) para una sección de datos."""
    from fpdf.fonts import FontFace
    estilo_etq = FontFace(emphasis="BOLD", fill_color=(245, 248, 251), color=(51, 71, 91))
    pdf.set_draw_color(227, 232, 238)
    pdf.set_fill_color(255, 255, 255)   # celdas de VALOR en blanco (no heredan el color de la barra)
    pdf.set_font("ot", "", 9)
    with pdf.table(col_widths=(30, 70), width=ancho, first_row_as_headings=False,
                   line_height=5.2, borders_layout="ALL") as table:
        for etiqueta, valor in filas:
            valor = valor if valor not in (None, "", []) else "—"
            row = table.row()
            row.cell(etiqueta, style=estilo_etq)
            row.cell(str(valor))


def _pdf_checklist(pdf, ot, ancho):
    """Tabla del checklist. Pruebas PENDIENTES -> columnas en blanco."""
    from fpdf.fonts import FontFace
    enc = FontFace(emphasis="BOLD", fill_color=(51, 71, 91), color=(255, 255, 255))
    pdf.set_draw_color(227, 232, 238)
    pdf.set_fill_color(255, 255, 255)   # celdas del CUERPO en blanco (no heredan el color de la barra)
    pdf.set_font("ot", "", 8.5)
    with pdf.table(col_widths=(36, 22, 20, 32), width=ancho, first_row_as_headings=True,
                   line_height=5, borders_layout="ALL") as table:
        cab = table.row()
        for titulo in ("Prueba", "Resultado", "Estado", "Observación"):
            cab.cell(titulo, style=enc)
        for p in ot.checklist:
            casilla = "[X]" if p.realizada else "[  ]"
            row = table.row()
            row.cell(f"{casilla} {p.nombre}")
            if getattr(p, "solo_observacion", False):
                # Sin medición: una celda de observación que abarca las 3 columnas.
                row.cell(p.observacion if p.realizada else "", colspan=3)
            elif p.realizada:
                col_txt, col_bg = _color_estado_pdf(p.estado)
                row.cell(f"{p.valor} {p.unidad}".strip())
                row.cell(p.estado, align="CENTER",
                         style=FontFace(emphasis="BOLD", color=col_txt, fill_color=col_bg))
                row.cell(p.observacion or "")
            else:
                row.cell("")   # Resultado en blanco
                row.cell("")   # Estado en blanco
                row.cell("")   # Observación en blanco


def generar_pdf(ot, ruta):
    """Genera el PDF profesional de la OT en `ruta` y devuelve la ruta."""
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF(format="A4", unit="mm")
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(14, 12, 14)
    fuentes = r"C:\Windows\Fonts"
    pdf.add_font("ot", "", os.path.join(fuentes, "arial.ttf"))
    pdf.add_font("ot", "B", os.path.join(fuentes, "arialbd.ttf"))
    pdf.add_page()
    ancho = pdf.epw

    # --- Encabezado corporativo (banda azul, dos líneas) ---
    pdf.set_fill_color(31, 58, 95)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("ot", "B", 13)
    pdf.cell(ancho * 0.62, 8, EMPRESA["nombre"], fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font("ot", "B", 11)
    pdf.cell(ancho * 0.38, 8, "ORDEN DE TRABAJO", fill=True, align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(200, 214, 229)
    pdf.set_font("ot", "", 8)
    pdf.cell(ancho * 0.62, 6, EMPRESA["eslogan"], fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_font("ot", "B", 9)
    pdf.cell(ancho * 0.38, 6, f"N.º {ot.folio}", fill=True, align="R",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # --- Sub-banda: fecha + prioridad + estado ---
    fecha = ot.fecha_creacion.strftime("%d/%m/%Y %H:%M")
    pdf.set_fill_color(238, 243, 248)
    pdf.set_text_color(51, 71, 91)
    pdf.set_font("ot", "", 9)
    pdf.cell(ancho * 0.55, 8, f"  Fecha de emisión: {fecha}", fill=True,
             new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_fill_color(*_hex_a_rgb(_COLOR_PRIORIDAD.get(ot.prioridad.value, "#7f8c8d")))
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("ot", "B", 8)
    pdf.cell(ancho * 0.27, 8, f"PRIORIDAD {ot.prioridad.value.upper()}", fill=True,
             align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.set_fill_color(*_hex_a_rgb(_COLOR_ESTADO_OT.get(ot.estado.value, "#34495e")))
    pdf.cell(ancho * 0.18, 8, ot.estado.value.upper(), fill=True, align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(26, 43, 60)

    # --- Secciones de datos ---
    _pdf_barra(pdf, "Cliente y ubicación", ancho)
    _pdf_datos(pdf, [("Cliente", ot.cliente), ("Planta", ot.planta),
                     ("Ubicación", ot.ubicacion)], ancho)

    _pdf_barra(pdf, "Equipo", ancho)
    filas_equipo = [
        ("Tag / identif.", ot.equipo.tag),
        ("Equipo", ot.equipo.nombre),
        ("Marca / modelo", f"{ot.equipo.marca} {ot.equipo.modelo}".strip()),
    ]
    if getattr(ot.equipo, "serie", ""):
        filas_equipo.append(("Serie", ot.equipo.serie))
    if getattr(ot.equipo, "potencia", ""):
        filas_equipo.append(("Potencia", ot.equipo.potencia))
    if getattr(ot.equipo, "tension", ""):
        filas_equipo.append(("Tensión", ot.equipo.tension))
    if getattr(ot.equipo, "clase_aislamiento", ""):
        filas_equipo.append(("Clase de aislamiento", ot.equipo.clase_aislamiento))
    filas_equipo += [("Área", ot.equipo.area), ("Criticidad", ot.equipo.criticidad)]
    _pdf_datos(pdf, filas_equipo, ancho)

    _pdf_barra(pdf, "Falla y diagnóstico", ancho)
    _pdf_datos(pdf, [
        ("Reporte del operador", ot.reporte_original),
        ("Descripción de la falla", ot.descripcion_falla),
        ("Acciones recomendadas", ot.acciones_recomendadas),
    ], ancho)

    _pdf_barra(pdf, "Trabajo ejecutado", ancho)
    repuestos = ", ".join(ot.repuestos_utilizados) if ot.repuestos_utilizados else "—"
    _pdf_datos(pdf, [
        ("Tipo de mantenimiento", ot.tipo),
        ("Descripción del trabajo", ot.descripcion_trabajo),
        ("Repuestos utilizados", repuestos),
        ("Tiempo estimado", ot.tiempo_estimado),
        ("Técnico asignado", ot.tecnico_asignado),
    ], ancho)

    _pdf_barra(pdf, f"Checklist de pruebas — {ot.tipo_equipo()}", ancho)
    _pdf_checklist(pdf, ot, ancho)

    # --- Firmas ---
    pdf.ln(10)
    w3 = ancho / 3
    pdf.set_text_color(51, 71, 91)
    pdf.set_font("ot", "", 8)
    for _ in range(3):
        pdf.cell(w3, 6, "____________________", align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.ln(5)
    for rol in ("Técnico responsable", "Supervisor de mantenimiento", "Recibido por (cliente)"):
        pdf.cell(w3, 5, rol, align="C", new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.ln(10)

    # --- Pie ---
    pdf.set_font("ot", "", 7)
    pdf.set_text_color(138, 153, 168)
    pdf.multi_cell(ancho, 4,
                   f"Documento generado por Zeus · Agente de mantenimiento industrial · {EMPRESA['contacto']}",
                   align="C")

    pdf.output(ruta)
    return ruta


# === DEMO: genera una OT de motor de ejemplo y la guarda como HTML ==========
if __name__ == "__main__":
    motor = Equipo("MOTOR-12", "Motor trifásico 50 HP",
                   marca="WEG", modelo="W22", area="Compresores", criticidad="alta")
    ot = OrdenTrabajoMotor(
        equipo=motor,
        cliente="Industrias del Norte S.A.",
        planta="Planta Norte",
        ubicacion="Nave 2 — Sala de compresores",
        prioridad=Prioridad.ALTA,
    )
    ot.reporte_original = ("El operador del turno B reporta vibración fuerte y olor a "
                           "quemado en el motor del compresor 2, con zumbido irregular.")
    ot.descripcion_falla = ("Desgaste de rodamientos del lado acople con sobrecalentamiento "
                            "y ligero desbalance del rotor.")
    ot.acciones_recomendadas = ("Sustituir rodamientos lado acople y opuesto, rebalancear "
                                "rotor y verificar alineación con láser.")
    ot.tipo = "correctivo"
    ot.descripcion_trabajo = ("Desmontaje del motor, reemplazo de rodamientos 6209-2RS, "
                             "limpieza de devanados, rebalanceo de rotor y alineación láser.")
    ot.repuestos_utilizados = ["Rodamiento SKF 6209-2RS (x2)",
                               "Grasa SKF LGHP 2 (200 g)",
                               "Solvente dieléctrico (1 L)"]
    ot.tiempo_estimado = "4.0 h"
    ot.tecnico_asignado = "Ing. Jayro Rojas"

    # Resultados de las pruebas (motor ya reparado y validado)
    ot.registrar_prueba("Inspección visual", "Sin daños visibles", "OK")
    ot.registrar_prueba("Medición de aislamiento", 520, "OK", "Mínimo aceptable 100 MΩ")
    ot.registrar_prueba("Resistencia de devanados", 0.42, "OK", "Equilibrada entre fases")
    ot.registrar_prueba("Vibración", 2.1, "OK", "Límite ISO 4.5 mm/s")
    ot.registrar_prueba("Temperatura", 62, "OK")
    ot.registrar_prueba("Alineación", 0.04, "OK", "Tolerancia 0.05 mm")
    ot.registrar_prueba("Prueba en vacío", 11.8, "OK")
    ot.registrar_prueba("Prueba con carga", 47.5, "OK", "Corriente nominal 48 A")

    html = generar_html(ot)

    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    salida_dir = os.path.join(base, "salida")
    os.makedirs(salida_dir, exist_ok=True)
    ruta = os.path.join(salida_dir, f"{ot.folio}.html")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(html)
    ruta_pdf = os.path.join(salida_dir, f"{ot.folio}.pdf")
    generar_pdf(ot, ruta_pdf)

    print("Documento generado:", ruta)
    print("PDF generado:", ruta_pdf)
