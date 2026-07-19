#!/usr/bin/env python3
"""INSTRUMENTOS — sampler de instrumentos REALES. El fin de los sintetizadores.

André, tres veces y cada vez más claro:
  "los que tú haces luego se escucha como videojuego"
  "cuando te digo videojuego justo a eso me refiero, esos que tú haces"
  "elimínalos por completo y empieza a descargar cosas de calidad"

Esto lo cumple. Toda nota melódica sale ahora de una GRABACIÓN de un instrumento
de verdad (VCSL, CC0 1.0 verificado leyendo su LICENSE), no de sumar sierras.

CÓMO FUNCIONA
  VCSL nombra cada archivo con su nota adentro:
      Mbira6_Normal_MainSpirit_B2_k8_vl3_rr2.wav
                              ^^ nota  ^^^ capa de velocity  ^^^ round-robin
  Se escanea la carpeta, se saca la nota de cada nombre, y se arma un mapa
  instrumento → {nota MIDI: [archivos]}. Al pedir una nota:
    · si existe grabada, se usa TAL CUAL (cero procesamiento)
    · si no, se toma la MÁS CERCANA y se resamplea el mínimo necesario
  Nunca se estira más de 4 semitonos: más allá el timbre se deforma y vuelve a
  sonar a sintetizador, que es justo lo que estamos matando.

  Los round-robin y las capas de velocity se eligen al azar por golpe — así dos
  notas iguales seguidas NO son el mismo archivo, que es el "copy-paste
  robótico" que ya habíamos arreglado en la batería con kit.vary().
"""
import os, re, glob, random
import numpy as np
from dream_core import SR, ffdecode

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(HERE, '_samples', 'vcsl')

# nota en el nombre: _C4_ · _F#3_ · _Bb2_ · _A-1_
_RE = re.compile(r'_([A-G])([#b]?)(-?\d)[_.]')
_PC = {'C':0,'D':2,'E':4,'F':5,'G':7,'A':9,'B':11}

def _midi(nombre):
    m = _RE.search(nombre)
    if not m: return None
    p, alt, octa = m.group(1), m.group(2), int(m.group(3))
    v = _PC[p] + (1 if alt=='#' else -1 if alt=='b' else 0)
    return 12*(octa+1) + v            # C4 = 60, como el estándar

# ---- catálogo curado: nombre corto → cómo reconocerlo en la ruta
CATALOGO = {
 'kalimba':   ('kalimba',),
 'mbira':     ('mbira',),
 'balafon':   ('balafon',),
 'marimba':   ('marimba',),
 'vibrafono': ('vibraphone',),
 'glocken':   ('glockenspiel',),
 'xilofono':  ('xylophone',),
 'celesta':   ('celesta',),
 'arpa':      ('harp',),
 'piano':     ('piano',),
 'organo':    ('organ',),
 'guitarra':  ('guitar',),
 'campana':   ('bell', 'chime', 'crotale'),
 'cuenco':    ('singing bowl', 'bowl'),
 'gong':      ('gong', 'tam-tam'),
 'flauta':    ('flute', 'recorder', 'ocarina', 'pan pipe'),
 'contrabajo':('contrabass', 'double bass'),
}

_MAPA = None      # instrumento → {midi: [rutas]}
_CACHE = {}       # ruta → audio decodificado

def mapa():
    global _MAPA
    if _MAPA is not None: return _MAPA
    _MAPA = {}
    if not os.path.isdir(RAIZ): return _MAPA
    for f in glob.glob(os.path.join(RAIZ, '**', '*.wav'), recursive=True):
        n = _midi(os.path.basename(f))
        if n is None: continue
        low = f.lower()
        for inst, claves in CATALOGO.items():
            if any(c in low for c in claves):
                _MAPA.setdefault(inst, {}).setdefault(n, []).append(f)
                break
    return _MAPA

def hay(inst):
    return inst in mapa() and len(mapa()[inst]) > 0

def instrumentos():
    """Los que de verdad quedaron utilizables, con su rango."""
    out = []
    for k, v in sorted(mapa().items()):
        if not v: continue
        ns = sorted(v)
        out.append((k, len(ns), ns[0], ns[-1], sum(len(x) for x in v.values())))
    return out

def _carga(ruta):
    if ruta not in _CACHE:
        if len(_CACHE) > 220: _CACHE.clear()          # techo de memoria
        x = ffdecode(ruta, mono=True).astype(np.float32)
        nz = np.nonzero(np.abs(x) > 1.5e-4)[0]
        if len(nz): x = x[nz[0]:]
        m = float(np.abs(x).max())
        _CACHE[ruta] = (x/m if m > 0 else x)
    return _CACHE[ruta]

MAX_ESTIRA = 4        # semitonos. Más allá el timbre se deforma y vuelve a sonar sintético.

