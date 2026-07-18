#!/usr/bin/env python3
"""FICCIÓN — single cosmic-disco / sci-fi retro-futurista (estilo Brunello "Science
Fiction"). 127 BPM, Re menor. Arpegios análogos con delay punteado (dotted-8th),
lead cósmico desafinado, pads espaciales, campanas FM, láseres y voz vocoder,
sobre un 4x4 909 cálido con percusión drum-line. Bajo LIMPIO. Máster SUAVE
(dinámico, drums sin saturar — lección de André)."""
import os
import numpy as np
from dream_core import (SR, lp, hp, bp, sat, widen, sub_mono, pingpong,
                        master_file, ffmeter, wav_write, spectrum_pct, fconv)
import brunello_voices as V
from brunello_voices import midi_f, pdeg

HERE = os.path.dirname(os.path.abspath(__file__))
TMP = os.path.join(HERE, '_ficcion_tmp'); os.makedirs(TMP, exist_ok=True)
BPM = 127.0
SPB = int(round(SR * 240.0 / BPM)); S16 = SPB / 16.0; BEAT_S = 60.0 / BPM
SW = 0.56
ROOT = 38                                              # Re (D2) para el bajo
KICK = V.kick_disco()

# acordes [bass_root, t1, t2, t3] octava media — Dm Bb F C (i VI III VII)
CHORDS = [[38, 50, 53, 57], [34, 46, 50, 53], [41, 53, 57, 60], [36, 48, 52, 55]]
# bajo disco octava-bounce (step16, oct_off, len16, vel) ciclo de 2 compases
BASSP = [(0,0,2,1.0),(4,1,1,.7),(6,0,1,.8),(8,0,2,.9),(12,1,1,.7),(14,0,1,.7),
         (16,0,2,1.0),(20,1,1,.7),(22,0,1,.8),(24,0,2,.9),(28,1,1,.7),(30,0,1,.7)]
# arpegio 16vos (grados de la tríada, subiendo/bajando) ciclo 1 compás
ARP = [0,1,2,3,2,1,2,3,0,1,2,3,2,3,2,1]
# gancho del lead (Re menor pentatónica) (step16, grado, oct, len16) ciclo 2 compases
HOOK = [(0,0,1,3),(6,2,1,2),(10,3,1,2),(16,4,1,2),(20,2,1,3),(26,0,1,4)]

SONG = [('intro',24),('build',16),('body',40),('break',24),('build2',16),('peak',40),('outro',20)]
TOTBARS = sum(b for _, b in SONG)

def sw(s):
    return s * S16 + ((SW - 0.5) * 2 * S16 if s % 2 else 0.0)

def add(buf, pos, x, g=1.0):
    pos = int(pos)
    if pos < 0: x = x[-pos:]; pos = 0
    e = min(len(buf), pos + len(x))
    if e > pos: buf[pos:e] += x[:e - pos] * g

def plan(sec, p):
    """gains por bar según sección y posición p (0..1)."""
    b = dict(kick=1, bass=1, hats=0.7, shk=0.6, clap=1, conga=0.6, arp=0, lead=0,
             pad=0, bell=0, vox=0, gain=1.0, predrop=0)
    if sec == 'intro':
        b.update(clap=0 if p < 0.4 else 1, conga=0.3 if p < 0.5 else 0.6, hats=0.4 + 0.3*p,
                 gain=0.7 + 0.3*p, kick=0 if p < 0.15 else 1, arp=0.5 if p > 0.6 else 0)
    elif sec == 'build':
        b.update(arp=1, conga=0.8, pad=0.5, gain=0.9 + 0.1*p, vox=0.4)
        if p > 0.85: b.update(kick=0, bass=0, clap=0, predrop=1)      # silencio pre-drop
    elif sec == 'body':
        b.update(arp=1, lead=1, pad=0.7, conga=0.85, bell=0.5, vox=0.6, gain=1.02)
    elif sec == 'break':
        if p < 0.75:                                                  # breakdown cinemático
            b.update(kick=0, bass=0, clap=0, conga=0.1, hats=0.1, shk=0.1,
                     arp=0.8, lead=0.7, pad=1, bell=0.7, vox=1, gain=0.72)
        else:
            b.update(pad=0.6, arp=1, vox=0.8, predrop=1 if p > 0.9 else 0, gain=0.9)
    elif sec == 'build2':
        b.update(arp=1, conga=0.9, pad=0.5, lead=0.6, gain=0.95, vox=0.5)
        if p > 0.85: b.update(kick=0, bass=0, clap=0, predrop=1)
    elif sec == 'peak':
        b.update(arp=1, lead=1, pad=0.7, conga=1.0, bell=0.6, vox=0.7, hats=0.9, gain=1.05)
    elif sec == 'outro':
        b.update(arp=0.5*(1-p), lead=0, pad=0.4*(1-p), conga=0.5, bell=0, vox=0,
                 gain=1.0 - 0.5*max(0, p-0.3), clap=1 if p < 0.6 else 0)
    return b

