#!/usr/bin/env python3
"""BLOOM — banger melódico house. Motor limpio (el de las rolas/VESSEL/TULUM):
arpegio brillante con pingpong + topline emotivo (el gancho) + groove que empuja.
Sin percusión turbia, sin subgraves raros."""
import os, json, subprocess, wave
import numpy as np, imageio_ffmpeg
import make_tracks as mt

SR = mt.SR; rng = mt.rng
HERE = os.path.dirname(os.path.abspath(__file__))
place, reverb, fbdelay, riser, duck_env = mt.place, mt.reverb, mt.fbdelay, mt.riser, mt.duck_env
mk_pad, mk_pluck, mk_bass, mk_stab, mk_kick, mk_hat = mt.mk_pad, mt.mk_pluck, mt.mk_bass, mt.mk_stab, mt.mk_kick, mt.mk_hat
lowpass, highpass = mt.lowpass, mt.highpass
def stereo(y, pan=1.0): return np.vstack([y * pan, y * (2 - pan)])

def clap(amp=0.22):
    n = int(0.18 * SR); t = np.arange(n) / SR
    x = highpass(rng.standard_normal(n), 1300)
    env = np.zeros(n)
    for d in (0.0, 0.008, 0.016):
        i = int(d * SR); env[i:] += np.exp(-np.arange(n - i) / SR / 0.012)
    env += np.exp(-t / 0.11) * 0.5
    y = x * env; y /= np.max(np.abs(y)) + 1e-9
    return stereo(y * amp)

