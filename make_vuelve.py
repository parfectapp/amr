#!/usr/bin/env python3
"""VUELVE — AMR SINGLE 002 (~4:10, 120 BPM, La menor). Soul afro house estilo
Black Coffee "You Need Me": VOZ DE MUJER original al centro, piano eléctrico
en comping soul, sub redondo de una nota por compás, percusión suave.
Arreglo desde CERO — nada de forks. Paleta propia en vuelve_voices.py."""
import os
import numpy as np
from dream_core import (SR, lp, hp, bp, sat, widen, sub_mono, pingpong,
                        master_file, ffmeter, wav_write, fconv)
import vuelve_voices as W
from vuelve_voices import midi_f

HERE = os.path.dirname(os.path.abspath(__file__))
BPM = 120.0
SPB = int(round(SR * 240.0 / BPM)); S16 = SPB / 16.0; BEAT_S = 0.5

# Am9 – Fmaj7 – Cmaj7 – G6, dos compases cada uno (el ciclo soul)
CHORDS = [[45, 52, 60, 64], [41, 48, 57, 64], [48, 55, 64, 67], [43, 50, 59, 64]]
TOPS   = [71, 69, 67, 66]                      # la nota de color del epiano

# ---- melodías ORIGINALES (vocalise, no letra) ----
ADLIB = [(69, 2.0, 'o'), (None, 1.0, 'o'), (67, 1.5, 'u'), (64, 3.5, 'o')]
VERSA = [(64, 1.0, 'o'), (67, 1.0, 'o'), (69, 1.5, 'a'), (None, 0.5, 'a'),
         (69, 1.0, 'e'), (71, 1.0, 'e'), (69, 2.0, 'o'), (None, 1.0, 'o'),
         (67, 1.0, 'u'), (69, 1.0, 'e'), (67, 1.5, 'a'), (64, 2.5, 'o'), (None, 1.0, 'o')]
HOOK  = [(72, 1.5, 'o'), (74, 0.5, 'o'), (72, 1.0, 'e'), (69, 1.5, 'a'), (None, 0.5, 'a'),
         (67, 1.0, 'u'), (69, 1.0, 'e'), (72, 2.0, 'o'), (None, 0.5, 'o'),
         (71, 1.0, 'e'), (69, 1.0, 'a'), (67, 1.5, 'o'), (64, 3.0, 'o')]
VERSB = [(72, 1.0, 'e'), (71, 1.0, 'e'), (69, 1.5, 'o'), (None, 0.5, 'o'),
         (67, 1.0, 'a'), (69, 1.0, 'a'), (71, 2.0, 'e'), (None, 1.0, 'e'),
         (69, 1.0, 'o'), (67, 1.0, 'u'), (64, 2.5, 'o'), (None, 1.5, 'o')]

SONG = [('intro', 12), ('versa', 16), ('lift', 8), ('hook', 16),
        ('versb', 16), ('hook2', 16), ('break', 8), ('hook3', 20), ('outro', 12)]

KICK = W.kick_soul()

def add(buf, pos, x, g=1.0):
    pos = int(pos)
    if pos < 0: x = x[-pos:]; pos = 0
    end = min(len(buf), pos + len(x))
    if end > pos: buf[pos:end] += x[:end - pos] * g

