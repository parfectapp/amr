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
    # marcas de las 7 rolas, el 3º en verde: BIOLUMINISCENCIA.
    # Antes el verde era AURORA, pero esa se sacó del set (sonaba a Avicii). Y
    # el destello queda MEJOR justificado aquí: bioluminiscencia es literalmente
    # el mar prendiéndose en verde cuando lo tocas — le das algo y te contesta,
    # que es la idea entera del disco.
    for i in range(7):
        cx = W * 0.10 + (W * 0.80) * (i + 0.5) / 7.0
        col = AURORA if i == 2 else CENIZA
        op = '1' if i == 2 else '0.55'
        p.append(f'<line x1="{cx:.1f}" y1="{W*0.845:.0f}" x2="{cx:.1f}" '
                 f'y2="{W*0.869:.0f}" stroke="{col}" stroke-width="2.4" opacity="{op}"/>')
    p.append('</svg>')
    return ''.join(p)


def svg_biolum(w=240):
    """BIOLUMINISCENCIA — el mar que se enciende donde lo tocas.

    Reemplaza al dibujo de AURORA, que se fue con la rola. Y el cambio le queda
    mejor al disco: la bioluminiscencia ES la respuesta — el plancton no brilla
    solo, brilla cuando algo lo mueve. Le das algo al mar y te contesta con luz.
    Por eso el verde aquí va en ESTELAS, no en manchas: marca por dónde pasó
    algo. Agua casi negra, y la luz sólo donde hubo movimiento.
    """
    rng = np.random.default_rng(17)
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         '<defs>',
         '<linearGradient id="biagua" x1="0" y1="0" x2="0" y2="1">'
         '<stop offset="0%" stop-color="#05070A"/>'
         '<stop offset="55%" stop-color="#0A1016"/>'
         '<stop offset="100%" stop-color="#04070A"/></linearGradient>',
         '<radialGradient id="biglow" cx="50%" cy="50%" r="50%">'
         f'<stop offset="0%" stop-color="{AURORA}" stop-opacity="0.34"/>'
         f'<stop offset="100%" stop-color="{AURORA}" stop-opacity="0"/>'
         '</radialGradient>',
         '</defs>',
         f'<rect width="{w}" height="{w}" fill="url(#biagua)"/>']

    # las estelas: curvas que se encienden fuerte en el centro y se apagan
    # en las puntas, porque el plancton tarda en prenderse y en apagarse
    for e in range(7):
        y0 = w * (0.16 + 0.11 * e) + rng.uniform(-6, 6)
        amp = rng.uniform(w * 0.03, w * 0.075)
        fase = rng.uniform(0, 6.3)
        largo = rng.uniform(0.55, 0.98)
        x0 = rng.uniform(0, w * (1 - largo))
        p.append(f'<ellipse cx="{x0+w*largo*0.5:.0f}" cy="{y0:.0f}" '
                 f'rx="{w*largo*0.42:.0f}" ry="{w*0.07:.0f}" fill="url(#biglow)"/>')
        N = 44
        for k in range(N):
            t0, t1 = k / N, (k + 1) / N
            def pt(t):
                x = x0 + w * largo * t
                y = y0 + amp * math.sin(fase + t * 6.0) + amp * 0.35 * math.sin(fase + t * 14.0)
                return x, y
            xa, ya = pt(t0); xb, yb = pt(t1)
            # brillo tipo campana: máximo a la mitad de la estela
            br = math.sin(math.pi * ((t0 + t1) / 2)) ** 1.6
            p.append(f'<line x1="{xa:.1f}" y1="{ya:.1f}" x2="{xb:.1f}" y2="{yb:.1f}" '
                     f'stroke="#CFFFEC" stroke-width="{0.7+1.9*br:.2f}" '
                     f'stroke-linecap="round" opacity="{0.10+0.80*br:.2f}"/>')

    # chispas sueltas: plancton que se prendió por su cuenta
    for _ in range(90):
        sx, sy = rng.uniform(0, w), rng.uniform(w * 0.05, w * 0.95)
        p.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="{rng.uniform(0.35,1.2):.2f}" '
                 f'fill="{AURORA}" opacity="{rng.uniform(0.15,0.75):.2f}"/>')
    p.append('</svg>')
    return ''.join(p)


