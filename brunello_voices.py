#!/usr/bin/env python3
"""BRUNELLO — paleta cosmic-disco / melodic-techno retro-futurista (estilo Brunello,
"Science Fiction"). Investigado: su firma es la PERCUSIÓN drum-line (batería de
marcha) + synths análogos "space disco" (arpegios con delay punteado, leads
desafinados, pads cósmicos, láseres) sobre un 4x4 909 cálido. Re menor, ~127 BPM.

⚠️ BAJO LIMPIO Y CÁLIDO — NADA de saw+drive agresivo (André rechazó ese bajo
'durísimo/sobresaturado' en PLAYA y BATUQUE). Aquí el bajo es sine+triángulo por
un LP suave, sin resonancia ni saturación fuerte. Paleta propia."""
import numpy as np
from dream_core import SR, lp, hp, bp, sat, sat_warm

def midi_f(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)

# Re menor natural (D E F G A Bb C) y su pentatónica
DMIN = [0, 2, 3, 5, 7, 8, 10]
DMINP = [0, 3, 5, 7, 10]
def sdeg(root, d, o=0, scale=DMIN): return root + scale[d % len(scale)] + 12 * (d // len(scale) + o)
def pdeg(root, d, o=0): return root + DMINP[d % 5] + 12 * (d // 5 + o)

def _tri(ph):  # triángulo limpio
    return (2.0 / np.pi) * np.arcsin(np.sin(ph)).astype(np.float32)

# ==================================================================== BATERÍA 909
def kick_disco():
    """kick 909/analógico redondo y punchy — corto, deja respirar el sub."""
    n = int(0.36 * SR); t = np.arange(n) / SR
    f = 58.0 + 78.0 * np.exp(-t / 0.026)                    # pitch env ~136→58Hz
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.16)
    clic = np.exp(-t / 0.0025) * np.sin(2 * np.pi * 1500 * t)
    x = sat(body.astype(np.float32), 1.35, 0.05) + 0.28 * clic.astype(np.float32)
    return lp(x, 3200, 2) * 0.9

def clap(rng):
    n = int(0.22 * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for d in (0.0, 0.008, 0.016):
        off = int(d * SR)
        x[off:] += (rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.011))[:n - off] * 0.8
    tail = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.11) * 0.5
    return bp((x + tail), 1100, 5600, 2) * 0.55

def hat(rng, open_=False):
    dec = (0.18 if open_ else 0.028) * rng.uniform(0.9, 1.1)
    n = int(dec * 6 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32)
    x += 0.3 * np.sign(np.sin(2 * np.pi * 8000 * t)).astype(np.float32)
    x *= np.exp(-t / dec)
    return hp(x, 7800, 2) * (0.22 if open_ else 0.3) * rng.uniform(0.85, 1.0)

def shaker(rng):
    n = int(0.05 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32) * (np.exp(-t / 0.026) * (1 - np.exp(-t / 0.006)))
    return bp(x, 4200, 9000, 2) * rng.uniform(0.45, 0.75)

def tamb(rng):
    n = int(0.11 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.05)
    jing = 0.4 * np.sign(np.sin(2 * np.pi * 9500 * t)).astype(np.float32) * np.exp(-t / 0.04)
    return hp((x + jing), 6500, 2) * 0.3

# ---- percusión DRUM-LINE (la firma de Brunello)
def conga(f0, rng, slap=False):
    """conga/bongo afinado con caída de pitch + golpe de piel (o slap)."""
    n = int((0.10 if slap else 0.16) * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.55 * np.exp(-t / 0.012))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.04 if slap else 0.08))
    tk = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.005) * (0.7 if slap else 0.45)
    return sat((tone.astype(np.float32) + bp(tk, 1200, 5000, 2)) * 0.7, 1.2, 0.05)

def tom(f0, rng):
    """tom/rototom afinado (redoble de batería de marcha)."""
    n = int(0.24 * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.4 * np.exp(-t / 0.02))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.10)
    tk = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.004) * 0.3
    return sat((x.astype(np.float32) + tk) * 0.7, 1.2, 0.05)

