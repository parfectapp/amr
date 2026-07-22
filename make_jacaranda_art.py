#!/usr/bin/env python3
"""Arte de JACARANDA — la lluvia de pétalos, generada, no dibujada a mano.

POR QUÉ ESTA IMAGEN
  El jacarandá no interesa como árbol: interesa como EVENTO. Pone violeta una
  ciudad entera durante tres semanas y se acaba. Y lo que la gente recuerda no
  es el árbol — es la calle cubierta, los pétalos cayendo encima de los coches,
  pisar violeta.

  Por eso la portada no dibuja un árbol. Dibuja **lo que cae**: miles de pétalos
  en el aire, densos arriba donde está la copa y amontonándose abajo hasta
  volverse alfombra.

CÓMO ESTÁ HECHA
  Un pétalo que cae NO baja derecho. Es ancho y ligero, así que el aire lo hace
  voltearse y planear de lado — el movimiento se llama *tumbling* y es por eso
  que un pétalo tarda tanto en llegar al suelo comparado con una piedra. Aquí
  eso se aproxima con dos cosas:
    · un campo de flujo suave con deriva hacia abajo (el viento y la gravedad)
    · un ángulo PROPIO por pétalo, sin relación con su vecino, porque cada uno
      va girando por su cuenta
  Eso último es lo que distingue esta imagen de la bandada que tenía antes el
  disco: los pájaros se ALINEAN con sus vecinos, los pétalos NO. Misma máquina,
  regla opuesta, y se lee distinto de inmediato.
"""
import os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W = 1000

# La paleta del jacarandá: violeta profundo con un lila que brilla. Son los
# mismos tonos que ya usaba el disco viejo — cambia la música, no el color.
VIOLETA = '#463A73'
LILA = '#9D8BD6'
HUESO = '#EAE6DF'


def campo(x, y):
    """Deriva del aire en (x,y): baja siempre, con corrientes laterales suaves."""
    u = (math.sin(y * 0.0062 + 0.7) * 0.85 + math.cos(x * 0.0041 + 2.2) * 0.42
         + math.sin(y * 0.0135) * 0.28)
    v = 1.55 + math.sin(x * 0.0057 + 1.1) * 0.22      # ← siempre hacia abajo
    n = math.hypot(u, v) or 1.0
    return u / n, v / n


def petalos(n=2600, seed=41):
    """Suelta pétalos y los deja caer por el campo.

    Devuelve (x, y, ángulo propio, peso). El ángulo NO sale del campo: cada
    pétalo gira por su cuenta mientras planea. Esa es la diferencia entre esto
    y una bandada."""
    rng = np.random.default_rng(seed)
    out = []
    intentos = 0
    while len(out) < n and intentos < n * 40:
        intentos += 1
        x = float(rng.uniform(-W * 0.05, W * 1.05))
        y = float(rng.uniform(-W * 0.05, W * 0.98))
        # densidad: mucha arriba (la copa), se abre al caer, se junta abajo
        t = max(0.0, min(1.0, y / W))
        copa = math.exp(-((t - 0.10) / 0.30) ** 2)         # la copa, arriba
        suelo = math.exp(-((t - 0.955) / 0.055) ** 2) * 1.15  # la alfombra, abajo
        aire = 0.30 * math.exp(-((t - 0.5) / 0.40) ** 2)   # los que van cayendo
        d = min(1.0, copa + suelo + aire)
        if rng.random() > d:
            continue
        for _ in range(int(rng.integers(2, 9))):
            u, v = campo(x, y)
            x += u * 8.0
            y += v * 8.0
        if not (-W * 0.06 < x < W * 1.06 and -W * 0.06 < y < W * 1.02):
            continue
        out.append((x, y, float(rng.uniform(0, 180)), d))
    return out