def svg_murmuracion(w=240):
    """La bandada sola. Aquí el verde no toca.

    ⚠️ LA v1 LEÍA COMO MANCHA — a tamaño de tarjeta parecía huella de dedo. Dos
    causas, las dos de fondo:
      · la densidad era un óvalo centrado, así que la bandada no tenía SILUETA,
        sólo era una nube redonda
      · todas las marcas medían casi igual, y sin variación de tamaño no hay
        profundidad: se ve textura plana en vez de miles de cuerpos en el aire

    La v2 le da forma de GOTA que se arrastra — denso en la cabeza y
    deshilachándose en la cola, que es como se ven de verdad: la bandada se
    comprime donde va y deja estela por donde vino. Y el tamaño de cada marca
    cambia mucho, para que unos pájaros se lean cerca y otros lejos.
    """
    rng = np.random.default_rng(31)
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         f'<rect width="{w}" height="{w}" fill="{HUESO}"/>']

    # la silueta: cabeza densa arriba-derecha, cola que se arrastra abajo-izq
    def dens(x, y):
        hx, hy = w * 0.66, w * 0.40                 # cabeza de la gota
        tx, ty = w * 0.20, w * 0.66                 # punta de la cola
        vx, vy = hx - tx, hy - ty
        L2 = vx * vx + vy * vy
        t = max(0.0, min(1.0, ((x - tx) * vx + (y - ty) * vy) / L2))
        px, py = tx + vx * t, ty + vy * t
        d = math.hypot(x - px, y - py)
        ancho = w * (0.045 + 0.115 * t ** 1.5)      # angosta atrás, ancha adelante
        return math.exp(-(d / ancho) ** 2) * (0.30 + 0.70 * t)

    cuerpos_ = []
    intentos = 0
    while len(cuerpos_) < 1250 and intentos < 90000:
        intentos += 1
        x, y = rng.uniform(0, w), rng.uniform(0, w * 0.84)
        if rng.random() > dens(x, y):
            continue
        u, v = campo(x / (w / W), y / (w / W))
        cuerpos_.append((x, y, math.degrees(math.atan2(v, u)), dens(x, y)))

    p.append(f'<g fill="{CENIZA}">')
    for x, y, a, d in cuerpos_:
        # rango de tamaño ANCHO = profundidad. Unos cerca, otros lejos.
        L = (0.9 + 3.4 * d) * (0.4 + 1.9 * float(rng.random()))
        p.append(f'<g transform="translate({x:.1f},{y:.1f}) rotate({a:.0f})">'
                 f'<ellipse rx="{L:.2f}" ry="{max(0.34, L*0.22):.2f}" '
                 f'opacity="{0.22+0.66*d:.2f}"/></g>')
    p.append('</g>')

    # tres rezagados sueltos: la bandada no tiene borde limpio
    for _ in range(3):
        x, y = rng.uniform(w * 0.06, w * 0.30), rng.uniform(w * 0.16, w * 0.34)
        p.append(f'<g transform="translate({x:.1f},{y:.1f}) rotate({rng.uniform(-25,10):.0f})">'
                 f'<ellipse rx="2.6" ry="0.7" fill="{CENIZA}" opacity="0.5"/></g>')

    p.append(f'<line x1="{w*0.10:.0f}" y1="{w*0.86:.0f}" x2="{w*0.90:.0f}" '
             f'y2="{w*0.86:.0f}" stroke="{CENIZA}" stroke-width="1.2" opacity="0.4"/>')
    p.append('</svg>')
    return ''.join(p)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    for nombre, gen in [('amr-ofrenda', svg),
                        ('ofrenda-biolum', svg_biolum),
                        ('ofrenda-murmuracion', svg_murmuracion)]:
        dst = os.path.join(HERE, 'art', f'{nombre}.svg')
        s = gen()
        with open(dst, 'w') as f:
            f.write(s)
        print(f'{nombre:22s} {len(s)//1024:4d} KB')
