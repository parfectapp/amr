#!/usr/bin/env python3
"""ROLA — la primera hecha con material profesional de verdad.

Todo lo aprendido hoy, junto:
  · loops REALES de Splice (licencia de suscriptor, uso comercial)
  · balafón REAL de VCSL para la melodía (el timbre que eligió André)
  · groove afro medido, no jitter aleatorio
  · 120 BPM exactos y 208 compases — las cifras de Keinemusik
  · estructura en múltiplos de 16, elementos que ENTRAN FILTRADOS, sin drop
  · ESTÉREO DESDE LA FUENTE: los loops vienen en estéreo y se preservan.
    (El defecto medido hoy: extrastereo MULTIPLICA el canal side, así que si
     la síntesis lo produce en cero, 1.9 × 0 = 0. GUERRERO mide mono literal.
     No se puede ensanchar en el máster algo que nació mono.)
  · máster suave para no matar el crest (taller01 dio 7.3 dB contra 8.7-13.7
    de las referencias — sobre-limitado)
"""
import os, sys, subprocess
import numpy as np
import imageio_ffmpeg
from dream_core import (SR, wav_write, sat, lp, hp, bp, master_file, ffmeter,
                        ffdecode, spectrum_pct, width_corr)
import instrumentos as I
import splice as SP
from af_voices import MIN, deg
from groove import Groove

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '_rola'); os.makedirs(OUT, exist_ok=True)

BPM = 120.0
SPB = int(round(SR * 240.0 / BPM))          # 1 compás = 2.000 s exactos
S16 = SPB / 16.0
ROOT = 57                                    # La menor
BARS = 208                                   # 6:56, como "The Rapture Pt.III"

# ── el material, elegido a mano del índice
MAT = {
 'drums':  ('SS_FA_120_drum_loop_are_you_heaven', 120),
 'hats':   ('TS_HIHAT_120_hats_14_inch_eights_bounce_barks', 120),
 'perc':   ('ff_pmt_122_drum_loop_clasp_percussion', 122),
 'piano':  ('ZEN_SHAV_120_piano_loop_club_Amin', 120),
 'bass':   ('BOS_ESG_130_Bass_Synth_Loop_Calm_Am', 130),
}

def halla(clave):
    nom, bpm = MAT[clave]
    for x in SP.indice():
        if x['nombre'].startswith(nom): return x['ruta'], bpm
    return None, bpm

def estira(x, ratio, grano=0.06):
    """Estiramiento granular que PRESERVA EL TONO. Resamplear cambiaría el tono:
    130→120 baja 1.4 semitonos y un bajo en La menor se volvería Sol."""
    if abs(ratio-1.0) < 0.004: return x
    est = x.ndim == 2
    def uno(v):
        g = int(grano*SR); hop_in = g//2; hop_out = int(hop_in*ratio)
        n_out = int(len(v)*ratio)
        out = np.zeros(n_out+g, np.float32); win = np.hanning(g).astype(np.float32)
        pi = po = 0
        while po+g < len(out) and pi+g < len(v):
            out[po:po+g] += v[pi:pi+g]*win
            pi += hop_in; po += hop_out
        return out[:n_out]
    return np.stack([uno(x[0]), uno(x[1])]) if est else uno(x)

def carga(clave, compases=1):
    """Carga el loop, lo estira al tempo y lo recorta a N compases exactos."""
    ruta, bpm = halla(clave)
    if not ruta: return None
    x = ffdecode(ruta)                        # ESTÉREO — no se suma a mono
    if x.ndim == 1: x = np.stack([x, x])
    if abs(bpm-BPM) > 0.5: x = estira(x, bpm/BPM)
    n = compases*SPB
    if x.shape[1] < n:
        rep = int(np.ceil(n/x.shape[1]))
        x = np.tile(x, (1, rep))
    x = x[:, :n]
    m = float(np.abs(x).max())
    return x/m if m > 0 else x

# ── la melodía que eligió André: BALAFÓN, grabación real
MELODIA = [(0,0,4,0), (0,6,3,2), (0,10,6,4), (1,2,4,2), (1,8,8,0)]
PROG = [0,3,6,2]                              # i-iv-VII-III, el "suspenso" que eligió

def acorde(ci):
    g = PROG[ci % 4]
    return [deg(ROOT,g,0,MIN), deg(ROOT,g+2,0,MIN), deg(ROOT,g+4,0,MIN)]

# ── estructura: 7 secciones, todas múltiplo de 16
SECCIONES = [
 dict(n='INTRO',     bars=32, abre=0.30, capas=('perc','hats')),
 dict(n='ENTRADA',   bars=32, abre=0.55, capas=('drums','perc','hats','bass')),
 dict(n='GROOVE',    bars=32, abre=0.85, capas=('drums','perc','hats','bass','balafon')),
 dict(n='CUERPO',    bars=32, abre=1.00, capas=('drums','perc','hats','bass','balafon','piano')),
 dict(n='BREAKDOWN', bars=32, abre=0.65, capas=('perc','hats','piano','balafon')),
 dict(n='CUMBRE',    bars=32, abre=1.00, capas=('drums','perc','hats','bass','balafon','piano')),
 dict(n='SALIDA',    bars=16, abre=0.40, capas=('perc','hats','piano')),
]

