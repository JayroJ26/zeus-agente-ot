"""
mensajes.py · Diálogo de Zeus con el operador por Telegram (textos + parsers).

Aquí vive el "guion" de la conversación, separado del CANAL (telegram_bot.py) y
de los DATOS (modelos.py):

  1) solicitar_datos(ot)   -> pide los campos OBLIGATORIOS que falten en la OT.
  2) aviso_ot(ot)          -> avisa que el checklist va EN BLANCO y explica, con
                              un ejemplo por prueba, cómo reportar cada resultado.
  3) aplicar_datos(ot, txt)      -> vuelca las respuestas del operador a la OT.
  4) aplicar_resultado(ot, txt)  -> registra el resultado de UNA prueba.

Los mensajes usan el HTML de Telegram (<b>negrita</b>, <i>cursiva</i>, <code>).
Las comparaciones de nombres son TOLERANTES (sin acentos ni mayúsculas), porque
el operador casi nunca escribe las tildes.
"""

import html
import unicodedata


# === Utilidades de comparación tolerante ====================================
def _norm(texto):
    """minúsculas y SIN acentos: 'Vibración' y 'vibracion' se comparan igual."""
    t = unicodedata.normalize("NFD", str(texto).strip().casefold())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def _vacio(valor):
    """True si el campo está vacío o marcado como '(por confirmar)'."""
    if not valor:
        return True
    return "por confirmar" in str(valor).strip().casefold()


# === Campos OBLIGATORIOS de la OT ===========================================
# Cada campo sabe LEERSE y ESCRIBIRSE en la OT. 'marca/modelo' es doble.

def _set_repuestos(ot, v):
    # "Aceite 15W40; Filtro de aire, Filtro de aceite"  ->  lista de repuestos
    ot.repuestos_utilizados = [x.strip() for x in v.replace(";", ",").split(",") if x.strip()]


# Registro de TODOS los campos posibles: (clave, etiqueta, leer, escribir).
# QUÉ campos son obligatorios lo decide cada OT en su CAMPOS_OBLIGATORIOS.
CAMPOS = [
    ("cliente",     "Cliente",                lambda o: o.cliente,             lambda o, v: setattr(o, "cliente", v)),
    ("planta",      "Planta",                 lambda o: o.planta,              lambda o, v: setattr(o, "planta", v)),
    ("ubicacion",   "Ubicación",              lambda o: o.ubicacion,           lambda o, v: setattr(o, "ubicacion", v)),
    ("equipo",      "Equipo (tipo)",          lambda o: o.equipo.nombre,       lambda o, v: setattr(o.equipo, "nombre", v)),
    ("tag",         "Tag / identificador",    lambda o: o.equipo.tag,          lambda o, v: setattr(o.equipo, "tag", v)),
    ("marca",       "Marca",                  lambda o: o.equipo.marca,        lambda o, v: setattr(o.equipo, "marca", v)),
    ("modelo",      "Modelo",                 lambda o: o.equipo.modelo,       lambda o, v: setattr(o.equipo, "modelo", v)),
    ("serie",       "Serie",                  lambda o: o.equipo.serie,        lambda o, v: setattr(o.equipo, "serie", v)),
    ("potencia",    "Potencia (KVA)",         lambda o: o.equipo.potencia,     lambda o, v: setattr(o.equipo, "potencia", v)),
    ("tension",     "Tensión (kV)",           lambda o: o.equipo.tension,      lambda o, v: setattr(o.equipo, "tension", v)),
    ("clase_aislamiento", "Clase de aislamiento (A/E/B/F/H)", lambda o: o.equipo.clase_aislamiento, lambda o, v: setattr(o.equipo, "clase_aislamiento", v)),
    ("area",        "Área",                   lambda o: o.equipo.area,         lambda o, v: setattr(o.equipo, "area", v)),
    ("criticidad",  "Criticidad",             lambda o: o.equipo.criticidad,   lambda o, v: setattr(o.equipo, "criticidad", v)),
    ("operaciones", "Operaciones realizadas", lambda o: o.descripcion_trabajo, lambda o, v: setattr(o, "descripcion_trabajo", v)),
    ("repuestos",   "Repuestos utilizados",   lambda o: ", ".join(o.repuestos_utilizados), _set_repuestos),
]