def secat(gb):
    """(section, p) para el bar global gb."""
    acc = 0
    for name, bars in SONG:
        if gb < acc + bars:
            return name, (gb - acc) / max(1, bars - 1)
        acc += bars
    return SONG[-1][0], 1.0

def render():
    rng = np.random.default_rng(303)
    n = TOTBARS * SPB
    kickb = np.zeros(n, np.float32); bassb = np.zeros(n, np.float32)
    drumb = np.zeros(n, np.float32); arpb = np.zeros(n, np.float32)
    leadb = np.zeros(n, np.float32); padL = np.zeros(n, np.float32); padR = np.zeros(n, np.float32)
    voxb = np.zeros(n, np.float32); bellb = np.zeros(n, np.float32)
    kpos = []
    for gb in range(TOTBARS):
        sec, p = secat(gb); b = plan(sec, p)
        base = gb * SPB
        ch = CHORDS[(gb // 2) % 4]; root = ch[0]; cyc = gb % 2
        last = (gb % 8 == 7)
        silent = (b['predrop'] and last)
        # kick
        if b['kick'] and not silent:
            for beat in range(4):
                add(kickb, base + beat*4*S16, KICK); kpos.append(int(base+beat*4*S16))
        # clap 2&4
        if b['clap'] and not silent:
            for s in (4, 12): add(drumb, base + sw(s) - 0.016*SR, V.clap(rng), b['clap']*0.7)
        # hats swing
        if b['hats'] > 0 and not silent:
            for s in range(16):
                op = (s % 4 == 2)
                add(drumb, base + sw(s) + rng.normal(0,.002)*SR, V.hat(rng, open_=op),
                    (0.5 if s%2 else 0.3)*b['hats']*(0.8 if op else 1))
        if b['shk'] > 0 and not silent:
            for s in range(0,16,2): add(drumb, base+sw(s)+rng.normal(0,.003)*SR, V.shaker(rng), 0.3*b['shk'])
        # drum-line congas + redoble de toms al cierre de frase
        if b['conga'] > 0 and not silent:
            capat = (3,6,10,14) if cyc==0 else (2,7,11,14)
            for s in capat:
                add(drumb, base+sw(s)+rng.normal(0,.003)*SR, V.conga(midi_f(50 if s%3 else 57), rng, slap=(s%2==1)), b['conga']*0.5)
            if b['conga'] >= 0.85 and last:
                for k, s in enumerate((10,12,13,14,15)):
                    add(drumb, base+sw(s), V.tom(190-24*k, rng), 0.42+0.08*k)
            if b['conga'] >= 0.8 and cyc==1 and gb%4==3:
                add(drumb, base+sw(7), V.rimshot(rng), 0.4)
        # BAJO limpio octava-bounce
        if b['bass'] and not silent:
            prev=None
            for (st,oo,ln,v) in BASSP:
                if st//16 != cyc: continue
                s = st%16; m = root-12+12*oo; f = midi_f(m)
                gl = prev if (prev and rng.uniform()<0.25) else None
                add(bassb, base+sw(s)+rng.normal(0,.003)*SR, V.bass_disco(f, ln*S16/SR*1.4, rng, glide_from=gl), v*0.92)
                prev=f
        # ARPEGIO (16vos con delay punteado luego)
        if b['arp'] > 0:
            for s in range(16):
                deg = ARP[s]; m = ch[1+deg%3] + 12
                add(arpb, base+s*S16, V.arp_synth(midi_f(m), 0.14, rng), b['arp']*0.5)
        # LEAD cósmico (gancho)
        if b['lead'] > 0 and gb%2==0:
            for (s,d,o,ln) in HOOK:
                pos = base + int(sw(s%16)) + (SPB if s>=16 else 0)
                add(leadb, pos, V.lead_analog(midi_f(pdeg(62,d,o)), ln*S16/SR*1.2, rng), b['lead']*0.5)
        # PADS cósmicos
        if b['pad'] > 0.2 and gb%2==0:
            x = V.pad_cosmic([m+12 for m in ch[1:]], 2*SPB/SR*1.05, rng)
            add(padL, base, x, b['pad']); add(padR, base+int(0.018*SR), x, b['pad']*0.93)
        # campanas FM
        if b['bell'] > 0 and gb%4==0:
            for s in (0,10,20):
                add(bellb, base+int(s*S16)+(0 if s<16 else 0), V.bell_fm(midi_f(pdeg(62,(s//5)%5,1)), 0.5, rng), b['bell']*0.5)
        # VOZ vocoder / etérea
        if b['vox'] > 0:
            if sec in ('break',) and p < 0.75:
                if gb%4==0: add(voxb, base, V.vox_ether(midi_f(pdeg(62,0,0)), 2*SPB/SR, rng, 'a'), b['vox']*0.5)
            elif gb%2==1:
                for s in (6,14):
                    if rng.uniform()<0.6:
                        add(voxb, base+sw(s), V.vox_robot(midi_f(pdeg(62,int(rng.integers(0,5)),0)), 0.2, rng, 'o'), b['vox']*0.5)
        # FX de sección
        if last and b['predrop']:
            add(arpb, base, V.riser(4*BEAT_S, rng), 0.9)
        if sec in ('body','peak') and gb%8==0 and p>0.05:
            add(bellb, base, V.laser(rng, up=(gb%16==0)), 0.5)

    # ------- buses (procesamiento SUAVE, dinámico)
    def sc(depth=0.4, rel=0.10):
        env = np.ones(n, np.float32)
        dip = 1.0 - depth*np.exp(-np.arange(int(rel*4*SR))/(rel*SR)).astype(np.float32)
        for p_ in kpos:
            e = min(n, p_+len(dip))
            if e>p_: env[p_:e] = np.minimum(env[p_:e], dip[:e-p_])
        return env
    env = sc()
    bassb *= env
    drum_st = widen(drumb, amount=0.42, seed=5)
    arp_st = pingpong(arpb*(env*0.4+0.6), BEAT_S, fb=0.42, mix=0.4, taps=7, damp=5200)  # dotted-8th
    lead_st = pingpong(leadb, BEAT_S, fb=0.4, mix=0.36, taps=6, damp=4600)
    bell_st = pingpong(bellb, BEAT_S, fb=0.34, mix=0.3, taps=5, damp=6000)
    vox_st = pingpong(voxb*(env*0.4+0.6), BEAT_S, fb=0.4, mix=0.42, taps=6, damp=5000)
    pads = np.stack([padL, padR]) * (env*0.4+0.6)[None,:]
    ir = np.random.default_rng(21).standard_normal(int(2.6*SR)).astype(np.float32)*np.exp(-np.linspace(0,6.5,int(2.6*SR))).astype(np.float32)
    ir = lp(ir, 4800, 2); ir /= np.sqrt((ir**2).sum())+1e-12
    verb = np.stack([fconv(pads[0], ir*0.3), fconv(pads[1], ir*0.3)])
    music = (drum_st*0.72 + arp_st*0.6 + lead_st*0.6 + bell_st*0.5 + vox_st*0.5 + (pads+verb)*0.8)
    mm = 0.5*(music[0]+music[1]); ss = bp(0.5*(music[0]-music[1]), 200, 11000, 2)*2.1
    mix = np.stack([mm+ss, mm-ss])
    mix += kickb[None,:]*1.15 + bassb[None,:]*1.0            # bajo limpio, nivel moderado
    # automatización de gain por bar (macro-dinámica → onda natural)
    genv = np.ones(n, np.float32)
    for gb in range(TOTBARS):
        sec, p = secat(gb); genv[gb*SPB:(gb+1)*SPB] = plan(sec,p)['gain']
    genv = lp(genv, 2.0, 1); mix *= genv[None,:]
    mix = np.stack([sat(mix[0],1.06,0.03), sat(mix[1],1.06,0.03)])   # calorcito MUY suave
    mix = sub_mono(mix, 120.0)
    pk = np.abs(mix).max()
    if pk>0.94: mix *= 0.94/pk
    return mix

def build():
    print(f'FICCIÓN · {TOTBARS} compases ≈ {TOTBARS*SPB/SR/60:.1f} min', flush=True)
    mix = render()
    # normaliza suave (sin clipeo agresivo) — el limitador hace el control fino
    mix = np.stack([sat(mix[0],1.3,0.02), sat(mix[1],1.3,0.02)])
    mix *= 0.90/max(1e-9, float(np.abs(mix).max()))
    raw = os.path.join(TMP,'ficcion-raw.wav'); wav_write(raw, mix); del mix
    os.makedirs(os.path.join(HERE,'masters'), exist_ok=True)
    final = os.path.join(HERE,'masters','amr-ficcion.wav')
    print('  … master -9.0 LUFS (dinámico)', flush=True)
    hist = master_file(raw, final, target_i=-9.0, ceiling_db=-1.2)
    from dream_core import ffdecode
    I,lra,tp = ffmeter(final)
    print(f'MASTER: {hist} → {I} LUFS · LRA {lra} · TP {tp} · {spectrum_pct(ffdecode(final,mono=True))}')
    print(final)

if __name__ == '__main__':
    build()