def build():
    rng = np.random.default_rng(21)
    total = sum(b for _, b in SONG) * SPB + 5 * SPB
    kickb = np.zeros(total, np.float32); bassb = np.zeros(total, np.float32)
    percb = np.zeros(total, np.float32); keysb = np.zeros(total, np.float32)
    vozb = np.zeros(total, np.float32); corb = np.zeros(total, np.float32)
    padL = np.zeros(total, np.float32); padR = np.zeros(total, np.float32)
    kpos = []
    sw = lambda s: s * S16 + 0.05 * 2 * S16 * (s % 2)      # swing suave 0.55

    pos_bar = 0
    for name, bars in SONG:
        for bar in range(bars):
            gb = pos_bar + bar
            base = gb * SPB
            ci = (gb // 2) % 4
            ch = CHORDS[ci]
            full = name in ('hook', 'hook2', 'hook3', 'lift', 'versb', 'outro')
            # KICK: medio tiempo en el verso A, 4x4 desde el lift (menos el break)
            if name == 'versa':
                for beat in (0, 2):
                    add(kickb, base + beat * 4 * S16, KICK, 0.8); kpos.append(int(base + beat * 4 * S16))
            elif full:
                for beat in range(4):
                    add(kickb, base + beat * 4 * S16, KICK, 0.95); kpos.append(int(base + beat * 4 * S16))
            # BAJO: UNA nota redonda por compás en el 1, con pickup en el 4& a veces
            if name not in ('intro', 'break'):
                fr = midi_f(ch[0] - 12)
                add(bassb, base, W.bass_soul(fr, BEAT_S * 3.4, rng), 0.95)
                if bar % 2 == 1 and rng.uniform() < 0.7:
                    add(bassb, base + int(14 * S16), W.bass_soul(fr * (1.5 if ci % 2 else 1.0), BEAT_S * 0.9, rng), 0.55)
            # EPIANO: comping soul — roll en el 1 y en el "y" del 3
            if name != 'break' or bar < 2:
                for st, g in ((0, 0.42), (10, 0.3)):
                    if st == 10 and not full: continue
                    for k, m in enumerate(ch[1:] + [TOPS[ci]]):
                        add(keysb, base + int(sw(st) + k * 0.028 * SR), W.epiano(midi_f(m), 1.5, rng), g * (0.85 ** k))
            # PERCUSIÓN suave: shaker 8vos, rim cruzado en el 3, conga escasa, hats
            if name not in ('intro',):
                for st in range(0, 16, 2):
                    add(percb, base + int(sw(st) + rng.normal(0, .003) * SR), W.shaker_brush(rng), 0.5 * (1.0 if st % 4 == 2 else 0.6))
                add(percb, base + int(8 * S16), W.rim_warm(rng), 0.55)          # cross-stick en el 3
                if full:
                    for st in (3, 11):
                        if rng.uniform() < 0.7:
                            add(percb, base + int(sw(st) + rng.normal(0, .004) * SR), W.conga_soft(rng, open_=(st == 11)), 0.4)
                    for st in (2, 6, 10, 14):
                        add(percb, base + int(sw(st)), W.hat_gentle(rng), 0.45)
                    if bar % 2 == 1:
                        add(percb, base + int(sw(6)), W.hat_gentle(rng, open_=True), 0.4)
            # PADS de vidrio bajo los hooks y el break
            if name in ('hook', 'hook2', 'hook3', 'break', 'lift') and bar % 2 == 0:
                for m in ch[1:3]:
                    x = W.pad_glass(midi_f(m + 12), 2 * SPB / SR * 1.05, rng)
                    add(padL, base, x, 0.7); add(padR, base + int(0.014 * SR), x, 0.65)
        pos_bar += bars

    # ---- LA VOZ (por frases, sobre la rejilla de compases) ----
    def put_voice(bar0, notes, coro=False, gain=1.0, breath=0.09):
        v = W.sing(notes, np.random.default_rng(rng.integers(1 << 30)), gain=gain, breath=breath)
        add(vozb, bar0 * SPB, v, 1.0)
        if coro:
            h = W.coros(notes, rng, semis=(4, 7), gain=0.4)
            add(corb, bar0 * SPB + int(0.02 * SR), h, 1.0)
    b0 = 0
    for name, bars in SONG:
        if name == 'intro':
            put_voice(b0 + 4, ADLIB, gain=0.85, breath=0.14)
            put_voice(b0 + 9, [(64, 1.5, 'u'), (67, 2.5, 'o')], gain=0.7, breath=0.16)
        elif name == 'versa':
            put_voice(b0, VERSA); put_voice(b0 + 8, VERSA, gain=0.95)
        elif name == 'lift':
            put_voice(b0 + 2, [(69, 1.5, 'e'), (71, 1.0, 'e'), (72, 3.0, 'o'), (None, 1, 'o'), (74, 2.0, 'a'), (72, 3.0, 'o')], gain=0.95)
        elif name == 'hook':
            put_voice(b0, HOOK); put_voice(b0 + 8, HOOK)
        elif name == 'versb':
            put_voice(b0, VERSB); put_voice(b0 + 8, VERSB, gain=0.9)
        elif name == 'hook2':
            put_voice(b0, HOOK, coro=True); put_voice(b0 + 8, HOOK, coro=True)
        elif name == 'break':
            put_voice(b0 + 1, HOOK, gain=0.95, breath=0.16)
        elif name == 'hook3':
            put_voice(b0, HOOK, coro=True)
            put_voice(b0 + 8, [(n + 12 if n else None, b, v) for n, b, v in HOOK[:5]] + HOOK[5:], coro=True)
            put_voice(b0 + 16, ADLIB, gain=0.8, breath=0.13)
        elif name == 'outro':
            put_voice(b0 + 2, [(69, 2.0, 'o'), (None, 0.5, 'o'), (67, 1.5, 'u'), (64, 4.0, 'o')], gain=0.75, breath=0.15)
        b0 += bars

    # ---- mezcla ----
    from make_hechizo import sidechain_env, _verb_ir
    env = sidechain_env(total, kpos, depth=0.3, rel_s=0.1)
    bassb *= env
    keys_st = widen(keysb * (env * 0.5 + 0.5), amount=0.5, seed=7)
    perc_st = widen(percb, amount=0.6, seed=3)
    voz_st = np.stack([vozb, vozb])
    vverb = np.stack([fconv(vozb, _verb_ir(1.9, 5200, 41)), fconv(vozb, _verb_ir(1.9, 5200, 42))])
    cor_st = pingpong(corb, BEAT_S, fb=0.35, mix=0.4, taps=5, damp=4600)
    pads = np.stack([padL, padR]) * (env * 0.5 + 0.5)[None, :]
    music = keys_st * 0.75 + perc_st * 0.6 + voz_st * 0.95 + vverb * 0.4 + cor_st * 0.6 + pads * 0.8
    mm = 0.5 * (music[0] + music[1]); ss = bp(0.5 * (music[0] - music[1]), 250, 10000, 2) * 2.0
    mix = np.stack([mm + ss, mm - ss])
    mix += kickb[None, :] * 1.1 + bassb[None, :] * 1.3
    mix = np.stack([sat(mix[0], 1.1, 0.04), sat(mix[1], 1.1, 0.04)])
    mix = sub_mono(mix, 120.0)
    pk = np.abs(mix).max()
    if pk > 0.9: mix *= 0.9 / pk
    return mix

if __name__ == '__main__':
    tb = sum(b for _, b in SONG)
    print(f'VUELVE · {tb} compases ≈ {tb * SPB / SR / 60:.1f} min', flush=True)
    mix = build()
    raw = os.path.join(HERE, 'masters', 'vuelve-raw.wav')
    final = os.path.join(HERE, 'masters', 'amr-vuelve.wav')
    wav_write(raw, mix); del mix
    hist = master_file(raw, final, target_i=-9.5, ceiling_db=-1.2)
    I, lra, tp = ffmeter(final)
    print(f'MASTER: {hist} → {I} LUFS · LRA {lra} · TP {tp}')
    print(final)