def svg():
    ps = petalos()
    p = [f'<svg viewBox="0 0 {W} {W}" xmlns="http://www.w3.org/2000/svg">',
         # ⚠️ El recorte no es opcional. Los pétalos se siembran FUERA del marco
         # a propósito, para que no se vea la orilla de donde salen — pero sin
         # clip se pintan encima del marco y se desbordan de la portada.
         f'<defs><clipPath id="jcmarco"><rect width="{W}" height="{W}"/></clipPath>',
         '<linearGradient id="jcaire" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="{LILA}" stop-opacity="0.20"/>'
         f'<stop offset="55%" stop-color="{LILA}" stop-opacity="0.05"/>'
         f'<stop offset="100%" stop-color="{VIOLETA}" stop-opacity="0.14"/>'
         '</linearGradient></defs>',
         f'<rect width="{W}" height="{W}" fill="{HUESO}"/>',
         f'<rect width="{W}" height="{W}" fill="url(#jcaire)"/>',
         '<g clip-path="url(#jcmarco)">']

    rng = np.random.default_rng(7)
    cuerpo = []
    for x, y, a, d in ps:
        # el pétalo del jacarandá es una campanita: más ancho que largo
        L = (3.2 + 5.0 * d) * (0.55 + 1.0 * float(rng.random()))
        # los de abajo van más oscuros: llevan días ahí y ya se pisaron
        prof = min(1.0, y / W)
        col = VIOLETA if (prof > 0.72 or rng.random() < 0.34) else LILA
        cuerpo.append(
            f'<g transform="translate({x:.1f},{y:.1f}) rotate({a:.0f})">'
            f'<ellipse rx="{L:.1f}" ry="{L*0.62:.2f}" fill="{col}" '
            f'opacity="{0.28+0.60*d:.2f}"/></g>')
    p.append(''.join(cuerpo))
    p.append('</g>')

    # la línea de la banqueta: donde la alfombra se acaba
    p.append(f'<line x1="{W*0.06:.0f}" y1="{W*0.875:.0f}" x2="{W*0.94:.0f}" '
             f'y2="{W*0.875:.0f}" stroke="{VIOLETA}" stroke-width="1.8" opacity="0.4"/>')
    # marcas de las 7 rolas, la 3ª (FULGOR) encendida: es el pico del disco.
    # Era la 5ª (EPIFANÍA) hasta que esa se sacó del set — al cambiar el número
    # de rolas hay que mover ESTA marca Y la regla nth-child del index.html,
    # si no se enciende el renglón equivocado.
    for i in range(7):
        cx = W * 0.10 + (W * 0.80) * (i + 0.5) / 7.0
        col = LILA if i == 2 else VIOLETA
        op = '1' if i == 2 else '0.5'
        p.append(f'<line x1="{cx:.1f}" y1="{W*0.875:.0f}" x2="{cx:.1f}" '
                 f'y2="{W*0.899:.0f}" stroke="{col}" stroke-width="2.4" opacity="{op}"/>')
    p.append('</svg>')
    return ''.join(p)


def svg_fulgor(w=240):
    """FULGOR — el jacarandá en plena floración, el árbol entero prendido.

    Es el pico del disco. La primera versión era una copa a contraluz de
    degradado (estilo atmosférico); André pidió emparejarla al estilo de la
    casa, como subsuelo y letanía. Ahora es un ICONO: un árbol bold con el
    tronco negro y la copa hecha una nube de flor violeta, con el sol detrás.
    El árbol que pone violeta la ciudad, en un solo objeto."""
    import math as _m
    TRONCO = '#2E2650'
    cx = 120
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         f'<defs><radialGradient id="jfg" cx="50%" cy="42%" r="52%">'
         f'<stop offset="0%" stop-color="#FFF3D6" stop-opacity="0.9"/>'
         f'<stop offset="42%" stop-color="{LILA}" stop-opacity="0.5"/>'
         f'<stop offset="100%" stop-color="{LILA}" stop-opacity="0"/>'
         f'</radialGradient></defs>',
         f'<ellipse cx="{cx}" cy="214" rx="60" ry="8" fill="{TRONCO}" opacity="0.06"/>',
         f'<circle cx="{cx}" cy="96" r="78" fill="url(#jfg)"/>']
    # tronco: sube del suelo y se abre en tres ramas
    p.append(f'<path d="M{cx-8},206 L{cx-8},120 L{cx+8},120 L{cx+8},206 Z" fill="{TRONCO}"/>')
    for ang, largo in [(-0.6, 46), (0.0, 40), (0.62, 46)]:
        x2 = cx + _m.sin(ang) * largo
        y2 = 120 - _m.cos(ang) * largo
        p.append(f'<line x1="{cx}" y1="126" x2="{x2:.0f}" y2="{y2:.0f}" '
                 f'stroke="{TRONCO}" stroke-width="9" stroke-linecap="round"/>')
    # copa: nube de flor, círculos violetas encimados (bold, no degradado)
    rng = __import__('numpy').random.default_rng(41)
    pom = [(cx, 78, 40), (cx-40, 96, 30), (cx+40, 96, 30),
           (cx-22, 62, 26), (cx+24, 60, 27), (cx, 108, 30),
           (cx-52, 74, 20), (cx+52, 74, 20)]
    for x, y, r in pom:
        p.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{VIOLETA}"/>')
    # manchones claros de flor (lila) para que la copa respire
    for _ in range(16):
        x = cx + float(rng.uniform(-56, 56)); y = 78 + float(rng.uniform(-30, 34))
        if _m.hypot((x-cx)/58, (y-84)/44) > 1: continue
        p.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{float(rng.uniform(4,9)):.0f}" '
                 f'fill="{LILA}" opacity="0.8"/>')
    # pétalos cayendo: tres puntitos bajo la copa (la lluvia que empieza)
    for x, y in [(cx-30, 150), (cx+18, 162), (cx+40, 140)]:
        p.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{VIOLETA}" opacity="0.7"/>')
    # suelo + dos puntitos de acento
    p.append(f'<rect x="{cx-52}" y="204" width="104" height="6" rx="3" fill="{VIOLETA}"/>')
    p.append(f'<circle cx="60" cy="150" r="2.2" fill="{TRONCO}"/>')
    p.append(f'<circle cx="182" cy="176" r="2.4" fill="{TRONCO}"/>')
    p.append('</svg>')
    return ''.join(p)


