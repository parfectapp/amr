#!/usr/bin/env python3
"""TAMBOR — paleta afro NUEVA. Nada compartido con hechizo/colibrí:
kora (Karplus-Strong), balafón con zumbido de calabaza, coro de formantes,
bajo de goma con glide, udu de barro, órgano suave, kick afro profundo."""
import numpy as np
from dream_core import SR, lp, hp, bp, sat, sat_warm

def midi_f(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)

def kick_afro():
    """kick afro: más grave (42Hz), boom largo y suave — el latido del ritual."""
    n = int(0.55 * SR); t = np.arange(n) / SR
    f = 42.0 + 40.0 * np.exp(-t / 0.03)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.24)
    x += 0.08 * np.sin(2 * np.pi * 84 * t) * np.exp(-t / 0.07)
    return lp(sat(x.astype(np.float32), 1.3, 0.07), 2200, 2) * 0.85

def kora(f, dur, rng, bright=0.55):
    """kora (arpa africana): cuerda pulsada Karplus-Strong, vectorizada por periodos."""
    N = max(8, int(SR / f))
    periods = max(2, int(dur * f))
    buf = (rng.uniform(-1, 1, N) * (1 - bright) + np.sin(2 * np.pi * np.arange(N) / N) * bright).astype(np.float32)
    out = np.empty(periods * N, np.float32)
    damp = 0.996 - 400.0 / (f * 90)          # cuerdas agudas mueren antes
    for k in range(periods):
        out[k * N:(k + 1) * N] = buf
        buf = 0.5 * (buf + np.roll(buf, 1)) * damp
    n = int(dur * SR)
    out = out[:n] if len(out) >= n else np.pad(out, (0, n - len(out)))
    att = np.minimum(1.0, np.arange(len(out)) / (0.002 * SR)).astype(np.float32)
    return sat(out * att * 0.8, 1.2, 0.05)

def balafon(f, dur, rng):
    """balafón: barra de madera (parcial 3.9x) + ZUMBIDO de la membrana de calabaza."""
    n = int(dur * SR); t = np.arange(n) / SR
    dec = 0.3 * rng.uniform(0.9, 1.1)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / dec)
    x += 0.3 * np.sin(2 * np.pi * f * 3.9 * t) * np.exp(-t / (dec * 0.3))
    buzz = np.sign(np.sin(2 * np.pi * f * t)).astype(np.float32) * rng.uniform(0.8, 1.0)
    buzz = bp(buzz * np.exp(-t / (dec * 0.8)).astype(np.float32), f * 3, f * 9, 2) * 0.35
    x += 0.2 * rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.004)
    return sat((x + buzz).astype(np.float32) * 0.7, 1.4, 0.1)

def bass_rubber(f0, f1, dur, rng, cutoff=520):
    """bajo de goma: triángulo cálido con GLIDE entre notas, ataque suave (Keinemusik)."""
    n = int(dur * SR); t = np.arange(n) / SR
    fs = f0 + (f1 - f0) * np.minimum(1.0, t / 0.07)
    ph = 2 * np.pi * np.cumsum(fs) / SR
    tri = (2 / np.pi) * np.arcsin(np.sin(ph))
    x = tri * 0.9 + 0.35 * np.sin(ph)
    env = np.minimum(1.0, t / 0.02) * np.exp(-np.maximum(0.0, t - dur * 0.75) / 0.08)
    return lp(sat_warm((x * env).astype(np.float32) * 1.2), cutoff, 2) * 0.55