def snare_drumline(rng, dur=0.11):
    """caja de drum-line: cuerpo + bordonera brillante (para flams y redobles)."""
    n = int(dur * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 220 * t) * np.exp(-t / 0.03)
    nz = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.05)
    return sat((body * 0.4 + bp(nz, 1800, 8500, 2) * 0.9).astype(np.float32) * 0.55, 1.25, 0.07)

def rimshot(rng):
    n = int(0.05 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * rng.uniform(1500, 1750) * t) * np.exp(-t / 0.007)
    return bp(x.astype(np.float32), 1000, 4200, 2) * 0.5

def clave(rng):
    n = int(0.06 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 2200 * t) * np.exp(-t / 0.012)
    return sat(x.astype(np.float32), 1.2, 0.05) * 0.45

def ride(rng):
    n = int(0.5 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32)
    for fq in (5200, 7100, 9300):
        x += 0.3 * np.sin(2 * np.pi * fq * t).astype(np.float32)
    return hp(x * np.exp(-t / 0.28), 5000, 2) * 0.16

# ==================================================================== EL BAJO (LIMPIO)
def bass_disco(f, dur, rng, cutoff=520, glide_from=None):
    """bajo cosmic-disco CÁLIDO y LIMPIO: sine sub + triángulo + un pelín de saw,
    por LP suave SIN resonancia, sin drive agresivo. Redondo, rueda en el pocket."""
    n = max(8, int(dur * SR)); t = np.arange(n) / SR
    if glide_from:
        fr = glide_from + (f - glide_from) * np.minimum(1.0, t / 0.05)
        ph = 2 * np.pi * np.cumsum(fr) / SR
    else:
        ph = 2 * np.pi * f * t
    sine = np.sin(ph).astype(np.float32)
    tri = _tri(ph)
    saw = (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    x = sine * 0.82 + tri * 0.34 + saw * 0.14                # dominan sine+tri = cálido
    env = np.minimum(1.0, t / 0.008) * np.exp(-np.maximum(0.0, t - dur * 0.7) / 0.07)
    x = lp(x * env.astype(np.float32), cutoff, 2)            # LP suave, sin pico
    return sat_warm(x) * 0.62                                # sat_warm = calorcito suave, no grit

# ==================================================================== SYNTHS CÓSMICOS
def arp_synth(f, dur, rng):
    """voz de arpegio: 2 saws detune por LP resonante MODERADO — el gesto space-disco.
    Corto/plucky; el delay punteado (en el arreglo) hace el resto."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for det in (-7, 7):
        ph = 2 * np.pi * f * 2 ** (det / 1200) * t + rng.uniform(0, 6)
        x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.4
    cenv = 500 + 3200 * np.exp(-t / 0.06)                    # pluck del filtro
    seg = max(1, n // 8); out = np.zeros(n, np.float32)
    for k in range(8):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        c = float(cenv[min(n - 1, (a + b_) // 2)])
        out[a:b_] = lp(x[a:b_], c, 2) * 0.5 + bp(x[a:b_], c * 0.8, c * 1.25, 2) * 0.6
    env = np.minimum(1.0, t / 0.004) * np.exp(-t / 0.10)
    return sat(out * env.astype(np.float32) * 0.5, 1.2, 0.06)

def lead_analog(f, dur, rng, glide_from=None):
    """lead análogo cósmico (Bodzin-ish): 3 saws detune por filtro que abre, vibrato."""
    n = int(dur * SR); t = np.arange(n) / SR
    if glide_from:
        fr = glide_from + (f - glide_from) * np.minimum(1.0, t / 0.07)
    else:
        fr = f * np.ones(n, np.float32)
    vib = 2.0 ** (5.0 * np.sin(2 * np.pi * 4.8 * t + rng.uniform(0, 6)) / 1200)
    x = np.zeros(n, np.float32)
    for det in (-8, 0, 9):
        ph = 2 * np.pi * np.cumsum(fr * vib * 2 ** (det / 1200)) / SR + rng.uniform(0, 6)
        x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.32
    # filtro que abre en el ataque (wow)
    cenv = 600 + 3400 * np.minimum(1.0, t / (dur * 0.4))
    seg = max(1, n // 8); out = np.zeros(n, np.float32)
    for k in range(8):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        out[a:b_] = lp(x[a:b_], float(cenv[min(n - 1, (a + b_) // 2)]), 2)
    env = np.minimum(1.0, t / 0.02) * np.exp(-np.maximum(0.0, t - dur * 0.8) / 0.18)
    return sat(out * env.astype(np.float32) * 0.42, 1.2, 0.06)

def pad_cosmic(ms, dur, rng, cut=1500):
    """pad cósmico ancho: saws desafinados muy filtrados, evoluciona."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for m in ms:
        f = midi_f(m)
        for det in (-11, -4, 4, 11):
            ph = 2 * np.pi * f * 2 ** (det / 1200) * t + rng.uniform(0, 6)
            x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.10
    lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.08 * t + rng.uniform(0, 6))
    env = np.minimum(1.0, t / 1.1) * np.minimum(1.0, np.maximum(0.0, dur - t) / 1.2)
    return lp(x * (env * lfo).astype(np.float32), cut, 2) * 0.44

