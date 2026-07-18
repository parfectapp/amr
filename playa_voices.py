#!/usr/bin/env python3
"""PLAYA — paleta Maccabi House / Burning Man (Adam Ten en la playa).
Funk-first: bajo CHICLOSO con slides, chops de guitarra muteada, clavinet,
stabs de metales retro, lead wah/talkbox, vocales juguetonas, viento de polvo.
NADA compartido con otros discos — paleta propia."""
import numpy as np
from dream_core import SR, lp, hp, bp, sat, sat_warm

def midi_f(m): return 440.0 * 2.0 ** ((m - 69) / 12.0)

MINP = [0, 3, 5, 7, 10]                       # pentatónica menor (los ganchos)
def pdeg(root, d, o=0): return root + MINP[d % 5] + 12 * (d // 5 + o)

# ---------------------------------------------------------------- batería
def kick_punch():
    """kick apretado y con pegada — corto, no boomy (el groove manda)."""
    n = int(0.30 * SR); t = np.arange(n) / SR
    f = 50.0 + 68.0 * np.exp(-t / 0.016)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.115)
    x += 0.5 * np.exp(-t / 0.004) * np.sin(2 * np.pi * 1300 * t) * np.exp(-t / 0.006)
    return lp(sat(x.astype(np.float32), 1.35, 0.05), 3200, 2) * 0.85

def snare_fat(rng):
    """backbeat gordo: cuerpo 185Hz + rafaga de ruido."""
    n = int(0.22 * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.045)
    nz = rng.standard_normal(n).astype(np.float32) * np.exp(-t / 0.075)
    x = body * 0.7 + bp(nz, 900, 7500, 2) * 0.9
    return sat(x.astype(np.float32) * 0.7, 1.3, 0.07)

def hat_funk(rng, open_=False):
    dec = (0.19 if open_ else 0.028) * rng.uniform(0.9, 1.1)
    n = int(dec * 6 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32)
    x += 0.3 * np.sign(np.sin(2 * np.pi * 6900 * t)).astype(np.float32)
    x *= np.exp(-t / dec)
    return hp(x, 7600, 2) * (0.3 if open_ else 0.4) * rng.uniform(0.85, 1.0)

def shk(rng):
    n = int(0.06 * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32) * (np.exp(-t / 0.03) * (1 - np.exp(-t / 0.007)))
    return bp(x, 3600, 8200, 2) * rng.uniform(0.55, 0.85)

def cowb(rng):
    """cencerro seco — el guiño Maccabi."""
    n = int(0.09 * SR); t = np.arange(n) / SR
    x = (np.sign(np.sin(2 * np.pi * 545 * t)) * 0.6 + np.sign(np.sin(2 * np.pi * 815 * t)) * 0.4)
    x = x.astype(np.float32) * np.exp(-t / 0.032)
    return bp(x, 480, 3200, 2) * 0.5

def block(rng):
    n = int(0.05 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * rng.uniform(880, 980) * t) * np.exp(-t / 0.009)
    return sat(x.astype(np.float32), 1.3, 0.05) * 0.55

def tom(f0, rng):
    n = int(0.3 * SR); t = np.arange(n) / SR
    f = f0 * (1 + 0.35 * np.exp(-t / 0.02))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)
    return sat(x.astype(np.float32) * 0.7, 1.25, 0.06)

# ---------------------------------------------------------------- el BAJO (la estrella)
def bass_rub(f, dur, rng, cutoff=750, glide_from=None):
    """bajo CHICLOSO: saw+square+sub por lowpass con envolvente — y slide opcional."""
    n = max(8, int(dur * SR)); t = np.arange(n) / SR
    if glide_from:
        fr = glide_from + (f - glide_from) * np.minimum(1.0, t / 0.05)
        ph = 2 * np.pi * np.cumsum(fr) / SR
    else:
        ph = 2 * np.pi * f * t
    saw = 2 * ((ph / (2 * np.pi)) % 1.0) - 1
    sq = np.sign(np.sin(ph * 0.5 + 0.4))
    sub = np.sin(ph * 0.5)
    x = (saw * 0.55 + sq * 0.2 + sub * 0.6).astype(np.float32)
    env = np.minimum(1.0, t / 0.006) * np.exp(-np.maximum(0.0, t - dur * 0.62) / 0.05)
    x = lp(x * env.astype(np.float32), cutoff, 2)
    x = lp(x, cutoff * 1.6, 2)                      # 4-polo suave
    return sat_warm(x) * 0.8

