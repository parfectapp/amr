#!/usr/bin/env python3
"""REJILLA — tempo exacto y dónde cae el compás 1.

La autocorrelación de analiza.py da 120.2 en ocho rolas seguidas, y eso huele a
artefacto: con hop de 512 muestras el retardo se cuantiza a frames enteros, y el
frame k=43 CORRESPONDE a 120.18 BPM. O sea que "120.2" es lo que se ve cuando el
tempo real es 120.000 — no una medición, un redondeo del método.

Importa porque el error se acumula. A 2:50 de rola, confundir 120.0 con 120.2
son 0.2/120 × 170 s ≈ 0.28 s de deriva: más de medio tiempo. Un set mezclado
sobre esa rejilla se despega solo.

CÓMO SE MIDE BIEN
  Se prueban tempos en malla fina (118–126 en pasos de 0.005) y para cada uno se
  suma la envolvente de onsets en las posiciones donde caería el pulso. El tempo
  correcto es el que más energía acumula, y como se suma sobre TODA la rola, un
  error chico desalinea los golpes del final y hunde el puntaje. Esa acumulación
  es justo lo que le falta a la autocorrelación de retardo corto.

  La fase (dónde empieza el compás) sale igual: se prueban los 4 desplazamientos
  de tiempo dentro del compás y gana el que pone los bombos en el 1.
"""
import numpy as np
from dream_core import SR, ffdecode

HOP = 256


def onsets(x, sr=SR):
    """Envolvente de ataques: flujo espectral rectificado, sólo lo que sube."""
    n, hop = 1024, HOP
    w = np.hanning(n).astype(np.float32)
    prev = None
    e = []
    for i in range(0, len(x) - n, hop):
        S = np.abs(np.fft.rfft(x[i:i + n] * w))
        if prev is not None:
            d = S - prev
            e.append(float(d[d > 0].sum()))
        prev = S
    e = np.array(e, dtype=np.float64)
    e -= e.mean()
    return np.maximum(e, 0.0)


def tempo_fino(e, lo=118.0, hi=126.0, paso=0.005, sr=SR):
    """El tempo que hace coincidir la rejilla con los ataques a lo largo de TODO."""
    fps = sr / HOP
    mejor, mejor_b = -1.0, None
    b = lo
    while b <= hi:
        per = 60.0 * fps / b                       # frames por tiempo
        idx = np.round(np.arange(0, len(e), per)).astype(int)
        idx = idx[idx < len(e)]
        s = float(e[idx].sum()) / len(idx)         # normalizado: más lento = menos pulsos
        if s > mejor:
            mejor, mejor_b = s, b
        b += paso
    return mejor_b, mejor


def fase_compas(e, bpm, sr=SR):
    """Cuál de los 4 tiempos del compás es el 1 — el que carga los bombos."""
    fps = sr / HOP
    per = 60.0 * fps / bpm
    mejor, mejor_f = -1.0, 0
    for f in range(4):
        idx = np.round(np.arange(f * per, len(e), per * 4)).astype(int)
        idx = idx[idx < len(e)]
        s = float(e[idx].sum()) / max(1, len(idx))
        if s > mejor:
            mejor, mejor_f = s, f
    return mejor_f


def rejilla(ruta):
    """Devuelve (bpm, offset_en_muestras_del_primer_compás)."""
    x = ffdecode(ruta, mono=True).astype(np.float32)
    xb = np.ascontiguousarray(x)                    # el bombo manda la rejilla
    from dream_core import lp
    e = onsets(lp(xb, 200.0, 4))
    b, _ = tempo_fino(e)
    f = fase_compas(e, b)
    off = int(round(f * (60.0 / b) * SR))
    return b, off, len(x) / SR


if __name__ == '__main__':
    import sys, os
    print(f'{"archivo":30s} {"BPM":>8s} {"compás s":>9s} {"offset":>8s}')
    for r in sys.argv[1:]:
        b, off, dur = rejilla(r)
        print(f'{os.path.basename(r)[:30]:30s} {b:8.3f} {240.0/b:9.4f} {off:8d}')