def saw_lead(f, dur, amp=0.13, K=13):
    """topline anthem: supersaw suave (3 voces detune), filtro cálido."""
    n = int(dur * SR); t = np.arange(n) / SR
    def one(fr):
        ph = 2 * np.pi * fr * t; s = np.zeros(n)
        for k in range(1, K + 1): s += np.sin(k * ph) / k
        return s
    y = one(f) + 0.7 * one(f * 1.004) + 0.7 * one(f * 0.996)
    y = lowpass(y, 3400)
    env = np.ones(n); a = int(0.02 * SR); r = int(min(0.22 * SR, n // 3))
    env[:a] = np.linspace(0, 1, a); env[-r:] *= np.linspace(1, 0, r)
    return np.vstack([y, y]) * env * amp / 2.4

# Am – F – C – G (i–VI–III–VII): eufórico y catchy
ARP = [
    [440, 523.25, 659.25, 783.99, 880, 783.99, 659.25, 523.25],       # Am
    [349.23, 440, 523.25, 659.25, 698.46, 659.25, 523.25, 440],       # F
    [523.25, 659.25, 783.99, 880, 1046.5, 880, 783.99, 659.25],       # C
    [392, 493.88, 587.33, 698.46, 783.99, 698.46, 587.33, 493.88],    # G
]
STAB = [[220, 261.63, 329.63, 392], [174.61, 220, 261.63, 349.23],
        [196, 261.63, 329.63, 392], [196, 246.94, 293.66, 392]]
PAD = [[110, 220, 261.63, 329.63], [87.31, 174.61, 261.63, 349.23],
       [98, 196, 261.63, 329.63], [98, 196, 293.66, 392]]
BASS = [55.0, 43.65, 65.41, 49.0]
def idx(bar): return (bar // 4) % 4
def rng_in(bar, spans): return any(a <= bar < b for a, b in spans)

# topline: el gancho que se canta (8 compases)
TOP = [(0, 0, 659.25, 2), (0, 8, 523.25, 2), (1, 0, 587.33, 2), (1, 8, 440.0, 2),
       (2, 0, 659.25, 2), (2, 8, 783.99, 2), (3, 0, 587.33, 4),
       (4, 0, 880.0, 2), (4, 8, 659.25, 2), (5, 0, 523.25, 4),
       (6, 0, 659.25, 2), (6, 8, 783.99, 2), (7, 0, 493.88, 2), (7, 8, 587.33, 2)]

def build():
    s = mt.Song(124, 112, swing=0.08)
    beat = s.beat
    DROPS = [(16, 40), (64, 96)]
    KICK_ON = [(8, 40), (56, 96), (104, 110)]

    # kick + hats + clap
    kick_s = mk_kick(f0=140, f1=47, amp=0.6, dur=0.36)
    ho, hc = mk_hat(True), mk_hat(False)
    drums = np.zeros((2, s.N))
    for bar in range(s.bars):
        kon = rng_in(bar, KICK_ON)
        if kon:
            for st in [0, 4, 8, 12]:
                place(drums, kick_s, s.t(bar, st)); s.kick_times.append(s.t(bar, st))
        if rng_in(bar, DROPS) or rng_in(bar, [(8, 16), (56, 64)]):
            for st in range(16):
                if st % 2:  # hats offbeat
                    h = ho if st % 4 == 3 else hc
                    place(drums, stereo(h, 0.92 if (st // 2) % 2 else 1.08) * 0.7, s.t(bar, st))
        if rng_in(bar, DROPS):
            for st in [4, 12]: place(drums, clap(0.2), s.t(bar, st))
    s.add(drums)
    duck = duck_env(s.N, s.kick_times, depth=0.5, rec=0.34)

    # bajo rodante limpio (offbeats)
    bc = {}
    bass = np.zeros((2, s.N))
    for bar in range(s.bars):
        if not rng_in(bar, KICK_ON): continue
        f = BASS[idx(bar)]
        if f not in bc: bc[f] = mk_bass(f, dur=0.32, amp=0.35)
        for st in [2, 6, 10, 14]:
            place(bass, bc[f], s.t(bar, st))
    s.add(bass * duck)

    # pad cálido
    pads = np.zeros((2, s.N))
    for blk in range(0, s.bars, 4):
        seg = mk_pad(PAD[idx(blk)], 4 * 4 * int(beat * SR) + SR, lfo_hz=0.06, dark=420, bright=1500, amp=0.062)
        place(pads, seg, s.t(blk))
    s.add(pads * duck, [(0, 0.5), (16, 0.85), (40, 1.25), (56, 0.9),
                        (64, 1.15), (96, 0.95), (112, 0.4)])

    # stabs de acorde (groove) en los drops
    stabs = np.zeros((2, s.N))
    for bar in range(s.bars):
        if not rng_in(bar, DROPS): continue
        st_s = mk_stab(STAB[idx(bar)], dur=0.34, bp=1100, q=1.1, amp=0.14)
        for st in [2, 10, 14]: place(stabs, st_s, s.t(bar, st))
    stabs = stabs + fbdelay(stabs, beat * 0.75, fb=0.34, damp=2400) * 0.4
    s.add(stabs)

    # ARPEGIO brillante = el gancho (8vos up-down con pingpong)
    ARP_ON = [(16, 40), (40, 56), (64, 96)]
    arp = np.zeros((2, s.N))
    for bar in range(s.bars):
        if not rng_in(bar, ARP_ON): continue
        soft = 0.55 if rng_in(bar, [(40, 56)]) else 1.0
        seq = ARP[idx(bar)]
        for i, st in enumerate([0, 2, 4, 6, 8, 10, 12, 14]):
            pan = 0.9 if i % 2 else 1.1
            place(arp, stereo(mk_pluck(seq[i], dur=0.42, amp=0.15 * soft, bright=2600).mean(0), pan), s.t(bar, st))
    arp = arp + fbdelay(arp, beat * 0.75, fb=0.4, damp=2800) * 0.5
    s.add(arp + reverb(arp, 1.1, damp=3000, mix=0.22))

    # TOPLINE emotivo (el que se canta) — break + drop 2
    top = np.zeros((2, s.N))
    def lay(sb, amp):
        for pb, st, f, bts in TOP:
            place(top, saw_lead(f, bts * beat * 0.98, amp=amp), s.t(sb + pb, st))
    lay(40, 0.10)          # breakdown, suave
    lay(72, 0.14)          # drop 2, presente (el gancho)
    top = top + fbdelay(top, beat * 0.5, fb=0.3, damp=3000) * 0.3
    s.add(top + reverb(top, 1.5, damp=2800, mix=0.32))

    # risers hacia cada drop
    place(s.mix, riser(beat * 8, s.N, f0=300, f1=6000, amp=0.06), s.t(8))
    place(s.mix, riser(beat * 8, s.N, f0=300, f1=7000, amp=0.07), s.t(56))
    return mt.master(s, 'amr-bloom')

if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'masters'), exist_ok=True)
    os.makedirs(os.path.join(HERE, 'audio'), exist_ok=True)
    print('Sintetizando BLOOM (banger melódico)…', flush=True)
    wav, dur, peaks = build()
    print(f'  WAV: {wav}  ({dur:.1f}s)', flush=True)
    FF = imageio_ffmpeg.get_ffmpeg_exe()
    m4a = os.path.join(HERE, 'audio', 'amr-bloom.m4a')
    subprocess.run([FF, '-y', '-v', 'error', '-i', wav, '-c:a', 'aac', '-b:a', '192k',
                    '-movflags', '+faststart', m4a], check=True)
    print(f'  M4A: {m4a}', flush=True)
    meta = dict(id='amr-bloom', title='BLOOM', kicker='THE SINGLE', tracks=1,
                dur=round(dur, 1), titles=['BLOOM'], file='audio/amr-bloom.m4a',
                art='art/amr-bloom.svg', edition=30, peaks=peaks, offsets=[0.0], bpm=124, key='A MIN')
    with open(os.path.join(HERE, 'bloom.js'), 'w') as f:
        f.write('window.AMR_BLOOM=' + json.dumps(meta) + ';')
    print('  bloom.js escrito. done', flush=True)
