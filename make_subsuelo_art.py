#!/usr/bin/env python3
"""Arte de SUBSUELO — íconos en el estilo de la casa, no escenas atmosféricas.

⚠️ ESTE ARCHIVO SE REHIZO. La primera versión eran escenas de degradado a sangre
(estratos, columnas hexagonales llenando el cuadro, anillos concéntricos).
André: "cambia los dibujos de los subsuelo por algo del estilo". Tenía razón —
el catálogo tiene un ESTILO y esas escenas no eran de él.

EL ESTILO DE LA CASA (ver art/guer-cactus.svg, guer-serpiente.svg, tulum-atlas):
  · fondo transparente (se ve el hueso de la tarjeta)
  · UN objeto icónico, dibujado con trazo grueso negro (#141210, width ~14-15)
  · un glow radial suave del color del disco detrás
  · una sombra elíptica de piso (el objeto está parado en algo)
  · detalles finos en el color de acento (width ~2.6) y dos puntitos negros
Es un grabado, no una fotografía. Cada disco es un objeto reconocible.

LOS TRES OBJETOS DE SUBSUELO (industrial, subterráneo, óxido):
  · portada  = una escalera que baja — el concepto del disco: ocho niveles
               hacia abajo, de la banqueta a la roca
  · BASALTO  = las columnas de basalto (los órganos), la roca del fondo
  · DUCTO    = una rejilla de ventilación, el tiro de aire
"""
import os, math

HERE = os.path.dirname(os.path.abspath(__file__))
TINTA = '#141210'          # el negro cálido del estilo
OXIDO = '#B4501F'
HUESO = '#EAE6DF'


def _glow(idg, cx, cy, r):
    return (f'<defs><radialGradient id="{idg}" cx="50%" cy="50%" r="50%">'
            f'<stop offset="0%" stop-color="{OXIDO}" stop-opacity="0.42"/>'
            f'<stop offset="55%" stop-color="{OXIDO}" stop-opacity="0.14"/>'
            f'<stop offset="100%" stop-color="{OXIDO}" stop-opacity="0"/>'
            f'</radialGradient></defs>'
            f'<ellipse cx="{cx}" cy="212" rx="54" ry="8" fill="{TINTA}" opacity="0.05"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{idg})"/>')


def _dots():
    return (f'<circle cx="60" cy="150" r="2.2" fill="{TINTA}"/>'
            f'<circle cx="186" cy="172" r="2.4" fill="{TINTA}"/>')


def svg_portada(w=240):
    """Escalera que baja — el concepto del disco hecho ícono: ocho niveles hacia
    abajo, de la banqueta a la roca. La primera versión era una tapa de
    alcantarilla, pero con los radios se leía como RUEDA DE CARRETA, no como
    subsuelo. La escalera no se confunde con nada: es bajar, y punto. Abajo, el
    óxido encendido = el fondo (BASALTO)."""
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">']
    # glow del fondo abajo-derecha (hacia donde se desciende)
    p.append(f'<defs><radialGradient id="ssp" cx="50%" cy="50%" r="50%">'
             f'<stop offset="0%" stop-color="{OXIDO}" stop-opacity="0.5"/>'
             f'<stop offset="60%" stop-color="{OXIDO}" stop-opacity="0.16"/>'
             f'<stop offset="100%" stop-color="{OXIDO}" stop-opacity="0"/>'
             f'</radialGradient></defs>')
    p.append(f'<ellipse cx="120" cy="214" rx="72" ry="8" fill="{TINTA}" opacity="0.05"/>')
    p.append(f'<circle cx="150" cy="176" r="62" fill="url(#ssp)"/>')
    # la escalera: masa sólida con el borde superior escalonado (6 escalones),
    # bajando de arriba-izquierda a abajo-derecha. Sólida = no se lee como barras.
    x0, y0, paso = 54, 60, 21
    esc = [(x0, y0)]
    for i in range(6):
        esc.append((x0 + (i+1)*paso, y0 + i*paso))       # tramo horizontal (huella)
        esc.append((x0 + (i+1)*paso, y0 + (i+1)*paso))    # tramo vertical (contrahuella)
    borde = ' '.join(f'{x},{y}' for x, y in esc)
    base = f'{x0+6*paso},202 {x0},202'
    p.append(f'<polygon points="{borde} {base}" fill="{TINTA}"/>')
    # nariz de óxido en el filo de cada escalón (donde pega la luz)
    for i in range(6):
        xa = x0 + (i+1)*paso
        ya = y0 + i*paso
        p.append(f'<line x1="{xa-paso}" y1="{ya}" x2="{xa}" y2="{ya}" '
                 f'stroke="{OXIDO}" stroke-width="4" stroke-linecap="round"/>')
    # el último escalón se hunde en el óxido: un bloque encendido al fondo
    p.append(f'<rect x="{x0+6*paso-4}" y="{y0+6*paso-4}" width="10" height="26" fill="{OXIDO}"/>')
    p.append(_dots())
    p.append('</svg>')
    return ''.join(p)


