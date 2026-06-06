"""
tools/generar_assets.py · Recursos visuales de Zeus, dibujados POR CÓDIGO.

Genera en assets/:
    logo.png                  emblema de la empresa (engranaje + rayo) para el membrete
    equipo_motor.png          ilustración técnica de un motor eléctrico
    equipo_generador.png      ilustración técnica de un grupo electrógeno
    equipo_transformador.png  ilustración técnica de un transformador

Se dibujan con Pillow a 4x (supersampling) y se reducen con LANCZOS para que los
bordes queden suaves. No usa archivos de terceros ni descargas: es 100%
reproducible con un comando, y la paleta es la misma de reporte.py.

Uso:
    .venv\\Scripts\\python tools\\generar_assets.py
"""

import math
import os

from PIL import Image, ImageDraw

# --- Paleta corporativa (igual que reporte.EMPRESA / barras azules) ----------
AZUL   = (31, 58, 95)      # #1f3a5f  azul principal (contornos, fondo del emblema)
AZUL2  = (51, 71, 91)      # #33475b  azul secundario
AZUL3  = (45, 109, 164)    # acento azul medio (relleno de los equipos)
AZUL4  = (74, 144, 201)    # azul claro (brillos)
GRIS   = (200, 214, 229)   # #c8d6e5  gris azulado claro
GRISL  = (232, 238, 244)   # gris muy claro
ORO    = (240, 184, 40)    # rayo / energía
BLANCO = (255, 255, 255)

SS = 4               # supersampling (se dibuja a SIZE*SS y se reduce)
SIZE = 600           # lado final en px


# ----------------------------------------------------------------------------
# Utilidades de dibujo (todo en coordenadas del lienzo grande S = SIZE*SS)
# ----------------------------------------------------------------------------
def _nuevo():
    """Lienzo cuadrado transparente a escala de supersampling."""
    S = SIZE * SS
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img), S


def _guardar(img, nombre, carpeta, autocrop=False, margen=0.05):
    final = img.resize((SIZE, SIZE), Image.LANCZOS)
    if autocrop:
        # Recorta a la caja del contenido (alfa) + un margen, para que el equipo
        # quede apaisado y llene mejor el espacio junto a la tabla de la OT.
        caja = final.getbbox()
        if caja:
            m = int(SIZE * margen)
            l, t, r, b = caja
            final = final.crop((max(0, l - m), max(0, t - m),
                                min(SIZE, r + m), min(SIZE, b + m)))
    ruta = os.path.join(carpeta, nombre)
    final.save(ruta)
    print("  generado:", os.path.relpath(ruta), f"({final.width}x{final.height})")
    return ruta


def _rrect(draw, caja, radio, fill=None, outline=None, width=1):
    draw.rounded_rectangle(caja, radius=radio, fill=fill, outline=outline, width=width)


def _engranaje(draw, cx, cy, r_ext, r_base, r_hueco, n, color, fondo):
    """Corona dentada (anillo) centrada en (cx,cy). Perfora el centro con `fondo`."""
    disco = []
    paso = 2 * math.pi / n
    tp = paso * 0.30     # semiángulo de la punta del diente
    tb = paso * 0.46     # semiángulo de la base del diente
    pts = []
    for i in range(n):
        a = i * paso - math.pi / 2
        for (r, t) in ((r_base, -tb), (r_ext, -tp), (r_ext, tp), (r_base, tb)):
            pts.append((cx + r * math.cos(a + t), cy + r * math.sin(a + t)))
    # disco base + dientes en una sola pasada
    draw.ellipse([cx - r_base, cy - r_base, cx + r_base, cy + r_base], fill=color)
    draw.polygon(pts, fill=color)
    # hueco central
    draw.ellipse([cx - r_hueco, cy - r_hueco, cx + r_hueco, cy + r_hueco], fill=fondo)


def _rayo(draw, cx, cy, h, color, outline=None, ow=0):
    """Rayo (bolt) centrado en (cx,cy) con altura total `h`."""
    u = h / 2.0
    pts = [
        (cx - 0.34 * u, cy - 1.00 * u),
        (cx + 0.46 * u, cy - 1.00 * u),
        (cx + 0.04 * u, cy - 0.16 * u),
        (cx + 0.40 * u, cy - 0.16 * u),
        (cx - 0.40 * u, cy + 1.00 * u),
        (cx - 0.10 * u, cy + 0.10 * u),
        (cx - 0.48 * u, cy + 0.10 * u),
    ]
    if outline:
        draw.polygon(pts, fill=color, outline=outline, width=ow)
    else:
        draw.polygon(pts, fill=color)


