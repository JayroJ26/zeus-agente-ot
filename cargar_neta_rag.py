# -*- coding: utf-8 -*-
"""
cargar_neta_rag.py · Carga al RAG de Zeus las secciones clave del estandar
ANSI/NETA ATS-2009 (Acceptance Testing Specifications for Electrical Power
Equipment and Systems), traducidas/condensadas al espanol.

El PDF original esta en ingles; la busqueda del RAG es por palabra clave en
espanol, asi que NO se trocea el PDF crudo: se cargan fragmentos fieles y
limpios, ya traducidos, con su tipo_equipo y palabras clave (tema). Cada
fragmento captura el contenido accionable: inspeccion visual/mecanica,
pruebas electricas y criterios de aceptacion.

Idempotente: si la fuente ya esta en el RAG, no vuelve a cargar.
Uso:  .venv\\Scripts\\python -X utf8 cargar_neta_rag.py
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

import rag

FUENTE = "ANSI/NETA ATS-2009 - Pruebas de aceptacion de equipo electrico"

# (tipo_equipo, tema, texto)
FRAGMENTOS = [
    # ===================== TRANSFORMADOR =====================
    ("Transformador", "transformador seco baja tension inspeccion visual mecanica",
     "Transformador seco tipo aire de baja tension (devanados <=600 V y <=167 kVA monofasico o "
     "<=500 kVA trifasico). Inspeccion visual y mecanica: comparar la placa de datos con planos y "
     "especificaciones; revisar condicion fisica y mecanica; verificar anclaje, alineacion y puesta a "
     "tierra; comprobar que los soportes elasticos esten libres y que se hayan retirado los soportes de "
     "embarque; verificar que la unidad este limpia; inspeccionar las conexiones electricas atornilladas "
     "(ohmimetro de baja resistencia, torque con llave calibrada o termografia); verificar que las tomas "
     "(taps) queden como se especifico."),
    ("Transformador", "transformador seco baja tension pruebas electricas aislamiento relacion transformacion",
     "Transformador seco de baja tension. Pruebas electricas: medir resistencia de las conexiones "
     "atornilladas con ohmimetro de baja resistencia; resistencia de aislamiento devanado-a-devanado y "
     "cada devanado-a-tierra (calcular el indice de polarizacion); prueba de relacion de transformacion "
     "(TTR) en todas las posiciones de tomas; verificar la tension secundaria correcta fase-a-fase y "
     "fase-a-neutro despues de energizar y antes de cargar."),
    ("Transformador", "transformador seco baja tension criterios aceptacion valores",
     "Transformador seco de baja tension, criterios de aceptacion: la resistencia de aislamiento minima "
     "debe cumplir el dato del fabricante (o Tabla 100.5); el indice de polarizacion no debe ser menor a "
     "1.0; los resultados de TTR no deben desviarse mas de medio por ciento (0.5%) respecto a las bobinas "
     "adyacentes o a la relacion calculada; las tensiones secundarias deben concordar con la placa; "
     "investigar conexiones cuya resistencia se desvie mas de 50% del valor mas bajo similar."),
    ("Transformador", "transformador seco grande media tension inspeccion ventiladores temperatura pararrayos",
     "Transformador seco tipo aire grande (devanados >600 V, o BT mayor a 167 kVA monofasico / 500 kVA "
     "trifasico). Inspeccion visual y mecanica: ademas de placa, condicion, anclaje y limpieza, verificar "
     "ajustes de control y alarma en los indicadores de temperatura; verificar que los ventiladores de "
     "enfriamiento operen y que sus motores tengan la proteccion de sobrecorriente correcta; inspeccionar "
     "conexiones atornilladas; verificar las tomas y la presencia de pararrayos (apartarrayos)."),
    ("Transformador", "transformador seco grande pruebas factor potencia excitacion nucleo tension aplicada",
     "Transformador seco grande. Pruebas electricas: resistencia de aislamiento devanado-devanado y "
     "devanado-tierra con indice de polarizacion; factor de potencia o factor de disipacion en todos los "
     "devanados (prueba tip-up en devanados >2.5 kV); relacion de transformacion (TTR) en todas las tomas; "
     "corriente de excitacion por fase; resistencia de cada devanado en cada toma; resistencia de "
     "aislamiento del nucleo a 500 V cc si es aislado; prueba de tension aplicada (dielectric withstand) a "
     "los devanados contra tierra."),
    ("Transformador", "transformador seco grande criterios factor potencia tip-up nucleo",
     "Transformador seco grande, criterios: factor de potencia CHL esperado <=2.0% en transformadores de "
     "potencia y <=5.0% en transformadores de distribucion; tip-up de FP que exceda 1.0% se investiga; "
     "TTR dentro de +/-0.5%; resistencia de devanados (corregida por temperatura) dentro de 1% de "
     "resultados previos; resistencia de aislamiento del nucleo >= 1 megohm a 500 V cc; la tension "
     "soportada AC no debe exceder 75% de la tension de prueba de fabrica por un minuto; indice de "
     "polarizacion >= 1.0."),
    ("Transformador", "transformador liquido aceite inspeccion buchholz nivel pcb boquillas",
     "Transformador sumergido en liquido (aceite). Inspeccion visual y mecanica: comparar placa con "
     "planos; revisar el registrador de impacto antes de descargar; verificar etiquetado de contenido "
     "PCB; anclaje, alineacion y tierra; boquillas limpias; ajustes de alarma, control y disparo en "
     "indicadores de temperatura y nivel; operacion de los circuitos de alarma/control/disparo del relé "
     "de presion subita (Buchholz) y relé de presion de falla; ventiladores y bombas con proteccion de "
     "sobrecorriente; nivel correcto de liquido en tanque y boquillas; presion positiva en unidades con "
     "manto de gas; probar el cambiador de tomas y verificar pararrayos."),
    ("Transformador", "transformador liquido pruebas aceite dga rigidez dielectrica boquillas excitacion",
     "Transformador en liquido. Pruebas electricas: resistencia de aislamiento con indice de polarizacion; "
     "TTR en todas las tomas; factor de potencia/disipacion de devanados y de cada boquilla (o prueba de "
     "collar caliente); corriente de excitacion; resistencia de cada devanado por posicion del cambiador; "
     "resistencia de aislamiento del nucleo a 500 V cc. Muestra de liquido aislante (ASTM D923) probada "
     "por: rigidez dielectrica (ASTM D877/D1816), numero de neutralizacion acida, tension interfacial, "
     "color y condicion visual; analisis de gases disueltos (DGA) segun ANSI/IEEE C57.104."),
    ("Transformador", "transformador liquido criterios aceptacion dga boquillas nivel presion",
     "Transformador en liquido, criterios: indice de polarizacion >= 1.0; TTR dentro de +/-0.5%; factor de "
     "potencia de devanados segun fabricante (o Tabla 100.3); investigar FP y capacitancia de boquillas que "
     "varien mas de 10% del dato de placa; niveles de liquido dentro de tolerancia y presion positiva en "
     "unidades con manto de gas; resultados del liquido aislante segun Tabla 100.4; evaluar el DGA segun "
     "ANSI/IEEE C57.104."),

    # ===================== MOTOR =====================
    ("Motor", "maquina rotativa motor inspeccion visual escobillas ventiladores rtd alineacion entrehierro",
     "Maquinas rotativas (motores y generadores). Inspeccion visual y mecanica: comparar placa con planos; "
     "condicion fisica y mecanica; anclaje, alineacion y puesta a tierra; inspeccionar deflectores de aire, "
     "medios filtrantes, ventiladores de enfriamiento, anillos rozantes, escobillas y portaescobillas; "
     "conexiones atornilladas (ohmimetro de baja resistencia, torque calibrado o termografia); pruebas "
     "especiales como entrehierro (air-gap) y alineacion de la maquina; verificar lubricacion y sistemas de "
     "lubricacion; verificar que los circuitos de los detectores de temperatura (RTD) concuerden con planos."),
    ("Motor", "motor induccion ac pruebas resistencia aislamiento indice polarizacion vibracion rodamientos",
     "Motores de induccion de corriente alterna (AC). Pruebas electricas: resistencia de conexiones con "
     "ohmimetro de baja resistencia; resistencia de aislamiento segun ANSI/IEEE 43 (maquinas >200 HP / "
     "150 kW: 10 minutos y calcular indice de polarizacion; <=200 HP: 1 minuto y calcular relacion de "
     "absorcion dielectrica); prueba de tension soportada en cc para maquinas >=2300 V (ANSI/IEEE 95); "
     "resistencia de estator fase-a-fase en maquinas >=2300 V; factor de potencia y tip-up; surge "
     "comparison; resistencia de aislamiento de rodamientos aislados; prueba de los circuitos RTD; verificar "
     "calentadores de espacio; prueba de vibracion."),
    ("Motor", "motor criterios aislamiento minimo megohm 40 grados vibracion tabla estator",
     "Motores, criterios de aceptacion electricos: el indice de polarizacion o la relacion de absorcion "
     "dielectrica no debe ser menor a 1.0. La resistencia de aislamiento minima (IR 1 min, corregida a 40 C) "
     "se lee asi: IR 1min = kV + 1 para devanados anteriores a 1970 y todos los devanados de campo; "
     "IR 1min = 100 megohms para armaduras de cc y devanados ac posteriores a 1970 (bobinas formadas); "
     "IR 1min = 5 megohms para maquinas con bobinas random-wound y devanados <1 kV. Investigar resistencias "
     "de estator fase-fase que se desvien mas de 5%; la vibracion de la maquina desacoplada y sin carga no "
     "debe exceder la Tabla 100.10 (si la excede, hacer analisis de vibracion completo)."),
    ("Motor", "motor corriente continua dc conmutador escobillas alto potencial polos campo",
     "Motores de corriente continua (DC). Inspeccion: deflectores de aire, ventiladores, escobillas y "
     "portaescobillas, conmutador y tacogenerador; entrehierro y alineacion. Pruebas: resistencia de "
     "aislamiento de todos los devanados (ANSI/IEEE 43); prueba de alto potencial (NEMA MG 1, 3.1); caida "
     "de tension en CA sobre todos los polos de campo; medir corriente de armadura en marcha y corriente o "
     "tension de campo y comparar con placa; vibracion. Criterios: variacion de caida de tension polo-a-polo "
     "<=5%; corrientes comparables a placa."),
    ("Motor", "control de motores arrancador baja tension contactores sobrecarga guardamotor fusibles",
     "Control de motores - arrancadores de baja tension. Inspeccion: placa, condicion, anclaje, limpieza; "
     "inspeccionar contactores (operacion mecanica; gap, desgaste, alineacion y presion de contactos segun "
     "fabricante); proteccion de marcha del motor: verificar que el rango del elemento de sobrecarga "
     "(relé térmico/guardamotor) sea correcto para la aplicacion, o el rango del fusible si protege la "
     "marcha; conexiones atornilladas; lubricacion. Pruebas: resistencia de aislamiento por polo "
     "(fase-fase y fase-tierra con el arrancador cerrado y a traves de cada polo abierto, 1 minuto); probar "
     "dispositivos de proteccion del motor; probar interruptores (Seccion 7.6); pruebas operacionales."),
    ("Motor", "control de motores media tension enclavamientos botella vacio contactos coordinacion",
     "Control de motores - arrancadores de media tension. Inspeccion: enclavamientos electricos y mecanicos; "
     "barreras y persianas; ejercitar componentes y verificar indicadores; contactores (operacion mecanica y "
     "contactos); verificar que el rango de la proteccion de sobrecarga sea correcto y ajustar dispositivos "
     "segun el estudio de coordinacion de protecciones. Pruebas: aislamiento de contactores; prueba de "
     "integridad de la botella de vacio (dielectric withstand) con contactos abiertos; resistencia de "
     "contactos; resistencia de fusibles de potencia; probar transformador de control y de arranque; probar "
     "dispositivos de proteccion del motor."),
    ("Motor", "control de motores criterios aislamiento cableado control dos megohm coordinacion",
     "Control de motores, criterios de aceptacion: la resistencia de aislamiento debe cumplir el dato del "
     "fabricante (o Tabla 100.5); la resistencia de aislamiento del cableado de control no debe ser menor a "
     "2 megohms; los parametros de proteccion del motor deben ajustarse segun el fabricante y el estudio de "
     "coordinacion; investigar conexiones que se desvien mas de 50% del valor mas bajo. Un centro de control "
     "de motores (CCM/MCC) se prueba por partes: barras (Sec. 7.1), interruptores y arrancadores."),

    # ===================== GENERADOR ELECTRICO =====================
    ("Generador eléctrico", "generador sincrono campo excitatriz curva v rele factor potencia alto potencial",
     "Generadores (y motores) sincronos. Ademas de las pruebas de maquina rotativa: resistencia de "
     "aislamiento del devanado de campo principal, del devanado de campo de la excitatriz y de la armadura "
     "de la excitatriz (ANSI/IEEE 43); prueba de caida de tension en CA en todos los polos de campo; prueba "
     "de alto potencial al sistema de excitacion (ANSI/IEEE 421.3); resistencia de los devanados de campo y "
     "de la excitatriz; prueba de diodos y SCR de los semiconductores de campo; ajustar la corriente de "
     "campo de la excitatriz al valor de placa; verificar los temporizadores del relé de factor de potencia; "
     "trazar la curva V (corriente de estator vs. corriente de excitacion); verificar la operacion del relé "
     "de factor de potencia al reducir la excitacion."),
    ("Generador eléctrico", "generador sincrono criterios caida polo polo aislamiento rele factor potencia",
     "Generadores sincronos, criterios: la variacion de la caida de tension en CA entre polos no debe "
     "exceder 10%; el indice de polarizacion/relacion de absorcion >= 1.0 con IR 1min minima (kV+1, "
     "100 megohms o 5 megohms segun el tipo de devanado, corregida a 40 C); cuando la excitacion reducida "
     "cae por debajo del valor de disparo, el relé de factor de potencia debe operar; resistencias de "
     "devanados de campo comparadas con el dato del fabricante."),
    ("Generador eléctrico", "generador emergencia motor generador planta nfpa 110 sincronizacion paro sobrevelocidad",
     "Generador de emergencia (grupo motor-generador / planta de emergencia). Inspeccion: placa, condicion, "
     "anclaje, alineacion, tierra y limpieza. Pruebas electricas y mecanicas: resistencia de aislamiento "
     "(ANSI/IEEE 43); probar relés de proteccion (Seccion 7.9); verificar rotacion de fases, fasor y "
     "operacion sincronizada; prueba funcional del paro del motor por baja presion de aceite, "
     "sobretemperatura, sobrevelocidad y otras protecciones; vibracion en cada tapa de rodamiento; prueba de "
     "desempeño segun ANSI/NFPA 110; verificar el funcionamiento del gobernador y del regulador."),
    ("Generador eléctrico", "generador emergencia criterios protecciones nfpa 110 indice polarizacion",
     "Generador de emergencia, criterios: el indice de polarizacion >= 1.0 (IR 1min corregida a 40 C: kV+1, "
     "100 megohms o 5 megohms segun el devanado); las protecciones de baja presion de aceite, "
     "sobretemperatura y sobrevelocidad deben operar segun fabricante; rotacion de fases y sincronizacion "
     "conformes al diseño; el desempeño debe cumplir ANSI/NFPA 110; gobernador y regulador segun fabricante."),

    # ===================== GENERAL (aplica a todos) =====================
    ("", "conexiones atornilladas alta resistencia torque termografia ohmimetro general",
     "Conexiones electricas atornilladas (aplica a todo equipo). Para detectar alta resistencia usar uno o "
     "mas metodos: ohmimetro de baja resistencia; verificacion del torque con llave calibrada segun el "
     "fabricante o la Tabla 100.12; o termografia (Seccion 9). Criterio: investigar las conexiones cuya "
     "resistencia se desvie mas de 50% respecto al valor mas bajo de conexiones similares."),
    ("", "puesta a tierra sistema tierra caida potencial nfpa 70 nec 250 electrodo",
     "Sistemas de puesta a tierra. Inspeccion: verificar que el sistema cumpla planos y NFPA 70 (Codigo "
     "Electrico Nacional, Articulo 250); condicion fisica; conexiones libres de corrosion. Pruebas "
     "electricas: medir resistencia de conexiones; prueba de caida de potencial (fall-of-potential, "
     "ANSI/IEEE 81) en el electrodo o sistema de tierra principal; pruebas punto a punto para medir la "
     "resistencia entre el sistema de tierra principal y los marcos de los equipos, el neutro del sistema y "
     "los puntos de neutro derivados."),
    ("", "puesta a tierra criterios resistencia cinco ohms punto a punto ieee 142",
     "Puesta a tierra, criterios de aceptacion: la resistencia entre el electrodo de tierra principal y "
     "tierra no debe ser mayor a 5 ohms en sistemas comerciales o industriales grandes, y de 1.0 ohm o menos "
     "en tierras de estaciones de generacion o transmision, salvo otra especificacion del propietario "
     "(ANSI/IEEE 142); investigar valores de resistencia punto a punto que excedan 0.5 ohm."),
    ("", "cables media alta tension pantalla terminaciones radio curvatura aislamiento continuidad",
     "Cables de media y alta tension. Inspeccion: comparar datos con planos; daños fisicos en secciones "
     "expuestas; conexiones atornilladas; conectores de compresion (ajuste e indentacion correctos); puesta "
     "a tierra de pantalla, soportes y terminaciones; radio de curvatura igual o mayor al minimo (ICEA y "
     "fabricante); proteccion contra fuego; identificacion; condicion de chaqueta y aislamiento. Pruebas: "
     "resistencia de aislamiento de cada conductor con los demas conductores y pantallas aterrizados; prueba "
     "de continuidad de pantalla; pruebas de tension soportada (cc, VLF o frecuencia industrial) y "
     "diagnostico de linea base (factor de potencia/tan delta, descargas parciales)."),
    ("", "cables criterios aislamiento continuidad pantalla diez ohms tension soportada",
     "Cables de media y alta tension, criterios: resistencia de aislamiento segun fabricante (o Tabla 100.1); "
     "la pantalla debe presentar continuidad (investigar valores que excedan 10 ohms por cada 1000 pies de "
     "cable); en la prueba de tension soportada, si no hay evidencia de falla del aislamiento al terminar el "
     "tiempo total de aplicacion, el cable se considera aprobado; valores aceptables segun la norma o "
     "literatura del fabricante segun el metodo elegido."),
    ("", "interruptor termomagnetico caja moldeada pickup inyeccion primaria coordinacion disparo",
     "Interruptores de aire de caja moldeada / caja aislada (termomagneticos). Inspeccion: comparar placa; "
     "condicion fisica; anclaje y alineacion; limpieza; operar el interruptor para asegurar operacion suave; "
     "conexiones atornilladas; inspeccionar mecanismo de operacion, contactos y camaras de arco; ajustar las "
     "protecciones segun el estudio de coordinacion. Pruebas: resistencia de aislamiento por polo (fase-fase "
     "y fase-tierra con el interruptor cerrado, y a traves de cada polo abierto); resistencia de contacto/"
     "polo; determinar pickup y retardo de tiempo largo, tiempo corto, falla a tierra e instantaneo por "
     "inyeccion primaria de corriente; minima tension de pickup de las bobinas de disparo y cierre."),
    ("", "interruptor criterios banda tiempo corriente pickup tabla aislamiento control",
     "Interruptores, criterios de aceptacion: resistencia de aislamiento segun fabricante (o Tabla 100.1); "
     "caida en microohm o milivolts cc dentro del rango normal del fabricante; los valores de pickup de "
     "tiempo largo, tiempo corto, falla a tierra e instantaneo deben estar dentro de la banda de tolerancia "
     "tiempo-corriente del fabricante (o Tablas 100.7 y 100.8); el cableado de control no debe ser menor a "
     "2 megohms; las funciones de apertura, cierre, disparo, trip-free y anti-pump deben operar como se "
     "diseñaron."),
]


def main():
    existentes = rag.fuentes()
    if FUENTE in existentes:
        print(f"La fuente ya esta cargada ({existentes[FUENTE]} fragmentos). No se hace nada.")
        print("Para recargar, elimina antes esos fragmentos de data/rag.json.")
        return
    antes = rag.contar()
    for tipo, tema, texto in FRAGMENTOS:
        rag.agregar(texto, fuente=FUENTE, tipo_equipo=tipo, tema=tema)
    despues = rag.contar()
    print(f"Cargados {despues - antes} fragmentos del estandar ANSI/NETA ATS-2009.")
    print(f"Total de fragmentos en el RAG: {despues}")
    print("\nResumen por fuente:")
    for f, n in rag.fuentes().items():
        print(f"  {f}: {n}")


if __name__ == "__main__":
    main()