def bell_fm(f, dur, rng):
    """campana FM glassy (brillo retro-futuro)."""
    n = int(dur * SR); t = np.arange(n) / SR
    mod = np.sin(2 * np.pi * f * 2.01 * t) * 3.5 * np.exp(-t / 0.3)
    x = np.sin(2 * np.pi * f * t + mod).astype(np.float32)
    env = np.exp(-t / (dur * 0.4))
    return (x * env.astype(np.float32)) * 0.34

def laser(rng, up=False):
    """láser sci-fi: barrido de pitch resonante."""
    n = int(0.3 * SR); t = np.arange(n) / SR; prog = t / (n / SR)
    f = (150 + 2600 * prog) if up else (2800 - 2600 * prog)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    return sat(bp(x * np.exp(-t / 0.10), 400, 6000, 2), 1.3, 0.08) * 0.34

def vox_robot(f, dur, rng, vow='o'):
    """voz VOCODER/robótica sci-fi (fragmento, textura)."""
    F = dict(a=((760, 1.0), (1220, 0.5)), o=((520, 1.0), (920, 0.5)),
             e=((540, 1.0), (1900, 0.4)), u=((360, 1.0), (900, 0.4)))[vow]
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * f * t
    saw = (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    env = np.minimum(1.0, t / 0.01) * np.exp(-np.maximum(0.0, t - dur * 0.5) / 0.07)
    saw *= env.astype(np.float32)
    out = sum(bp(saw, fq * 0.9, fq * 1.1, 2) * g for fq, g in F)
    ring = np.sin(2 * np.pi * (f * 0.5) * t)
    return sat((out * (0.72 + 0.28 * ring)).astype(np.float32) * 0.5, 1.25, 0.08)

def vox_ether(f, dur, rng, vow='a'):
    """voz etérea/aireada (colchón misterioso del breakdown)."""
    F = dict(a=((760, 1.0), (1220, 0.5), (2600, 0.2)), o=((520, 1.0), (900, 0.5), (2500, 0.2)),
             u=((360, 1.0), (900, 0.4), (2400, 0.15)))[vow]
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * f * (t + 0.003 * np.sin(2 * np.pi * 4.6 * t + rng.uniform(0, 6)))
    src = np.zeros(n, np.float32)
    for h in range(1, 22):
        src += (np.sin(h * ph) / h ** 1.15).astype(np.float32)
    env = np.minimum(1.0, t / 0.1) * np.minimum(1.0, np.maximum(0.0, dur - t) / 0.5)
    src *= env.astype(np.float32)
    out = sum(bp(src, fq * 0.87, fq * 1.15, 2) * g for fq, g in F)
    return sat(out * 0.5, 1.15, 0.05)

# ==================================================================== FX
def riser(dur, rng):
    n = int(dur * SR); t = np.arange(n) / SR; prog = t / (n / SR)
    nz = rng.standard_normal(n).astype(np.float32)
    out = np.zeros(n, np.float32); seg = max(1, n // 28)
    for k in range(28):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        p = float(prog[min(n - 1, (a + b_) // 2)])
        out[a:b_] = bp(nz[a:b_], 300 + 5000 * p ** 2, 700 + 9000 * p ** 2, 2)
    return (out * (prog ** 1.6)).astype(np.float32) * 0.38

def downlift(rng):
    n = int(0.7 * SR); t = np.arange(n) / SR; prog = t / (n / SR)
    f = 1000 * (1 - prog) + 60
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    return sat(bp(x * np.exp(-t / 0.32), 150, 4500, 2), 1.25, 0.08) * 0.38

def impact(rng):
    n = int(1.4 * SR); t = np.arange(n) / SR
    f = 44 + 80 * np.exp(-t / 0.05)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.5)
    nz = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.55)
    return (sat(boom.astype(np.float32), 1.25, 0.05) + bp(nz, 200, 3600, 2) * 0.4) * 0.58

def revswell(dur, rng):
    n = int(dur * SR); t = np.arange(n) / SR; prog = t / (n / SR)
    x = hp(rng.standard_normal(n).astype(np.float32), 4000, 2)
    return (x * (prog ** 2.3)).astype(np.float32) * 0.28

if __name__ == '__main__':
    from dream_core import wav_write, spectrum_pct
    rng = np.random.default_rng(9)
    bpm = 127; spb = int(SR * 240 / bpm); s16 = spb / 16
    n = spb * 2; mix = np.zeros(n, np.float32)
    def put(buf, pos, x, g=1.0):
        pos = int(pos); e = min(len(buf), pos + len(x))
        if e > pos: buf[pos:e] += x[:e - pos] * g
    K = kick_disco(); SW = 0.56
    for bar in range(2):
        base = bar * spb
        for b in range(4): put(mix, base + b * 4 * s16, K)
        put(mix, base + 4 * s16, clap(rng), 0.7); put(mix, base + 12 * s16, clap(rng), 0.7)
        for s in range(16):
            sw = base + s * s16 + ((SW - 0.5) * 2 * s16 if s % 2 else 0)
            put(mix, sw, hat(rng, open_=(s % 4 == 2)), 0.4 if s % 2 else 0.26)
        for s in (2, 6, 10, 14): put(mix, base + s * s16, shaker(rng), 0.3)
        # drum-line: congas + un flam de tom en el 2do compás
        for s in (3, 7, 11, 14): put(mix, base + s * s16, conga(midi_f(50 if s % 3 else 57), rng, slap=(s % 2==1)), 0.4)
        if bar == 1:
            for k, s in enumerate((12, 13, 14, 15)): put(mix, base + s * s16, tom(180 - 26 * k, rng), 0.4)
        # bajo LIMPIO octava-bounce (Re)
        for st, m in [(0, 38), (4, 50), (6, 38), (8, 38), (12, 50), (14, 38)]:
            put(mix, base + st * s16, bass_disco(midi_f(m - 12), 1.4 * s16 / SR, rng), 0.9)
    # arpegio + lead cósmico
    for k in range(8):
        put(mix, int(k * 2 * s16), arp_synth(midi_f(pdeg(62, k % 5, 1)), 0.16, rng), 0.4)
    put(mix, 0, lead_analog(midi_f(62), 0.9, rng), 0.4)
    put(mix, spb + 8 * s16, laser(rng), 0.6)
    mix /= max(1e-9, np.abs(mix).max())
    wav_write('_test_brunello.wav', np.stack([mix, mix]))
    print('BRUNELLO groove:', {k: round(v, 1) for k, v in spectrum_pct(mix).items()})
    print('_test_brunello.wav listo')