def _onda_seno(draw, x0, x1, y, amp, color, w):
    """Onda senoidal (símbolo AC) entre x0 y x1, centrada en y."""
    pts = []
    n = 60
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        ang = (x - x0) / (x1 - x0) * 2 * math.pi
        pts.append((x, y - amp * math.sin(ang)))
    draw.line(pts, fill=color, width=w, joint="curve")


# ----------------------------------------------------------------------------
# LOGO / emblema de la empresa
# ----------------------------------------------------------------------------
def logo(carpeta):
    img, d, S = _nuevo()
    cx = cy = S / 2
    R = S * 0.46
    # anillo exterior + disco azul del emblema
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=AZUL)
    d.ellipse([cx - R, cy - R, cx + R, cy + R], outline=AZUL4, width=int(S * 0.012))
    Ri = S * 0.40
    d.ellipse([cx - Ri, cy - Ri, cx + Ri, cy + Ri], outline=GRIS, width=int(S * 0.006))
    # engranaje claro (anillo dentado), perforado con el azul del emblema
    _engranaje(d, cx, cy, r_ext=S * 0.34, r_base=S * 0.265, r_hueco=S * 0.205,
               n=12, color=GRIS, fondo=AZUL)
    # rayo dorado al centro
    _rayo(d, cx, cy, h=S * 0.40, color=ORO, outline=AZUL, ow=int(S * 0.006))
    return _guardar(img, "logo.png", carpeta)


# ----------------------------------------------------------------------------
# MOTOR eléctrico (vista lateral)
# ----------------------------------------------------------------------------
def motor(carpeta):
    img, d, S = _nuevo()
    g = int(S * 0.010)                 # grosor de contorno base
    def u(f): return f * S
    # base / patas
    _rrect(d, [u(.20), u(.66), u(.34), u(.72)], u(.012), fill=AZUL2)
    _rrect(d, [u(.52), u(.66), u(.66), u(.72)], u(.012), fill=AZUL2)
    _rrect(d, [u(.16), u(.70), u(.74), u(.745)], u(.01), fill=AZUL)
    # tapa trasera (ventilador) izquierda
    _rrect(d, [u(.13), u(.40), u(.20), u(.66)], u(.015), fill=AZUL2, outline=AZUL, width=g)
    for k in range(4):                 # rejillas del ventilador
        yy = u(.43 + k * .055)
        d.line([u(.145), yy, u(.185), yy], fill=GRIS, width=int(S * 0.006))
    # cuerpo / carcasa
    _rrect(d, [u(.18), u(.38), u(.66), u(.68)], u(.03), fill=AZUL3, outline=AZUL, width=g)
    for k in range(5):                 # aletas longitudinales de refrigeración
        yy = u(.405 + k * .052)
        d.line([u(.21), yy, u(.63), yy], fill=AZUL4, width=int(S * 0.008))
    # brillo superior
    _rrect(d, [u(.20), u(.39), u(.64), u(.405)], u(.006), fill=AZUL4)
    # caja de bornes arriba
    _rrect(d, [u(.34), u(.30), u(.50), u(.385)], u(.012), fill=AZUL2, outline=AZUL, width=g)
    # tapa frontal (lado acople) derecha
    _rrect(d, [u(.63), u(.35), u(.71), u(.70)], u(.02), fill=AZUL2, outline=AZUL, width=g)
    # eje
    _rrect(d, [u(.71), u(.49), u(.83), u(.55)], u(.01), fill=GRIS, outline=AZUL2, width=int(S*0.006))
    return _guardar(img, "equipo_motor.png", carpeta, autocrop=True)