# Valores de ejemplo para ilustrar la respuesta de cada dato.
_EJEMPLO_DATO = {
    "cliente": "Green Valley",
    "planta": "Planta Sur",
    "ubicacion": "Casa de máquinas",
    "tag": "GEN-01",
    "marca": "Cummins",
    "modelo": "C250 D5",
    "serie": "SN-123456",
    "potencia": "250 KVA",
    "tension": "13.8 kV",
    "clase_aislamiento": "F",
    "area": "Energía",
    "criticidad": "alta",
    "operaciones": "Cambio de aceite y filtros; prueba bajo carga",
    "repuestos": "Aceite 15W40 (12 L), Filtro de aceite, Filtro de aire",
}


def _ejemplo_dato(clave, ot):
    """Valor de ejemplo para un campo. Para 'equipo' usa el tipo real de la OT."""
    if clave == "equipo":
        return ot.tipo_equipo()
    return _EJEMPLO_DATO.get(clave, "...")


def campos_faltantes(ot):
    """Devuelve [(clave, etiqueta), ...] de los campos OBLIGATORIOS de ESTA OT
    (según ot.CAMPOS_OBLIGATORIOS) que están vacíos o '(por confirmar)'."""
    registro = {clave: (etiq, get) for clave, etiq, get, _set in CAMPOS}
    obligatorios = getattr(type(ot), "CAMPOS_OBLIGATORIOS", [c for c, *_ in CAMPOS])
    faltan = []
    for clave in obligatorios:
        if clave in registro and _vacio(registro[clave][1](ot)):
            faltan.append((clave, registro[clave][0]))
    return faltan


def solicitar_datos(ot):
    """Mensaje que pide los datos obligatorios que faltan. None si no falta nada."""
    faltan = campos_faltantes(ot)
    if not faltan:
        return None
    pedido = "\n".join(f"• <b>{etiq}</b>" for _c, etiq in faltan)
    ejemplo = "\n".join(f"{etiq}: {_ejemplo_dato(clave, ot)}" for clave, etiq in faltan)
    return (
        f"📝 Para completar la orden <b>{ot.folio}</b> necesito estos datos "
        f"(responde uno por línea, o un mensaje por dato):\n\n"
        f"{pedido}\n\n"
        f"<b>Ejemplo:</b>\n<code>{html.escape(ejemplo)}</code>"
    )


# === Checklist: aviso de columnas en blanco + ejemplo por prueba ============
_EJEMPLO_VALOR = {
    # --- Motor ---
    "inspeccion visual": "sin daños",
    "medicion de aislamiento": "520",
    "resistencia de devanados": "0.42",
    "vibracion": "2.1",
    "temperatura": "62",
    "alineacion": "0.04",
    "prueba en vacio": "11.8",
    "prueba con carga": "47.5",
    # --- Generador ---
    "inspeccion general": "correcto",
    "nivel de aceite del motor": "OK",
    "filtros (aire, aceite, combustible)": "limpios",
    "baterias y cargador": "13.8 V",
    "sistema de combustible": "sin fugas",
    "sistema de escape": "sin fugas",
    "prueba de arranque": "arranca en 3 s",
    "prueba bajo carga": "230 kW estable",
    "transferencia automatica (ats)": "OK en 8 s",
    # --- Transformador ---
    "relacion de transformacion (ttr)": "0.3 % de error",
    "resistencia de aislamiento": "2 GΩ",
    "prueba de rigidez dielectrica": "soporta 34 kV / 1 min",
    "puesta a tierra": "0.8 Ω",
    "verificacion de protecciones": "OK",
}