def seccion(s, idx, cache):
    bars = s['bars']; n = bars*SPB
    mix = np.zeros((2, n), np.float32)
    rng = np.random.default_rng(50 + idx*7)
    g = Groove('afro', S16, SR, bpm=BPM, seed=50+idx)
    abre = s['abre']

    def filtra(x, cmin, cmax, prog):
        """entrar ≠ sonar completo: el filtro abre a lo largo de la sección"""
        if abre >= 0.99: return x
        c = cmin + (cmax-cmin)*min(1.0, abre*(0.80+0.20*prog))
        return np.stack([lp(x[0], float(c), 2), lp(x[1], float(c), 2)])

    # ---- capas de loop
    for capa, gain, (cmin, cmax) in (('drums',0.80,(400,16000)), ('perc',0.52,(600,16000)),
                                     ('hats',0.34,(1200,16000)), ('bass',0.62,(120,3000)),
                                     ('piano',0.44,(500,9000))):
        if capa not in s['capas']: continue
        L = cache[capa]
        if L is None: continue
        for b in range(bars):
            blk = L[:, (b % (L.shape[1]//SPB))*SPB : ((b % (L.shape[1]//SPB))+1)*SPB]
            if blk.shape[1] < SPB: continue
            mix[:, b*SPB:(b+1)*SPB] += filtra(blk, cmin, cmax, b/max(1,bars-1)) * gain

    # ---- BALAFÓN real tocando la melodía
    if 'balafon' in s['capas']:
        bal = np.zeros(n, np.float32)
        for b in range(bars):
            base = b*SPB; c = acorde(b//2)
            for (mb, st, ln, gr) in MELODIA:
                if b % 2 != mb: continue
                nt = ROOT + 12 + MIN[gr % 7] + 12*(gr // 7)
                v = I.nota('balafon', nt, ln*S16/SR, rng)
                p = int(g.pos(base, st, b))
                # el feel afro EMPUJA 12 ms adelante, así que en el compás 0 la
                # posición sale NEGATIVA — y un índice negativo en numpy corta
                # desde el final del arreglo, no desde el inicio.
                if p < 0:
                    v = v[-p:]; p = 0
                e = min(n, p + len(v))
                if e > p: bal[p:e] += v[:e-p] * (0.5 + 0.5*g.vel(st,b))
        # ancho REAL por decorrelación, no multiplicando un side que no existe
        d = int(0.009*SR)
        bal_st = np.stack([bal, np.concatenate([np.zeros(d,np.float32), bal[:-d]])])
        mix += filtra(bal_st, 700, 12000, 0.5) * 0.42

    return mix

def main():
    print(f'ROLA · {BARS} compases · {BARS*SPB/SR/60:.2f} min · {BPM:.0f} BPM · La menor', flush=True)
    print('  cargando material de Splice…', flush=True)
    cache = {}
    for k in MAT:
        cache[k] = carga(k, compases=4)
        print(f'    {"✓" if cache[k] is not None else "✗"} {k:7s} {MAT[k][0][:46]}', flush=True)

    partes = []
    for i, s in enumerate(SECCIONES):
        print(f'  … {s["n"]:10s} {s["bars"]:>3} comp  filtros {s["abre"]*100:3.0f}%  '
              f'{"+".join(s["capas"])}', flush=True)
        partes.append(seccion(s, i, cache))
    x = np.concatenate(partes, axis=1)

    # corte de lodo + saturación MUY suave (el crest es sagrado)
    x = np.stack([m - bp(m, 250.0, 400.0, 2)*0.26 for m in x])
    x = np.stack([sat(x[0], 1.06, 0.02), sat(x[1], 1.06, 0.02)])
    x *= 0.92/max(1e-9, float(np.abs(x).max()))

    raw = os.path.join(OUT, 'raw.wav'); wav_write(raw, x)
    fin = os.path.join(OUT, 'rola.wav')
    hist = master_file(raw, fin, target_i=-10.0, ceiling_db=-1.0)
    os.remove(raw)
    m4a = os.path.join(OUT, 'rola.m4a')
    subprocess.run([FF,'-y','-v','error','-i',fin,'-c:a','aac_at','-b:a','256k',
                    '-movflags','+faststart',m4a], check=True)
    I_, lra, tp = ffmeter(fin)
    y = ffdecode(fin); mono = 0.5*(y[0]+y[1])
    rms = float(np.sqrt((mono.astype(np.float64)**2).mean())); pk = float(np.abs(y).max())
    w, c, cs = width_corr(y)
    print(f'\nMASTER: {hist} → {I_} LUFS · LRA {lra} · TP {tp}')
    print(f'CREST {20*np.log10(pk/rms):.1f} dB   (refs 8.7–13.7)')
    print(f'ANCHO {w:.3f}  corr {c:.3f}  graves-mono {cs:.3f}')
    print(f'ESPECTRO {spectrum_pct(mono)}')
    print(f'\n  http://localhost:4274/_rola/rola.m4a')
    os.remove(fin)

if __name__ == '__main__':
    main()