# ----------------------------------------------------------------------------
# GENERADOR (grupo electrógeno: motor + alternador con símbolo AC)
# ----------------------------------------------------------------------------
def generador(carpeta):
    img, d, S = _nuevo()
    g = int(S * 0.010)
    def u(f): return f * S
    # skid / base
    _rrect(d, [u(.12), u(.70), u(.88), u(.76)], u(.012), fill=AZUL, outline=AZUL, width=g)
    _rrect(d, [u(.17), u(.745), u(.27), u(.79)], u(.006), fill=AZUL2)   # apoyos
    _rrect(d, [u(.73), u(.745), u(.83), u(.79)], u(.006), fill=AZUL2)
    # motor de combustión (izquierda)
    _rrect(d, [u(.15), u(.42), u(.45), u(.70)], u(.025), fill=AZUL3, outline=AZUL, width=g)
    for k in range(3):                 # cilindros
        xx = u(.205 + k * .075)
        _rrect(d, [xx, u(.36), xx + u(.045), u(.42)], u(.008), fill=AZUL2, outline=AZUL, width=int(S*0.006))
    d.line([u(.40), u(.36), u(.40), u(.30)], fill=AZUL2, width=int(S * 0.012))  # escape
    _rrect(d, [u(.375), u(.27), u(.43), u(.31)], u(.01), fill=AZUL2)
    # acople
    _rrect(d, [u(.45), u(.52), u(.50), u(.60)], u(.006), fill=GRIS)
    # alternador (cilindro, derecha)
    _rrect(d, [u(.50), u(.44), u(.82), u(.70)], u(.04), fill=AZUL3, outline=AZUL, width=g)
    # cara frontal con símbolo AC (círculo claro + onda)
    cfx, cfy, cr = u(.74), u(.57), u(.10)
    d.ellipse([cfx - cr, cfy - cr, cfx + cr, cfy + cr], fill=GRISL, outline=AZUL, width=g)
    _onda_seno(d, cfx - cr * 0.7, cfx + cr * 0.7, cfy, cr * 0.45, AZUL, int(S * 0.012))
    # brillo del cilindro
    d.line([u(.54), u(.47), u(.78), u(.47)], fill=AZUL4, width=int(S * 0.012))
    return _guardar(img, "equipo_generador.png", carpeta, autocrop=True)


# ----------------------------------------------------------------------------
# TRANSFORMADOR (de distribución: tanque + bushings + radiadores)
# ----------------------------------------------------------------------------
def transformador(carpeta):
    img, d, S = _nuevo()
    g = int(S * 0.010)
    def u(f): return f * S
    # radiadores (aletas) a los lados
    for lado in (0, 1):
        x0 = u(.18) if lado == 0 else u(.755)
        for k in range(4):
            xx = x0 + k * u(.018)
            d.line([xx, u(.42), xx, u(.70)], fill=AZUL2, width=int(S * 0.012))
        d.line([x0, u(.42), x0 + u(.054), u(.42)], fill=AZUL2, width=int(S * 0.012))
        d.line([x0, u(.70), x0 + u(.054), u(.70)], fill=AZUL2, width=int(S * 0.012))
    # tanque
    _rrect(d, [u(.24), u(.40), u(.76), u(.74)], u(.03), fill=AZUL3, outline=AZUL, width=g)
    # tapa
    _rrect(d, [u(.26), u(.36), u(.74), u(.42)], u(.018), fill=AZUL2, outline=AZUL, width=g)
    # brillo
    _rrect(d, [u(.27), u(.44), u(.73), u(.46)], u(.006), fill=AZUL4)
    # placa de datos
    _rrect(d, [u(.43), u(.54), u(.57), u(.66)], u(.01), fill=GRISL, outline=AZUL, width=int(S*0.006))
    for k in range(3):
        d.line([u(.45), u(.575 + k * .03), u(.55), u(.575 + k * .03)], fill=AZUL2, width=int(S*0.006))
    # bushings (3 aisladores arriba)
    for cxf in (.37, .50, .63):
        cxp = u(cxf)
        d.line([cxp, u(.22), cxp, u(.37)], fill=AZUL2, width=int(S * 0.018))   # poste
        for j, ry in enumerate((.235, .275, .315)):                            # discos
            rw = u(.045) - j * u(.004)
            d.ellipse([cxp - rw, u(ry) - u(.012), cxp + rw, u(ry) + u(.012)],
                      fill=GRIS, outline=AZUL2, width=int(S * 0.005))
        d.ellipse([cxp - u(.018), u(.20), cxp + u(.018), u(.232)], fill=ORO, outline=AZUL, width=int(S*0.005))
    return _guardar(img, "equipo_transformador.png", carpeta, autocrop=True)


def main():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    carpeta = os.path.join(raiz, "assets")
    os.makedirs(carpeta, exist_ok=True)
    print("Generando recursos visuales en assets/ ...")
    logo(carpeta)
    motor(carpeta)
    generador(carpeta)
    transformador(carpeta)
    print("Listo.")


if __name__ == "__main__":
    main()
