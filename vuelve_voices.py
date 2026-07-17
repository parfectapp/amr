#!/usr/bin/env python3
"""VUELVE — paleta soul propia (nada compartido con otros discos).
La pieza central: VOZ DE MUJER cantada por síntesis de frase continua —
contorno de F0 con scoops y legato, vibrato que entra tarde, jitter humano,
formantes femeninas con morph entre vocales, y aire de respiración."""
import numpy as np
from dream_core import SR, lp, hp, bp, sat, sat_warm

def midi_f(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)

# formantes FEMENINAS (F1,F2,F3) + ganancias
FORM = dict(a=((860, 1.0), (1220, 0.5), (2810, 0.28)),
            e=((560, 1.0), (2100, 0.42), (2900, 0.25)),
            i=((310, 1.0), (2500, 0.4), (3300, 0.22)),
            o=((555, 1.0), (950, 0.55), (2600, 0.22)),
            u=((370, 1.0), (950, 0.45), (2650, 0.18)))

def sing(notes, rng, gain=1.0, breath=0.09, vib_depth=28.0):
    """canta una FRASE completa. notes = [(midi|None, beats, vocal)] a 120 BPM.
    Una sola fuente glotal continua → el legato es real, no notas pegadas."""
    beat = 0.5  # s por beat a 120
    total = int(sum(b for _, b, _ in notes) * beat * SR) + int(0.4 * SR)
    f0 = np.zeros(total, np.float32)
    amp = np.zeros(total, np.float32)
    segs = []                                   # (i0, i1, vocal) para el morph
    pos = 0.0
    prev_f = None
    for (m, beats, vow) in notes:
        n = int(beats * beat * SR)
        i0 = int(pos * SR)
        if m is None:                            # respiro
            prev_f = None
        else:
            f = midi_f(m)
            t = np.arange(n) / SR
            # scoop de entrada (o glide legato desde la nota anterior)
            start = prev_f if prev_f else f * 0.945
            gl = start + (f - start) * np.minimum(1.0, t / (0.06 if prev_f else 0.09))
            # vibrato que ENTRA TARDE (como cantante real) + jitter
            vibenv = np.minimum(1.0, np.maximum(0.0, t - 0.22) / 0.3)
            vib = 2.0 ** (vib_depth * vibenv * np.sin(2 * np.pi * 5.6 * t + rng.uniform(0, 6)) / 1200)
            jit = 2.0 ** (rng.normal(0, 3.5) / 1200)
            f0[i0:i0 + n] = (gl * vib * jit).astype(np.float32)
            # dinámica de la nota: crece, sostiene, suelta
            a = np.minimum(1.0, t / 0.05) * (0.85 + 0.15 * np.minimum(1.0, t / 0.4))
            a *= np.minimum(1.0, np.maximum(0.05, (beats * beat - t)) / 0.12)
            amp[i0:i0 + n] = a.astype(np.float32)
            segs.append((i0, i0 + n, vow))
            prev_f = f
        pos += beats * beat
    # ---- fuente glotal: 22 armónicos con caída natural
    ph = 2 * np.pi * np.cumsum(f0) / SR
    src = np.zeros(total, np.float32)
    for h in range(1, 23):
        src += (np.sin(h * ph) / (h ** 1.25)).astype(np.float32)
    src *= amp
    # ---- morph de formantes: filtra por segmento con crossfade de 50 ms
    out = np.zeros(total, np.float32)
    xf = int(0.05 * SR)
    for (i0, i1, vow) in segs:
        a0, a1 = max(0, i0 - xf), min(total, i1 + xf)
        seg = src[a0:a1]
        v = sum(bp(seg, fq * 0.88, fq * 1.12, 2) * g for fq, g in FORM[vow])
        v += seg * 0.10                          # un poco de fuente directa = presencia
        w = np.ones(a1 - a0, np.float32)
        w[:min(xf, len(w))] = np.linspace(0, 1, min(xf, len(w)))
        w[-min(xf, len(w)):] = np.linspace(1, 0, min(xf, len(w)))
        out[a0:a1] += v * w
    # ---- aire: respiración filtrada por la boca, más al inicio de frase
    br = hp(rng.standard_normal(total).astype(np.float32), 1400, 2) * amp * breath
    br[:int(0.15 * SR)] *= 2.2
    out = out + br
    out = sat(out * 0.5, 1.25, 0.08)
    return lp(out, 8200, 2) * gain

