"""
modelos.py · Clases POO del agente Zeus (generador de órdenes de trabajo).

Estructura de clases:
    Prioridad / EstadoOT ... enumeraciones (valores cerrados y seguros)
    Equipo ................. el activo físico de la planta
    Prueba ................. un renglón del checklist (con su medición)
    OrdenDeTrabajo ......... CLASE BASE: todo lo común a cualquier OT
        └── OrdenTrabajoMotor ... HIJA: hereda todo y aporta el checklist de motor
"""

from datetime import datetime
from enum import Enum

import folios   # memoria persistente del folio (data/contador_folios.json)


# === ENUMERACIONES ===========================================================
# Un Enum es una lista de valores fijos. Evita errores de dedo ("ata" en vez de
# "alta") porque solo se puede usar uno de los valores definidos.

class Prioridad(Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "crítica"


class EstadoOT(Enum):
    ABIERTA = "abierta"
    EN_PROCESO = "en proceso"
    FINALIZADA = "finalizada"


# === EQUIPO ==================================================================
class Equipo:
    """Un activo físico de la planta: una bomba, un motor, un compresor, etc."""

    def __init__(self, tag, nombre, marca="", modelo="", area="", criticidad="media",
                 serie="", potencia="", tension="", clase_aislamiento=""):
        self.tag = tag                 # ID único, ej. "MOTOR-12"
        self.nombre = nombre           # ej. "Motor trifásico 50 HP"
        self.marca = marca             # ej. "WEG"
        self.modelo = modelo           # ej. "W22"
        self.area = area               # ej. "Compresores"
        self.criticidad = criticidad   # "baja" | "media" | "alta"
        self.serie = serie             # número de serie (placa), ej. "SN-123456"
        self.potencia = potencia       # capacidad nominal, ej. "250 KVA"
        self.tension = tension         # tensión nominal, ej. "13.8 kV"
        self.clase_aislamiento = clase_aislamiento   # clase térmica: A/E/B/F/H (motores)

    def descripcion(self):
        marca_modelo = f"{self.marca} {self.modelo}".strip()
        marca_modelo = f" {marca_modelo}" if marca_modelo else ""
        return f"[{self.tag}] {self.nombre}{marca_modelo} — área: {self.area}"


# === PRUEBA (un renglón del checklist) ======================================
class Prueba:
    """Una prueba técnica del checklist. Guarda si se hizo y qué se midió."""

    def __init__(self, nombre, unidad="", solo_observacion=False):
        self.nombre = nombre
        self.unidad = unidad
        self.solo_observacion = solo_observacion   # True: sin medición, solo observación
        self.realizada = False
        self.valor = None
        self.estado = "N/A"        # "OK" | "fuera de rango" | "N/A"
        self.observacion = ""

    def registrar(self, valor, estado="OK", observacion=""):
        """Marca la prueba como realizada y guarda la medición."""
        self.realizada = True
        self.valor = valor
        self.estado = estado
        self.observacion = observacion

    def __str__(self):
        # __str__ define cómo se ve la prueba al imprimirla con print().
        casilla = "[x]" if self.realizada else "[ ]"
        if self.realizada:
            medicion = f"{self.valor} {self.unidad}".strip()
        else:
            medicion = "—"
        obs = f" · {self.observacion}" if self.observacion else ""
        return f"{casilla} {self.nombre}: {medicion} ({self.estado}){obs}"


# === ORDEN DE TRABAJO (CLASE BASE) ==========================================
class OrdenDeTrabajo:
    """Lo COMÚN a cualquier orden de trabajo, sea de motor, bomba, etc.

    Las clases hijas (OrdenTrabajoMotor, ...) heredan todo esto y solo
    definen SU checklist y SU tipo de equipo.
    """

    # Campos OBLIGATORIOS por defecto (claves de campo, ver mensajes.py). Cada
    # tipo de OT puede redefinir esta lista según lo que su equipo necesite.
    CAMPOS_OBLIGATORIOS = ["cliente", "planta", "ubicacion", "equipo", "tag",
                           "marca", "modelo", "area", "criticidad"]

    def __init__(self, equipo, cliente="", planta="", ubicacion="",
                 prioridad=Prioridad.MEDIA, tipo="correctivo"):
        self.fecha_creacion = datetime.now()
        self.folio = self._generar_folio()
        self.estado = EstadoOT.ABIERTA
        self.chat_id = None            # dueño: chat de Telegram que reportó la OT

        # --- Cliente / ubicación ---
        self.cliente = cliente
        self.planta = planta
        self.ubicacion = ubicacion

        # --- Equipo (COMPOSICIÓN: una OT "tiene un" objeto Equipo) ---
        self.equipo = equipo

        # --- Clasificación ---
        self.prioridad = prioridad     # un valor de Prioridad
        self.tipo = tipo               # "correctivo" | "preventivo"

        # --- Falla / diagnóstico ---
        self.reporte_original = ""     # texto crudo del operador
        self.descripcion_falla = ""
        self.acciones_recomendadas = ""   # vendrá del RAG (manual)

        # --- Trabajo ejecutado ---
        self.descripcion_trabajo = ""
        self.repuestos_utilizados = []
        self.tiempo_estimado = ""
        self.tecnico_asignado = ""

        # --- Pruebas (POLIMORFISMO: cada hija arma SU checklist) ---
        self.checklist = self._crear_checklist()

        # --- Cierre ---
        self.observaciones = ""
        self.fecha_cierre = None

    def _generar_folio(self):
        """Pide el siguiente folio ÚNICO a la memoria persistente (folios.py).

        El correlativo vive en disco (data/contador_folios.json), por eso NO se
        reinicia al cerrar el programa ni la sesión de Claude. Se reinicia solo
        al cambiar de año.
        """
        return folios.siguiente_folio(self.fecha_creacion.year)

    def _crear_checklist(self):
        """La BASE no sabe qué pruebas tocan. Cada hija lo sobrescribe."""
        return []

    def tipo_equipo(self):
        """Método POLIMÓRFICO: cada hija dice a qué equipo atiende."""
        return "genérico"

    def registrar_prueba(self, nombre, valor, estado="OK", observacion=""):
        """Busca una prueba del checklist por nombre y guarda su medición."""
        objetivo = nombre.strip().casefold()
        for prueba in self.checklist:
            if prueba.nombre.casefold() == objetivo:
                prueba.registrar(valor, estado, observacion)
                return
        raise ValueError(f"La prueba '{nombre}' no existe en este checklist.")

    def finalizar(self, observaciones=""):
        """Da por TERMINADA la OT: estado FINALIZADA y fecha de cierre."""
        self.estado = EstadoOT.FINALIZADA
        if observaciones:
            self.observaciones = observaciones
        self.fecha_cierre = datetime.now()

    def resumen(self):
        return (f"{self.folio} · OT de {self.tipo_equipo()} · {self.equipo.tag} · "
                f"prioridad {self.prioridad.value} · estado {self.estado.value}")

    def to_dict(self):
        """Serializa la OT COMPLETA a un dict (para guardarla en JSON y poder
        reconstruirla luego con crear_desde_dict)."""
        return {
            "clase": type(self).__name__,
            "folio": self.folio,
            "fecha_creacion": self.fecha_creacion.isoformat(),
            "estado": self.estado.name,
            "chat_id": self.chat_id,
            "cliente": self.cliente,
            "planta": self.planta,
            "ubicacion": self.ubicacion,
            "prioridad": self.prioridad.name,
            "tipo": self.tipo,
            "equipo": {
                "tag": self.equipo.tag, "nombre": self.equipo.nombre,
                "marca": self.equipo.marca, "modelo": self.equipo.modelo,
                "area": self.equipo.area, "criticidad": self.equipo.criticidad,
                "serie": self.equipo.serie, "potencia": self.equipo.potencia,
                "tension": self.equipo.tension,
                "clase_aislamiento": self.equipo.clase_aislamiento,
            },
            "reporte_original": self.reporte_original,
            "descripcion_falla": self.descripcion_falla,
            "acciones_recomendadas": self.acciones_recomendadas,
            "descripcion_trabajo": self.descripcion_trabajo,
            "repuestos_utilizados": self.repuestos_utilizados,
            "tiempo_estimado": self.tiempo_estimado,
            "tecnico_asignado": self.tecnico_asignado,
            "checklist": [
                {"nombre": p.nombre, "unidad": p.unidad,
                 "solo_observacion": p.solo_observacion, "realizada": p.realizada,
                 "valor": p.valor, "estado": p.estado, "observacion": p.observacion}
                for p in self.checklist
            ],
            "observaciones": self.observaciones,
            "fecha_cierre": self.fecha_cierre.isoformat() if self.fecha_cierre else None,
        }


# === ORDEN DE TRABAJO DE MOTOR (CLASE HIJA) =================================
class OrdenTrabajoMotor(OrdenDeTrabajo):
    """HERENCIA: 'OrdenTrabajoMotor(OrdenDeTrabajo)' significa que hereda TODO
    lo de OrdenDeTrabajo. Aquí solo cambiamos lo propio del motor."""

    # El motor suma 'clase_aislamiento' a los datos obligatorios.
    CAMPOS_OBLIGATORIOS = ["cliente", "planta", "ubicacion", "equipo", "tag",
                           "marca", "modelo", "clase_aislamiento", "area", "criticidad"]

    def _crear_checklist(self):
        # POLIMORFISMO: sobrescribe el método de la base con el checklist de motor.
        return [
            Prueba("Inspección visual"),
            Prueba("Medición de aislamiento", "MΩ"),
            Prueba("Resistencia de devanados", "Ω"),
            Prueba("Vibración", "mm/s"),
            Prueba("Temperatura", "°C"),
            Prueba("Alineación", "mm"),
            Prueba("Prueba en vacío", "A"),
            Prueba("Prueba con carga", "A"),
        ]

    def tipo_equipo(self):
        return "Motor"


# === ORDEN DE TRABAJO DE GENERADOR (CLASE HIJA) ============================
class OrdenTrabajoGenerador(OrdenDeTrabajo):
    """HIJA: OT para el mantenimiento de un GENERADOR ELÉCTRICO (planta de
    emergencia). Igual que el motor, hereda TODO y solo aporta SU checklist, SU
    tipo de equipo y SUS campos obligatorios (que suman serie, potencia,
    operaciones realizadas y repuestos utilizados)."""

    CAMPOS_OBLIGATORIOS = ["cliente", "planta", "ubicacion", "equipo", "tag",
                           "marca", "modelo", "serie", "potencia",
                           "operaciones", "repuestos"]

    def _crear_checklist(self):
        # POLIMORFISMO: checklist propio del mantenimiento de un generador.
        return [
            Prueba("Inspección general"),
            Prueba("Nivel de aceite del motor"),
            Prueba("Filtros (aire, aceite, combustible)"),
            Prueba("Baterías y cargador"),
            Prueba("Sistema de combustible"),
            Prueba("Sistema de escape"),
            Prueba("Prueba de arranque"),
            Prueba("Prueba bajo carga"),
            Prueba("Transferencia automática (ATS)"),
        ]

    def tipo_equipo(self):
        return "Generador eléctrico"


# === ORDEN DE TRABAJO DE TRANSFORMADOR (CLASE HIJA) ========================
class OrdenTrabajoTransformador(OrdenDeTrabajo):
    """HIJA: OT para el MONTAJE (puesta en servicio) de un TRANSFORMADOR. Suma a
    los datos del equipo la tensión (kV) y su checklist de pruebas eléctricas.
    Las DOS primeras pruebas son inspecciones SIN medición: solo llevan
    observación (Prueba con solo_observacion=True)."""

    CAMPOS_OBLIGATORIOS = ["cliente", "planta", "ubicacion", "equipo",
                           "marca", "modelo", "serie", "potencia", "tension",
                           "operaciones", "repuestos"]

    def _crear_checklist(self):
        return [
            Prueba("Inspección de instalación", solo_observacion=True),
            Prueba("Verificación de conexiones", solo_observacion=True),
            Prueba("Relación de transformación (TTR)"),
            Prueba("Resistencia de aislamiento"),
            Prueba("Prueba de rigidez dieléctrica"),
            Prueba("Puesta a tierra"),
            Prueba("Verificación de protecciones"),
        ]

    def tipo_equipo(self):
        return "Transformador"


# === RECONSTRUCCIÓN desde dict (para persistir y releer las OT en disco) =====
_CLASES_OT = {
    "OrdenDeTrabajo": OrdenDeTrabajo,
    "OrdenTrabajoMotor": OrdenTrabajoMotor,
    "OrdenTrabajoGenerador": OrdenTrabajoGenerador,
    "OrdenTrabajoTransformador": OrdenTrabajoTransformador,
}


def crear_desde_dict(data):
    """Reconstruye una OT desde el dict de to_dict(), SIN consumir un folio nuevo
    ni rehacer el checklist: restaura el estado guardado tal cual."""
    Clase = _CLASES_OT.get(data.get("clase"), OrdenDeTrabajo)
    ot = Clase.__new__(Clase)            # instancia SIN llamar a __init__

    eq = data["equipo"]
    ot.equipo = Equipo(eq["tag"], eq["nombre"], eq["marca"], eq["modelo"],
                       eq["area"], eq["criticidad"], eq["serie"], eq["potencia"],
                       eq["tension"], eq.get("clase_aislamiento", ""))

    ot.folio = data["folio"]
    ot.fecha_creacion = datetime.fromisoformat(data["fecha_creacion"])
    ot.estado = EstadoOT[data["estado"]]
    ot.chat_id = data.get("chat_id")
    ot.cliente = data["cliente"]
    ot.planta = data["planta"]
    ot.ubicacion = data["ubicacion"]
    ot.prioridad = Prioridad[data["prioridad"]]
    ot.tipo = data["tipo"]
    ot.reporte_original = data["reporte_original"]
    ot.descripcion_falla = data["descripcion_falla"]
    ot.acciones_recomendadas = data["acciones_recomendadas"]
    ot.descripcion_trabajo = data["descripcion_trabajo"]
    ot.repuestos_utilizados = list(data["repuestos_utilizados"])
    ot.tiempo_estimado = data["tiempo_estimado"]
    ot.tecnico_asignado = data["tecnico_asignado"]
    ot.observaciones = data["observaciones"]
    ot.fecha_cierre = datetime.fromisoformat(data["fecha_cierre"]) if data.get("fecha_cierre") else None

    ot.checklist = []
    for d in data["checklist"]:
        p = Prueba(d["nombre"], d.get("unidad", ""), d.get("solo_observacion", False))
        p.realizada = d["realizada"]
        p.valor = d["valor"]
        p.estado = d["estado"]
        p.observacion = d["observacion"]
        ot.checklist.append(p)

    return ot


# === PRUEBA RÁPIDA (solo corre si ejecutas este archivo directamente) =======
if __name__ == "__main__":
    # En consolas de Windows (cp1252), símbolos como Ω rompen print(); UTF-8 lo evita.
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    # 1) Creamos el equipo (con marca y modelo)
    motor = Equipo("MOTOR-12", "Motor trifásico 50 HP",
                   marca="WEG", modelo="W22", area="Compresores", criticidad="alta")

    # 2) Generamos una orden de trabajo DE MOTOR
    ot = OrdenTrabajoMotor(
        equipo=motor,
        cliente="Industrias del Norte S.A.",
        planta="Planta Norte",
        ubicacion="Nave 2 - Sala de compresores",
        prioridad=Prioridad.ALTA,
    )
    ot.descripcion_falla = "Vibración excesiva y olor a quemado del lado del acople."
    ot.descripcion_trabajo = "Cambio de rodamientos y rebalanceo del rotor."
    ot.repuestos_utilizados = ["Rodamiento 6209-2RS (x2)", "Grasa SKF LGHP 2"]
    ot.tecnico_asignado = "J. Rojas"

    # 3) Registramos algunas pruebas del checklist
    ot.registrar_prueba("Medición de aislamiento", 520, "OK", "Mínimo aceptable 100 MΩ")
    ot.registrar_prueba("Vibración", 7.2, "fuera de rango", "Límite ISO 4.5 mm/s")
    ot.registrar_prueba("Temperatura", 68, "OK")

    # 4) Mostramos la OT
    print(ot.resumen())
    print("Equipo :", ot.equipo.descripcion())
    print("Cliente:", ot.cliente, "—", ot.planta, "/", ot.ubicacion)
    print("Falla  :", ot.descripcion_falla)
    print("\nChecklist de pruebas:")
    for prueba in ot.checklist:
        print("  ", prueba)