def ejemplo_pruebas(ot):
    """Una línea de ejemplo por CADA prueba del checklist de la OT."""
    lineas = []
    for p in ot.checklist:
        if getattr(p, "solo_observacion", False):
            lineas.append(f"{p.nombre}: (escribe aquí tu observación, sin medición)")
        else:
            valor = _EJEMPLO_VALOR.get(_norm(p.nombre), "valor")
            unidad = f" {p.unidad}" if p.unidad else ""
            lineas.append(f"{p.nombre}: {valor}{unidad} | OK | (observación opcional)")
    return "\n".join(lineas)


def aviso_ot(ot):
    """Mensaje que acompaña a la OT: checklist en blanco + cómo reportar pruebas."""
    return (
        f"📋 La orden <b>{ot.folio}</b> se generó con el checklist <b>en blanco</b>: "
        f"las columnas <i>Resultado</i>, <i>Estado</i> y <i>Observación</i> van "
        f"vacías para que el técnico las complete tras el diagnóstico en campo.\n\n"
        f"Reporta <b>cada prueba con un mensaje</b>, en este formato:\n"
        f"<code>Prueba: valor unidad | estado | observación</code>\n"
        f"• <b>estado</b>: OK o «fuera de rango»\n"
        f"• <b>observación</b>: opcional\n\n"
        f"💡 O regístralas <b>paso a paso</b>: escribe <b>/pruebas</b> y te pregunto una por una.\n\n"
        f"<b>Ejemplos para este equipo ({html.escape(ot.tipo_equipo())}):</b>\n"
        f"<code>{html.escape(ejemplo_pruebas(ot))}</code>"
    )


# === PARSERS: aplican las respuestas del operador a la OT ====================
def _buscar_campo(etiqueta):
    objetivo = _norm(etiqueta)
    for campo in CAMPOS:
        clave, etiq, _get, _set = campo
        if objetivo == _norm(clave) or objetivo == _norm(etiq) or objetivo in _norm(etiq):
            return campo
    return None


def aplicar_datos(ot, texto):
    """Aplica respuestas 'Campo: valor' (una o varias líneas) a la OT.

    Devuelve la lista de claves aplicadas (ignora líneas sin ':' o sin valor).
    """
    aplicados = []
    for linea in texto.splitlines():
        if ":" not in linea:
            continue
        etiqueta, valor = linea.split(":", 1)
        valor = valor.strip()
        campo = _buscar_campo(etiqueta)
        if not valor or campo is None:
            continue
        clave, _etiq, _get, _set = campo
        _set(ot, valor)
        aplicados.append(clave)
    return aplicados


def _buscar_prueba(ot, nombre):
    objetivo = _norm(nombre)
    for p in ot.checklist:
        if _norm(p.nombre) == objetivo:
            return p
    return None


def _normalizar_estado(estado):
    """Lleva lo que escriba el operador al estado canónico del checklist."""
    e = _norm(estado)
    if e in ("", "ok", "bien", "correcto", "normal"):
        return "OK"
    if "fuera" in e or "rango" in e or "mal" in e or "falla" in e:
        return "fuera de rango"
    return estado.strip()