def coros(notes, rng, semis=(4, 7), gain=0.45):
    """armonías: la misma frase cantada arriba, desafinadas y atrasadas — el coro."""
    total = None; out = None
    for k, s in enumerate(semis):
        nn = [(m + s if m is not None else None, b, v) for (m, b, v) in notes]
        v = sing(nn, np.random.default_rng(rng.integers(1 << 30)), gain=gain * (0.8 ** k), breath=0.13)
        if out is None: out = v.copy()
        else:
            d = int(0.018 * SR * (k + 1))
            out[d:] += v[:len(v) - d]
    return out

# ---------------- instrumentos soul (propios de este single) ----------------
def epiano(f, dur, rng):
    """piano eléctrico soul: FM tine 1:3.7 índice bajo + cuerpo, chorus lento."""
    n = int(dur * SR); t = np.arange(n) / SR
    bell = np.exp(-t / 0.045)
    x = np.sin(2 * np.pi * f * t + 0.55 * bell * np.sin(2 * np.pi * f * 3.7 * t))
    x += 0.25 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t / (dur * 0.5))
    x *= np.exp(-t / (dur * 0.8)) * (1 + 0.08 * np.sin(2 * np.pi * 0.9 * t + rng.uniform(0, 6)))
    return sat(x.astype(np.float32) * 0.6, 1.35, 0.14)

def bass_soul(f, dur, rng):
    """sub redondo y lento: seno + octava suave, sin dientes."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.22 * np.sin(2 * np.pi * f * 2 * t)
    env = np.minimum(1.0, t / 0.025) * np.exp(-np.maximum(0.0, t - dur * 0.8) / 0.09)
    return lp(sat_warm((x * env).astype(np.float32)), 420, 2) * 0.6

def kick_soul():
    n = int(0.4 * SR); t = np.arange(n) / SR
    f = 45.0 + 42.0 * np.exp(-t / 0.024)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.17)
    return lp(sat(x.astype(np.float32), 1.25, 0.06), 2000, 2) * 0.8

def shaker_brush(rng):
    n = int(0.07 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32) * (np.exp(-t / 0.035) * (1 - np.exp(-t / 0.008)))
    return bp(x, 3200, 7000, 2) * rng.uniform(0.6, 0.9)

def rim_warm(rng):
    n = int(0.07 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * rng.uniform(1250, 1500) * t) * np.exp(-t / 0.011)
    x += 0.3 * rng.standard_normal(n) * np.exp(-t / 0.003)
    return bp(x.astype(np.float32), 700, 3600, 2) * 0.55

def conga_soft(rng, open_=True):
    dec = (0.13 if open_ else 0.05) * rng.uniform(0.9, 1.1)
    n = int(dec * 6 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * rng.uniform(165, 195) * (1 + 0.18 * np.exp(-t / 0.012)) * t) * np.exp(-t / dec)
    return sat(x.astype(np.float32) * 0.6, 1.3, 0.08)

def hat_gentle(rng, open_=False):
    dec = (0.22 if open_ else 0.03) * rng.uniform(0.9, 1.1)
    n = int(dec * 6 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32) * np.exp(-t / dec)
    return hp(x, 7800, 2) * (0.3 if open_ else 0.36) * rng.uniform(0.85, 1.0)

def pad_glass(f, dur, rng):
    """pad de vidrio: senos 1/2/3 con batido lento, muy suave."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for det, g in ((-4, 0.7), (0, 1.0), (5, 0.6)):
        fv = f * 2 ** (det / 1200)
        x += ((np.sin(2 * np.pi * fv * t) + 0.4 * np.sin(2 * np.pi * fv * 2 * t)
               + 0.15 * np.sin(2 * np.pi * fv * 3 * t)) * g).astype(np.float32)
    env = np.minimum(1.0, t / 0.6) * np.minimum(1.0, np.maximum(0.0, dur - t) / 0.5)
    return (x * env * 0.16).astype(np.float32)

if __name__ == '__main__':
    from dream_core import wav_write, spectrum_pct
    rng = np.random.default_rng(11)
    # frase de prueba: la voz sola, melodía soul en La menor
    PH = [(69, 1.5, 'o'), (72, 0.5, 'o'), (71, 1.0, 'e'), (69, 1.0, 'a'), (None, 0.5, 'a'),
          (67, 0.75, 'u'), (69, 0.75, 'e'), (64, 2.0, 'o')]
    v = sing(PH, rng, gain=1.0)
    h = coros(PH, rng, semis=(4,), gain=0.4)
    mix = v.copy(); mix[:len(h)] += h[:len(mix)]
    mix /= (np.abs(mix).max() + 1e-9)
    wav_write('_test_voz.wav', np.stack([mix, mix]))
    s = spectrum_pct(mix)
    print('VOZ:', {k: round(vv, 1) for k, vv in s.items()})
    print('dur:', round(len(mix) / SR, 1), 's — _test_voz.wav para escuchar')