def choir(f, dur, rng, vowel='a'):
    """coro humano sostenido: 3 voces desafinadas de formantes, ataque lento."""
    n = int(dur * SR); t = np.arange(n) / SR
    F = dict(a=(760, 1150, 2700), o=(480, 880, 2400), e=(500, 1750, 2450),
             u=(350, 780, 2200))[vowel]
    out = np.zeros(n, np.float32)
    for det, g in ((-7, 0.8), (0, 1.0), (8, 0.75)):
        fv = f * 2 ** (det / 1200) * (1 + 0.005 * np.sin(2 * np.pi * rng.uniform(4.5, 5.8) * t + rng.uniform(0, 6)))
        ph = 2 * np.pi * np.cumsum(fv) / SR
        gl = (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph) + 0.1 * np.sin(4 * ph)).astype(np.float32)
        v = sum(bp(gl, fq * 0.88, fq * 1.12, 2) * gg for fq, gg in zip(F, (1.0, 0.55, 0.3)))
        out += v * g
    env = np.minimum(1.0, t / 0.35) * np.minimum(1.0, np.maximum(0.0, (dur - t)) / 0.3)
    return (out * env * 0.33).astype(np.float32)

def organ_soft(f, dur, rng):
    """órgano de barras suave: senos 1/2/3/4 con trémolo leslie lento."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2 * t)
         + 0.28 * np.sin(2 * np.pi * f * 3 * t) + 0.15 * np.sin(2 * np.pi * f * 4 * t))
    trem = 1.0 + 0.12 * np.sin(2 * np.pi * 5.6 * t + rng.uniform(0, 6))
    env = np.minimum(1.0, t / 0.015) * np.exp(-np.maximum(0.0, t - dur * 0.6) / 0.12)
    return sat((x * trem * env).astype(np.float32) * 0.5, 1.3, 0.1)

def hit_udu(rng, deep=True):
    """udu de barro: 'whoop' hueco que cae — el agujero del cántaro."""
    n = int(0.3 * SR); t = np.arange(n) / SR
    f = (rng.uniform(140, 170) if deep else rng.uniform(220, 260)) * (0.45 ** (t / 0.3))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.14)
    x += 0.15 * rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.006)
    return sat(x.astype(np.float32) * 0.8, 1.4, 0.08)

def crickets(dur, rng):
    """grillos de noche: chirridos agudos pulsantes, muy al fondo."""
    n = int(dur * SR); x = np.zeros(n, np.float32)
    for _ in range(int(dur * 0.8)):
        p = rng.integers(0, max(1, n - int(0.8 * SR)))
        L = int(rng.uniform(0.4, 0.8) * SR); tt = np.arange(L) / SR
        fr = rng.uniform(4200, 5200)
        ch = np.sin(2 * np.pi * fr * tt) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * rng.uniform(18, 26) * tt)))
        x[p:p + L] += (ch * np.hanning(L) * 0.05).astype(np.float32)
    return x

if __name__ == '__main__':
    from dream_core import wav_write, spectrum_pct
    rng = np.random.default_rng(5)
    root = 57
    tests = {
        'kora':    lambda: np.concatenate([kora(midi_f(m), 0.6, rng) for m in (57, 60, 64, 62, 57, 64)]),
        'balafon': lambda: np.concatenate([balafon(midi_f(m), 0.4, rng) for m in (57, 60, 62, 64, 62, 60)]),
        'choir':   lambda: choir(midi_f(45), 3.0, rng, 'a') + choir(midi_f(52), 3.0, rng, 'o'),
        'bass':    lambda: np.concatenate([bass_rubber(midi_f(33), midi_f(m), 0.5, rng) for m in (33, 40, 36, 33)]),
        'organ':   lambda: organ_soft(midi_f(57), 1.0, rng) + organ_soft(midi_f(64), 1.0, rng),
        'udu':     lambda: np.concatenate([hit_udu(rng, d) for d in (True, False, True, True)]),
    }
    for name, fn in tests.items():
        x = fn().astype(np.float32); x /= (np.abs(x).max() + 1e-9)
        s = spectrum_pct(x)
        print(f'{name:8s} lowmid={s.get("lowmid",0):4.1f} mid={s.get("mid",0):4.1f} himid={s.get("himid",0):4.1f} air={s.get("air",0):4.1f}')
    print('paleta afro ok')