def aplicar_resultado(ot, texto):
    """Parsea 'Prueba: valor unidad | estado | observación' y lo registra en la OT.

    Devuelve el nombre de la prueba registrada.
    Lanza ValueError si el formato es inválido o la prueba no existe.
    """
    if ":" not in texto:
        raise ValueError("Formato inválido: usa 'Prueba: valor | estado | observación'.")
    nombre, resto = texto.split(":", 1)

    prueba = _buscar_prueba(ot, nombre)
    if prueba is None:
        disponibles = ", ".join(p.nombre for p in ot.checklist)
        raise ValueError(f"La prueba '{nombre.strip()}' no está en el checklist. "
                         f"Pruebas válidas: {disponibles}.")

    # Pruebas SIN medición (inspecciones): todo lo que sigue a ':' es observación.
    if getattr(prueba, "solo_observacion", False):
        ot.registrar_prueba(prueba.nombre, "", "N/A", resto.replace("|", " ").strip())
        return prueba.nombre

    partes = [p.strip() for p in resto.split("|")]
    valor = partes[0]
    estado = partes[1] if len(partes) > 1 else "OK"
    observacion = partes[2] if len(partes) > 2 else ""
    if "observacion opcional" in _norm(observacion):   # el operador dejó el placeholder del ejemplo
        observacion = ""
    if not valor:
        raise ValueError("Falta el valor de la prueba.")

    # Si el valor trae la unidad ('520 MΩ'), se la quitamos: la OT ya la conoce.
    u = prueba.unidad
    if u and len(valor) >= len(u) and valor[-len(u):].casefold() == u.casefold():
        valor = valor[:-len(u)].strip()

    ot.registrar_prueba(prueba.nombre, valor, _normalizar_estado(estado), observacion)
    return prueba.nombre


def aplicar_resultados(ot, texto):
    """Aplica varias pruebas (una por línea). Devuelve [(nombre|línea, error|None)]."""
    resultados = []
    for linea in texto.splitlines():
        linea = linea.strip()
        if not linea or ":" not in linea:
            continue
        try:
            resultados.append((aplicar_resultado(ot, linea), None))
        except ValueError as error:
            resultados.append((linea, str(error)))
    return resultados


# === Detección de comandos del operador =====================================
def es_finalizar(texto):
    """True si el mensaje pide dar por TERMINADA/finalizada la orden de trabajo."""
    t = _norm(texto)
    claves = ("terminad", "termine", "termino", "finaliz", "complet",
              "cerrar la orden", "cerrar la ot", "orden lista", "ya acab", "ya quedo")
    return any(c in t for c in claves)


def es_solicitud_ot(texto):
    """True si el operador PIDE que le manden el PDF de su OT (no es un reporte nuevo)."""
    t = _norm(texto)
    menciona = any(k in t for k in ("orden de trabajo", "la orden", "mi orden",
                                    "el pdf", "la ot", "mi ot", "ot-"))
    pide = any(k in t for k in ("manda", "envia", "reenvia", "pasa", "muestra",
                                "ver la", "ver mi", "quiero ver", "dame",
                                "necesito ver", "mi copia"))
    return menciona and pide


# === DEMO/PRUEBA: corre solo si ejecutas este archivo directamente ==========
if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")   # consola Windows -> UTF-8
    except AttributeError:
        pass

    from modelos import Equipo, OrdenTrabajoMotor, Prioridad

    # OT recién razonada de un reporte ambiguo: faltan varios datos.
    motor = Equipo(tag="(por confirmar)", nombre="Motor de línea 2",
                   marca="(por confirmar)", modelo="", area="Línea 2", criticidad="media")
    ot = OrdenTrabajoMotor(equipo=motor, cliente="Green Valley", planta="(por confirmar)",
                           ubicacion="Línea 2", prioridad=Prioridad.ALTA)

    print("===== CAMPOS FALTANTES =====")
    print(campos_faltantes(ot))

    print("\n===== MENSAJE: SOLICITAR DATOS =====")
    print(solicitar_datos(ot))

    print("\n===== MENSAJE: AVISO OT (checklist en blanco + ejemplos) =====")
    print(aviso_ot(ot))

    print("\n===== PARSER: aplicar datos =====")
    aplicados = aplicar_datos(ot, "Planta: Planta Sur\nMarca/modelo: WEG W22\nTag: MOTOR-23")
    print("aplicados:", aplicados)
    print("faltan ahora:", campos_faltantes(ot))

    print("\n===== PARSER: aplicar resultado de una prueba =====")
    registrada = aplicar_resultado(ot, "Vibracion: 2.1 mm/s | fuera de rango | supera ISO 4.5")
    print("registrada:", registrada)
    for p in ot.checklist:
        if p.realizada:
            print("  ->", p)