def svg_basalto(w=240):
    """Columnas de basalto — los órganos. Prismas verticales de distinta altura,
    parados juntos, con la cara de arriba encendida en óxido (la roca del fondo,
    el pico del disco)."""
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         _glow('ssb', 120, 128, 60)]
    # cinco columnas: (x, alto). El suelo común queda en y=206.
    cols = [(58, 92), (86, 128), (116, 150), (146, 116), (174, 138)]
    anch = 24
    suelo = 206
    for x, alto in cols:
        top = suelo - alto
        # el fuste
        p.append(f'<rect x="{x}" y="{top}" width="{anch}" height="{alto}" fill="{TINTA}"/>')
        # la cara de arriba: un rombo (hexágono en perspectiva) encendido
        d = anch * 0.34
        cara = f'{x},{top} {x+anch},{top} {x+anch-d:.0f},{top-9} {x+d:.0f},{top-9}'
        p.append(f'<polygon points="{cara}" fill="{OXIDO}"/>')
        # una junta horizontal en el fuste (las columnas se agrietan por tramos)
        jy = top + alto * 0.42
        p.append(f'<line x1="{x}" y1="{jy:.0f}" x2="{x+anch}" y2="{jy:.0f}" '
                 f'stroke="{HUESO}" stroke-width="1.4" opacity="0.35"/>')
    # línea de suelo
    p.append(f'<rect x="46" y="{suelo}" width="150" height="6" rx="3" fill="{OXIDO}"/>')
    p.append(_dots())
    p.append('</svg>')
    return ''.join(p)


def svg_ducto(w=240):
    """Rejilla de ventilación — el tiro de aire. Un aro grueso con persianas
    horizontales; por las rendijas se cuela el óxido, como la luz al fondo del
    tiro."""
    cx = cy = 120
    p = [f'<svg viewBox="0 0 {w} {w}" xmlns="http://www.w3.org/2000/svg">',
         _glow('ssd', cx, cy, 62),
         f'<defs><clipPath id="ssdc"><circle cx="{cx}" cy="{cy}" r="58"/></clipPath></defs>']
    # el óxido detrás de las rendijas (la luz colándose)
    p.append(f'<circle cx="{cx}" cy="{cy}" r="58" fill="{OXIDO}" opacity="0.5"/>')
    # las persianas: barras horizontales gruesas, recortadas al círculo
    p.append(f'<g clip-path="url(#ssdc)">')
    y = cy - 52
    while y < cy + 58:
        p.append(f'<rect x="{cx-64}" y="{y:.0f}" width="128" height="12" fill="{TINTA}"/>')
        y += 20
    p.append('</g>')
    # marco grueso
    p.append(f'<circle cx="{cx}" cy="{cy}" r="58" fill="none" stroke="{TINTA}" stroke-width="14"/>')
    # cuatro tornillos del marco
    for k in range(4):
        a = k / 4 * 2 * math.pi + math.pi / 4
        p.append(f'<circle cx="{cx+math.cos(a)*58:.1f}" cy="{cy+math.sin(a)*58:.1f}" '
                 f'r="4" fill="{TINTA}"/>')
    p.append(_dots())
    p.append('</svg>')
    return ''.join(p)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'art'), exist_ok=True)
    for nombre, gen in [('subsuelo', svg_portada),
                        ('subsuelo-basalto', svg_basalto),
                        ('subsuelo-ducto', svg_ducto)]:
        dst = os.path.join(HERE, 'art', f'{nombre}.svg')
        t = gen()
        with open(dst, 'w') as f:
            f.write(t)
        print(f'{nombre:22s} {len(t)} B')