# ---------------------------------------------------------------- armonía funk
def gtr_chop(f, rng, dur=0.09):
    """chop de guitarra funk MUTEADA (Karplus-Strong ahogado) — el skank."""
    n = int(dur * SR)
    per = max(2, int(SR / f))
    buf = rng.uniform(-1, 1, per).astype(np.float32)
    out = np.empty(n, np.float32)
    damp = 0.86                                      # muteo fuerte = chuck
    for i in range(n):
        out[i] = buf[i % per]
        buf[i % per] = damp * 0.5 * (buf[i % per] + buf[(i + 1) % per])
    env = np.exp(-np.arange(n) / (0.03 * SR)).astype(np.float32)
    return bp(out * env, 420, 3100, 2) * 0.8

def clav(f, rng, dur=0.16):
    """clavinet: KS brillante con mordida — responde al bajo."""
    n = int(dur * SR)
    per = max(2, int(SR / f))
    buf = np.sign(rng.uniform(-1, 1, per)).astype(np.float32)   # excitación cuadrada = bite
    out = np.empty(n, np.float32)
    for i in range(n):
        out[i] = buf[i % per]
        buf[i % per] = 0.965 * 0.5 * (buf[i % per] + buf[(i + 1) % per])
    env = np.exp(-np.arange(n) / (0.07 * SR)).astype(np.float32)
    x = out * env
    x = x + 0.5 * bp(x, f * 3.6, f * 5.2, 2)         # formante nasal clavinet
    return sat(x, 1.3, 0.1) * 0.5

def brass(ms, dur, rng):
    """stab de metales retro: saws desafinados en acorde, ataque rápido — ¡bwap!"""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for m in ms:
        f = midi_f(m)
        for det in (-9, 0, 8):
            fv = f * 2 ** (det / 1200)
            ph = 2 * np.pi * fv * t + rng.uniform(0, 6)
            x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.3
    env = np.minimum(1.0, t / 0.012) * np.exp(-np.maximum(0.0, t - dur * 0.5) / 0.07)
    br = np.minimum(1.0, t / 0.03)                   # brillo que abre (filtro-ataque)
    x = lp(x * env.astype(np.float32), 1400, 2) + hp(x * env.astype(np.float32), 1400, 2) * br.astype(np.float32)
    return sat(lp(x, 6800, 2) * 0.35, 1.35, 0.12)