def nota(inst, midi, dur=None, rng=None, gain=1.0, vel=1.0, largo_var=0.0):
    """Nota tocada por el instrumento REAL.

    ⭐ vel (0..1) NO es sólo volumen — también CIERRA EL FILTRO.
    Un instrumento real tocado suave no suena igual pero más bajito: suena más
    OSCURO, porque se excita menos el cuerpo y salen menos armónicos. Es la
    técnica que se ve en el desglose de "Marea" de Fred again: mapear velocity
    al cutoff, y luego darle una velocity distinta a CADA nota — de ahí se
    concluye que la tocó a mano.

    Y encaja con lo medido en la literatura: el tiempo de ataque PERCIBIDO se
    mueve entre 23 y 83 ms según la envolvente (Frontiers 2018), o sea que
    variando timbre y envolvente corres la sensación de timing decenas de ms
    SIN sacar una sola nota de la rejilla — que es justo lo que los estudios
    de humanización piden (cuantizado gana; el jitter aleatorio pierde).

    largo_var (0..1): variación aleatoria del LARGO por golpe. En el mismo
    desglose: los hats varían en largo Y afinación, no sólo en volumen."""
    M = mapa().get(inst)
    if not M:
        # ⚠️ ANTES devolvía silencio. Eso es peor que fallar: André borró la
        # librería para liberar disco y el motor siguió "tocando" notas mudas
        # sin avisar. Un hueco tiene que TRONAR, no disimularse.
        disponibles = ', '.join(sorted(mapa())) or 'NINGUNO'
        raise RuntimeError(
            f'INSTRUMENTO NO DISPONIBLE: "{inst}".\n'
            f'  Hay: {disponibles}\n'
            f'  ¿Falta la librería? Corre: python3 bajar_libreria.py')
    rng = rng or np.random
    disp = sorted(M)
    cerca = min(disp, key=lambda n: abs(n - midi))
    if abs(cerca - midi) > MAX_ESTIRA:                # fuera de rango: se transporta por octavas
        while midi - cerca > MAX_ESTIRA:  midi -= 12
        while cerca - midi > MAX_ESTIRA:  midi += 12
        cerca = min(disp, key=lambda n: abs(n - midi))
    x = _carga(rng.choice(M[cerca]))                  # round-robin al azar
    semis = midi - cerca
    if semis != 0:                                    # resample mínimo
        r = 2.0 ** (semis/12.0)
        n = int(len(x)/r)
        if n > 8:
            idx = np.minimum(len(x)-1, (np.arange(n)*r)).astype(np.int32)
            x = x[idx]
    # ---- velocity -> cutoff: suave = oscuro, fuerte = brillante
    v = float(np.clip(vel, 0.05, 1.0))
    if v < 0.985:
        from dream_core import lp
        # de ~1.2 kHz en pianissimo a ~18 kHz a fondo, curva perceptual
        corte = 1200.0 * (15.0 ** v)
        if corte < 16000.0:
            x = lp(x, float(corte), 2)
        x = x * (0.30 + 0.70 * v)          # y el volumen, claro
    if dur is not None and largo_var > 0 and rng is not None:
        dur = dur * (1.0 - largo_var * float(rng.random()))
    if dur is not None:
        n = int(dur*SR)
        if len(x) > n:
            x = x[:n].copy()
            f = min(int(0.012*SR), n//4)              # fade para no cortar seco
            if f > 2: x[-f:] *= np.linspace(1, 0, f).astype(np.float32)
        elif len(x) < n:
            x = np.concatenate([x, np.zeros(n-len(x), np.float32)])
    return x * gain

def acorde(inst, midis, dur=None, rng=None, gain=1.0, spread=0.012):
    """Varias notas con un rasgueo mínimo entre ellas — como lo tocaría una mano."""
    rng = rng or np.random
    voces = [nota(inst, m, dur, rng, gain) for m in midis]
    n = max(len(v) for v in voces) + int(spread*SR*len(midis))
    out = np.zeros(n, np.float32)
    for i, v in enumerate(voces):
        o = int(i*spread*SR)
        out[o:o+len(v)] += v
    return out / max(1.0, len(midis)**0.5)

if __name__ == '__main__':
    M = mapa()
    if not M:
        print(f'No hay samples en {RAIZ}. ¿Corrió bajar_libreria.py?'); raise SystemExit
    print(f'INSTRUMENTOS REALES disponibles (VCSL, CC0)\n')
    print(f'  {"instrumento":12s} {"notas":>5s} {"rango":>12s} {"archivos":>8s}')
    tot = 0
    for k, nn, lo, hi, arch in instrumentos():
        nom = lambda m: ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][m%12]+str(m//12-1)
        print(f'  {k:12s} {nn:5d} {nom(lo)+"–"+nom(hi):>12s} {arch:8d}')
        tot += arch
    print(f'\n  {len(M)} instrumentos · {tot} grabaciones')
    print('\nPrueba: una nota de cada uno…')
    rng = np.random.default_rng(1)
    for k, *_ in instrumentos():
        x = nota(k, 60, 0.6, rng)
        ok = np.isfinite(x).all() and float(np.abs(x).max()) > 1e-4
        print(f'  {"✓" if ok else "✗"} {k:12s} pico {float(np.abs(x).max()):.2f}')
