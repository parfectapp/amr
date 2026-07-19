#!/usr/bin/env python3
"""Portada de OFRENDA — una murmuración, generada, no dibujada a mano.

POR QUÉ ESTA IMAGEN
  El disco son ocho fuerzas naturales sin cara. La murmuración es la única de
  las ocho que sirve de retrato del conjunto: cien mil cuerpos que se mueven
  como uno solo, sin nadie mandando. Ocho ofrendas, un rito.

  Y la paleta ES la narrativa: todo el campo en ceniza, un solo puñado de
  cuerpos en verde aurora. Se le da algo al mundo y algo contesta — pero poquito.

CÓMO ESTÁ HECHA
  No son coordenadas inventadas a mano. Los estorninos reales no siguen a un
  líder: cada uno ajusta su rumbo según sus SIETE vecinos más cercanos, y de esa
  regla local sale la forma global (Ballerini et al., PNAS 2008 — midieron
  bandadas reales con fotografía estéreo y encontraron que la correlación es
  topológica, de siete vecinos, no métrica por distancia).

  Aquí eso se aproxima con un campo de flujo suave: cada cuerpo camina siguiendo
  la dirección local del campo, así que los vecinos terminan alineados sin que
  nadie coordine nada. Cada marca se estira en la dirección en que va — un pájaro
  visto de lado es una raya, no un punto.
"""
import os, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W = 1000

CENIZA = '#3A3A38'
AURORA = '#5FE8B0'
HUESO = '#EAE6DF'


def campo(x, y):
    """Dirección del flujo en (x,y). Suma de senos: suave y sin costuras.

    ⚠️ El término DERIVA no es decorativo. La primera versión era pura suma de
    senos y el campo se cerraba sobre sí mismo en el centro: salía un remolino
    con ojo, que lee como huracán y no como bandada. Una murmuración real no
    gira sobre un punto — VA HACIA ALGÚN LADO, toda junta, y las curvas son
    desviaciones de ese rumbo común. La deriva impone ese rumbo y hace que las
    ondulaciones se lean como lo que son: la bandada doblándose al viajar.
    """
    DERIVA = 1.35                                   # rumbo común, domina el campo
    u = (DERIVA
         + math.sin(y * 0.0075) * 0.85 + math.sin(y * 0.0161 + 1.7) * 0.38
         + math.cos(x * 0.0052 + 0.4) * 0.30)
    v = (math.cos(x * 0.0068 + 2.1) * 0.58 + math.sin(x * 0.0139) * 0.26
         - math.sin(y * 0.0043 + 0.9) * 0.24
         + math.sin(x * 0.0091 + y * 0.0057) * 0.22)   # ondas internas de densidad
    n = math.hypot(u, v) or 1.0
    return u / n, v / n


def densidad(x, y):
    """La bandada es más densa al centro y se deshilacha en los bordes."""
    dx, dy = (x - W * 0.50) / (W * 0.40), (y - W * 0.46) / (W * 0.30)
    r = math.hypot(dx, dy)
    return math.exp(-r * r * 1.15)


def cuerpos(n=2400, seed=11):
    """Suelta semillas y las camina por el campo. Devuelve (x, y, ángulo, peso)."""
    rng = np.random.default_rng(seed)
    out = []
    intentos = 0
    while len(out) < n and intentos < n * 60:
        intentos += 1
        x = float(rng.uniform(W * 0.06, W * 0.94))
        y = float(rng.uniform(W * 0.10, W * 0.86))
        if rng.random() > densidad(x, y):
            continue
        # camina unos pasos para que se alinee con sus vecinos del campo
        for _ in range(int(rng.integers(3, 14))):
            u, v = campo(x, y)
            x += u * 7.0
            y += v * 7.0
        if not (0 < x < W and 0 < y < W):
            continue
        u, v = campo(x, y)
        out.append((x, y, math.degrees(math.atan2(v, u)),
                    float(densidad(x, y))))
    return out