def lead_wah(f, dur, rng):
    """lead wah/talkbox: saw por bandpass que se mueve — juguetón, medio vocal."""
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * f * (t + 0.004 * np.sin(2 * np.pi * 5.2 * t + rng.uniform(0, 6)))
    saw = (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32)
    # wah: centro del bandpass barre 500→1800→700 dentro de la nota
    swp = 500 + 1300 * np.sin(np.pi * np.minimum(1.0, t / (dur * 0.8))) ** 2
    seg = max(1, n // 6); out = np.zeros(n, np.float32)
    for k in range(6):
        a, b_ = k * seg, min(n, (k + 1) * seg)
        if a >= n: break
        c = float(swp[min(n - 1, (a + b_) // 2)])
        out[a:b_] = bp(saw[a:b_], c * 0.7, c * 1.5, 2)
    env = np.minimum(1.0, t / 0.02) * np.exp(-np.maximum(0.0, t - dur * 0.75) / 0.09)
    return sat(out * env.astype(np.float32), 1.3, 0.09) * 0.6

def vox(f, dur, rng, vow='a'):
    """chop vocal juguetón: formantes + caída de pitch al final (¡ha!)."""
    F = dict(a=((830, 1.0), (1250, 0.5), (2900, 0.25)), e=((560, 1.0), (2100, 0.4), (2900, 0.2)),
             o=((540, 1.0), (960, 0.55), (2600, 0.2)), u=((380, 1.0), (960, 0.4), (2500, 0.15)),
             i=((320, 1.0), (2450, 0.4), (3300, 0.2)))[vow]
    n = int(dur * SR); t = np.arange(n) / SR
    fall = 1.0 - 0.16 * np.maximum(0.0, (t - dur * 0.55) / (dur * 0.45))   # cae al final
    ph = 2 * np.pi * np.cumsum(f * fall) / SR
    src = np.zeros(n, np.float32)
    for h in range(1, 16):
        src += (np.sin(h * ph) / h ** 1.15).astype(np.float32)
    env = np.minimum(1.0, t / 0.02) * np.exp(-np.maximum(0.0, t - dur * 0.6) / 0.07)
    src *= env.astype(np.float32)
    out = sum(bp(src, fq * 0.86, fq * 1.16, 2) * g for fq, g in F) + src * 0.06
    return sat(out * 0.6, 1.25, 0.08)

def pad_dust(ms, dur, rng):
    """pad cálido polvoso: saws desafinados muy filtrados — el amanecer."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for m in ms:
        f = midi_f(m)
        for det in (-7, 0, 6):
            fv = f * 2 ** (det / 1200)
            ph = 2 * np.pi * fv * t + rng.uniform(0, 6)
            x += (2 * ((ph / (2 * np.pi)) % 1.0) - 1).astype(np.float32) * 0.16
    env = np.minimum(1.0, t / 1.1) * np.minimum(1.0, np.maximum(0.0, dur - t) / 1.2)
    return lp(x * env.astype(np.float32), 1500, 2) * 0.5

def wind(dur, rng):
    """viento del desierto: ruido filtrado que respira lento."""
    n = int(dur * SR); t = np.arange(n) / SR
    x = rng.standard_normal(n).astype(np.float32)
    x = bp(x, 300, 1800, 2)
    lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.06 * t + rng.uniform(0, 6))
    return (x * (0.25 + 0.75 * lfo).astype(np.float32)) * 0.06

if __name__ == '__main__':
    from dream_core import wav_write, spectrum_pct
    rng = np.random.default_rng(7)
    # banco de prueba: 2 compases del groove a 119
    spb = int(SR * 240 / 119); s16 = spb / 16
    n = spb * 2; mix = np.zeros(n, np.float32)
    def put(buf, pos, x, g=1.0):
        pos = int(pos); e = min(len(buf), pos + len(x))
        if e > pos: buf[pos:e] += x[:e - pos] * g
    K = kick_punch()
    for bar in range(2):
        base = bar * spb
        for b in range(4): put(mix, base + b * 4 * s16, K)
        put(mix, base + 4 * s16, snare_fat(rng), 0.8); put(mix, base + 12 * s16, snare_fat(rng), 0.8)
        for s in range(16): put(mix, base + s * s16, hat_funk(rng), 0.5 if s % 2 else 0.3)
        riff = [(0, 33, 2), (6, 33, 1), (8, 45, 1), (10, 33, 2), (16, 33, 1), (22, 43, 1), (24, 40, 2), (28, 45, 1)]
        for st, m, ln in riff:
            if st // 16 == bar % 2 or True:
                put(mix, base + (st % 32) * s16 if st < 16 else base, np.zeros(1, np.float32))
        for st, m, ln in [(0, 33, 2), (6, 33, 1), (8, 45, 1), (10, 33, 2)]:
            put(mix, base + st * s16, bass_rub(midi_f(m), ln * s16 / SR * 1.9, rng), 0.9)
        for s in (2, 6, 10, 14): put(mix, base + s * s16, gtr_chop(midi_f(57), rng), 0.6)
        put(mix, base + 8 * s16, clav(midi_f(45), rng), 0.7)
    put(mix, 0, brass([57, 60, 64], 0.3, rng), 0.8)
    put(mix, spb, vox(midi_f(69), 0.25, rng, 'a'), 0.7)
    mix /= max(1e-9, np.abs(mix).max())
    wav_write('_test_playa.wav', np.stack([mix, mix]))
    print('groove:', {k: round(v, 1) for k, v in spectrum_pct(mix).items()})
    print('_test_playa.wav listo')