def svg_letania(w=240):
    """LETANÍA — el jacarandá florece en RACIMOS colgantes (panículas): decenas
    de campanitas idénticas colgando de un mismo tallo. Una letanía es la misma
    frase repetida hasta volverse una; el racimo es lo mismo hecho flor.

    ⚠️ La primera versión era una rejilla de florecitas que de lejos se leía como
    PAPEL TAPIZ, no como un dibujo. André pidió cambiarla "por algo del estilo".
    El estilo de la casa (guer-cactus, tulum-atlas) es UN objeto icónico en
    trazo grueso sobre hueso — así que ahora es un solo racimo, claro y bold."""
    TALLO = '#2E2650'          # violeta casi negro, el "trazo grueso" del estilo
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         f'<defs><radialGradient id="jlt" cx="50%" cy="48%" r="52%">'
         f'<stop offset="0%" stop-color="{LILA}" stop-opacity="0.42"/>'
         f'<stop offset="55%" stop-color="{LILA}" stop-opacity="0.13"/>'
         f'<stop offset="100%" stop-color="{LILA}" stop-opacity="0"/>'
         f'</radialGradient></defs>',
         f'<circle cx="120" cy="120" r="66" fill="url(#jlt)"/>']

    # una campanita del jacarandá: trompeta bold que cuelga (apunta abajo)
    def campana(cx, cy, col):
        d = (f'M{cx-5},{cy} C{cx-7},{cy+9} {cx-12},{cy+17} {cx-10},{cy+24} '
             f'L{cx+10},{cy+24} C{cx+12},{cy+17} {cx+7},{cy+9} {cx+5},{cy} Z')
        return (f'<path d="{d}" fill="{col}"/>'
                f'<ellipse cx="{cx}" cy="{cy+24}" rx="10" ry="3" fill="{LILA}" opacity="0.9"/>')

    # el racimo: triángulo colgante que se angosta hacia abajo (una panícula).
    # Todas las campanas IDÉNTICAS = la repetición de la letanía.
    filas = [(72, [-45,-22.5,0,22.5,45]), (100, [-33,-11,11,33]),
             (128, [-22,0,22]), (156, [-11,11]), (184, [0])]
    # rama de la que cuelga todo + tallo central
    p.append(f'<line x1="96" y1="52" x2="144" y2="52" stroke="{TALLO}" '
             f'stroke-width="7" stroke-linecap="round"/>')
    p.append(f'<line x1="120" y1="50" x2="120" y2="186" stroke="{TALLO}" stroke-width="4"/>')
    # tallitos a cada campana + las campanas
    bells = []
    for fy, xs in filas:
        for dx in xs:
            cx = 120 + dx
            p.append(f'<line x1="120" y1="{fy-14}" x2="{cx}" y2="{fy-4}" '
                     f'stroke="{TALLO}" stroke-width="2.4"/>')
            bells.append((cx, fy))
    # las campanas al final, encima de los tallos; una de cada tres en lila
    for i, (cx, fy) in enumerate(bells):
        p.append(campana(cx, fy, LILA if i % 3 == 1 else VIOLETA))
    # dos puntitos de acento, como el resto del catálogo
    p.append(f'<circle cx="66" cy="150" r="2.2" fill="{TALLO}"/>')
    p.append(f'<circle cx="180" cy="96" r="2.4" fill="{TALLO}"/>')
    p.append('</svg>')
    return ''.join(p)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    for nombre, gen in [('jacaranda', svg),
                        ('jacaranda-fulgor', svg_fulgor),
                        ('jacaranda-letania', svg_letania)]:
        dst = os.path.join(HERE, 'art', f'{nombre}.svg')
        s = gen()
        with open(dst, 'w') as f:
            f.write(s)
        print(f'{nombre:22s} {len(s)//1024:4d} KB')