def svg():
    cs = cuerpos()
    # el destello: los que caen dentro de un óvalo chico arriba a la derecha.
    # Es la RESPUESTA — tiene que ser poca, si no deja de ser un destello.
    fx, fy, fr = W * 0.665, W * 0.335, W * 0.105
    p = [f'<svg viewBox="0 0 {W} {W}" xmlns="http://www.w3.org/2000/svg">',
         f'<rect width="{W}" height="{W}" fill="{HUESO}"/>',
         '<defs><radialGradient id="ofglow" cx="50%" cy="50%" r="50%">'
         f'<stop offset="0%" stop-color="{AURORA}" stop-opacity="0.22"/>'
         f'<stop offset="100%" stop-color="{AURORA}" stop-opacity="0"/>'
         '</radialGradient></defs>',
         f'<ellipse cx="{fx:.0f}" cy="{fy:.0f}" rx="{fr*2.5:.0f}" ry="{fr*2.1:.0f}" '
         'fill="url(#ofglow)"/>']

    grises, verdes = [], []
    rng = np.random.default_rng(3)
    for x, y, a, d in cs:
        # marca alargada en la dirección de vuelo: un pájaro de perfil es una raya.
        # El factor al azar es lo que quita el look de "simulación de partículas":
        # en una bandada real unos están más cerca que otros, así que se ven de
        # distinto tamaño aunque todos sean el mismo pájaro.
        L = (3.0 + 5.4 * d) * (0.55 + 1.05 * float(rng.random()))
        gr = 0.26 + 0.66 * d
        # El destello NO tiene borde duro. Con un corte limpio el verde salía
        # como un óvalo pegado encima — leía a blob, no a luz. Cerca del borde
        # se decide al azar, así que la orilla se deshilacha: unos cuantos
        # cuerpos verdes sueltos afuera y unos grises adentro, que es como se
        # ve de verdad una luz cayendo sobre una bandada en movimiento.
        r2 = ((x - fx) / fr) ** 2 + ((y - fy) / (fr * 0.82)) ** 2
        p_verde = 1.0 - (r2 - 0.45) / 0.95           # 1 adentro, 0 pasando el borde
        dentro = float(rng.random()) < p_verde
        s = (f'<g transform="translate({x:.1f},{y:.1f}) rotate({a:.0f})">'
             f'<ellipse rx="{L:.1f}" ry="{max(0.62, L*0.19):.2f}" '
             f'opacity="{gr:.2f}"/></g>')
        (verdes if dentro else grises).append(s)

    p.append(f'<g fill="{CENIZA}">' + ''.join(grises) + '</g>')
    p.append(f'<g fill="{AURORA}">' + ''.join(verdes) + '</g>')

    # el horizonte: una sola línea, para que la bandada tenga suelo
    p.append(f'<line x1="{W*0.10:.0f}" y1="{W*0.845:.0f}" x2="{W*0.90:.0f}" '
             f'y2="{W*0.845:.0f}" stroke="{CENIZA}" stroke-width="1.6" opacity="0.5"/>')
    # marcas de los 8: ocho tramos sobre el horizonte, el 5º en verde (AURORA)
    for i in range(8):
        cx = W * 0.10 + (W * 0.80) * (i + 0.5) / 8.0
        col = AURORA if i == 4 else CENIZA
        op = '1' if i == 4 else '0.55'
        p.append(f'<line x1="{cx:.1f}" y1="{W*0.845:.0f}" x2="{cx:.1f}" '
                 f'y2="{W*0.869:.0f}" stroke="{col}" stroke-width="2.4" opacity="{op}"/>')
    p.append('</svg>')
    return ''.join(p)


def svg_aurora(w=240):
    """Cortina auroral. La forma no es inventada: las auroras se ven como
    cortinas verticales porque las partículas del sol bajan siguiendo las
    líneas del campo magnético, y esas líneas son casi verticales cerca de los
    polos. Por eso son rayos de arriba a abajo y no manchas."""
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         f'<rect width="{w}" height="{w}" fill="{CENIZA}"/>',
         '<defs><linearGradient id="aucur" x1="0" y1="0" x2="0" y2="1">'
         f'<stop offset="0%" stop-color="{AURORA}" stop-opacity="0"/>'
         f'<stop offset="38%" stop-color="{AURORA}" stop-opacity="0.85"/>'
         f'<stop offset="100%" stop-color="{AURORA}" stop-opacity="0.05"/>'
         '</linearGradient></defs>']
    rng = np.random.default_rng(5)
    # cada rayo es una línea vertical con una ondulación suave: la cortina
    for i in range(120):
        x0 = w * 0.10 + (w * 0.80) * i / 119.0
        amp = 9.0 + 7.0 * math.sin(i * 0.21)
        fase = i * 0.17
        pts = []
        for k in range(11):
            t = k / 10.0
            y = w * 0.12 + t * w * 0.62
            x = x0 + amp * math.sin(fase + t * 2.4)
            pts.append(f'{x:.1f},{y:.1f}')
        p.append(f'<polyline points="{" ".join(pts)}" fill="none" '
                 f'stroke="url(#aucur)" stroke-width="{1.1+0.9*rng.random():.2f}"/>')
    # el suelo, para que la cortina cuelgue de algo
    p.append(f'<line x1="{w*0.08:.0f}" y1="{w*0.82:.0f}" x2="{w*0.92:.0f}" '
             f'y2="{w*0.82:.0f}" stroke="{HUESO}" stroke-width="1" opacity="0.35"/>')
    p.append('</svg>')
    return ''.join(p)


def svg_murmuracion(w=240):
    """La bandada sola, apretada, sin destello: aquí el verde no toca."""
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         f'<rect width="{w}" height="{w}" fill="{HUESO}"/>',
         f'<g fill="{CENIZA}">']
    esc = w / float(W)
    for x, y, a, d in cuerpos(n=1500, seed=23):
        L = (2.6 + 4.0 * d) * esc * 2.4
        p.append(f'<g transform="translate({x*esc:.1f},{y*esc:.1f}) rotate({a:.0f})">'
                 f'<ellipse rx="{L:.2f}" ry="{max(0.45, L*0.20):.2f}" '
                 f'opacity="{0.28+0.60*d:.2f}"/></g>')
    p.append('</g>')
    p.append(f'<line x1="{w*0.10:.0f}" y1="{w*0.845:.0f}" x2="{w*0.90:.0f}" '
             f'y2="{w*0.845:.0f}" stroke="{CENIZA}" stroke-width="1.2" opacity="0.45"/>')
    p.append('</svg>')
    return ''.join(p)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    for nombre, gen in [('amr-ofrenda', svg),
                        ('ofrenda-aurora', svg_aurora),
                        ('ofrenda-murmuracion', svg_murmuracion)]:
        dst = os.path.join(HERE, 'art', f'{nombre}.svg')
        s = gen()
        with open(dst, 'w') as f:
            f.write(s)
        print(f'{nombre:22s} {len(s)//1024:4d} KB')
