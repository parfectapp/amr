#!/usr/bin/env python3
"""ANALIZA — saca tono y BPM de un archivo de audio, medidos, no adivinados.

Se necesita porque Gemini bautiza las rolas con títulos poéticos que NO dicen
cuál prompt las produjo. "Before The Sun Hits" puede ser PETRICOR o CENIZA.
Adivinar por el nombre y equivocarse rompe el arco armónico del set entero,
así que se mide.

TONO — Krumhansl-Schmuckler. Se arma un cromagrama (energía por clase de nota,
las 12), se correlaciona contra los 24 perfiles de tonalidad publicados por
Krumhansl y Kessler (1982) y gana el más parecido. Es el método estándar y su
punto débil conocido es confundir una tonalidad con su relativa (Fa mayor vs
Re menor comparten notas), así que se reporta también el segundo lugar: si el
1º y el 2º son relativos entre sí, la medición no distingue y hay que oír.

BPM — envolvente de onsets (flujo espectral rectificado) + autocorrelación.
Se busca sólo entre 100 y 140, y se dobla/parte al rango, porque un house de
121 se detecta igual de bien como 60.5 o 242.
"""
import sys, os
import numpy as np
from dream_core import SR, ffdecode

NOTAS = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

# Krumhansl & Kessler 1982 — perfiles de estabilidad tonal
KS_MAY = np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88])
KS_MEN = np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])


def cromagrama(x, sr=SR):
    """Energía por clase de nota, sumada sobre toda la rola."""
    n = 8192
    hop = 4096
    w = np.hanning(n).astype(np.float32)
    f = np.fft.rfftfreq(n, 1.0 / sr)
    # bin -> clase de nota (sólo 55 Hz a 2 kHz: abajo hay bombo, arriba hay aire)
    ok = (f > 55) & (f < 2000)
    midi = np.zeros(len(f))
    midi[ok] = 69 + 12 * np.log2(f[ok] / 440.0)
    clase = np.mod(np.round(midi).astype(int), 12)

    cro = np.zeros(12)
    for i in range(0, len(x) - n, hop):
        S = np.abs(np.fft.rfft(x[i:i + n] * w))
        S = S[ok]
        np.add.at(cro, clase[ok], S)
    return cro / max(1e-9, cro.sum())


def tono(cro):
    """Devuelve [(nombre, correlacion), ...] ordenado de mejor a peor."""
    out = []
    for t in range(12):
        for perfil, sufijo in ((KS_MAY, ' mayor'), (KS_MEN, ' menor')):
            p = np.roll(perfil, t)
            r = np.corrcoef(cro, p)[0, 1]
            out.append((NOTAS[t] + sufijo, float(r)))
    return sorted(out, key=lambda a: -a[1])


def son_relativas(a, b):
    """Fa mayor y Re menor son la misma escala — KS no las separa bien."""
    def parse(s):
        nom, mod = s.rsplit(' ', 1)
        return NOTAS.index(nom), mod
    ta, ma = parse(a)
    tb, mb = parse(b)
    if ma == mb:
        return False
    if ma == 'mayor':
        return (ta - 3) % 12 == tb          # relativa menor está 3 semitonos abajo
    return (ta + 3) % 12 == tb


def bpm(x, sr=SR):
    """Flujo espectral -> autocorrelación, forzado al rango de house."""
    n, hop = 1024, 512
    w = np.hanning(n).astype(np.float32)
    prev = None
    flujo = []
    for i in range(0, len(x) - n, hop):
        S = np.abs(np.fft.rfft(x[i:i + n] * w))
        if prev is not None:
            d = S - prev
            flujo.append(float(d[d > 0].sum()))      # sólo lo que SUBE = ataque
        prev = S
    e = np.array(flujo)
    e -= e.mean()
    ac = np.correlate(e, e, 'full')[len(e) - 1:]
    fps = sr / hop
    lo, hi = int(fps * 60 / 200), int(fps * 60 / 60)   # 60..200 BPM
    k = lo + int(np.argmax(ac[lo:hi]))
    b = 60.0 * fps / k
    while b < 100: b *= 2
    while b > 140: b /= 2
    return b


def analiza(ruta):
    x = ffdecode(ruta, mono=True).astype(np.float32)
    dur = len(x) / SR
    cro = cromagrama(x)
    ts = tono(cro)
    return dict(dur=dur, bpm=bpm(x), tono=ts[0], segundo=ts[1],
                ambiguo=son_relativas(ts[0][0], ts[1][0]))


if __name__ == '__main__':
    print(f'{"archivo":34s} {"largo":>6s} {"BPM":>6s}  {"tono":<10s} {"r":>5s}  '
          f'{"2º":<10s} {"r":>5s}')
    for r in sys.argv[1:]:
        try:
            d = analiza(r)
        except Exception as ex:
            print(f'{os.path.basename(r)[:34]:34s}  ! {ex}')
            continue
        m, s = divmod(int(d['dur']), 60)
        flag = '  ~relativas, no las separa' if d['ambiguo'] else ''
        print(f'{os.path.basename(r)[:34]:34s} {m:3d}:{s:02d} {d["bpm"]:6.1f}  '
              f'{d["tono"][0]:<10s} {d["tono"][1]:5.2f}  '
              f'{d["segundo"][0]:<10s} {d["segundo"][1]:5.2f}{flag}')
