#!/usr/bin/env python3
"""ÉXITO — todo lo aprendido de los 7 desgloses, junto.

Cada decisión de aquí sale de un video que André me pasó, no de mi criterio.

ORDEN DE CONSTRUCCIÓN (Against The Clock / PML)
  kick → bajo → sidechain → pad → return compartido → arp → lead → DRUMS AL FINAL
  El tipo lo dice: "si no, voy a tener un track de puro kick y melodía".
  Yo antes empezaba por la batería y apilaba loops. Al revés.

EL GRAVE (video de kick/bass en Ibiza)
  "Nunca tengas el kick y el bajo sonando al mismo tiempo."
  El kick cae en los pasos 0,4,8,12 → el bajo va en 2,6,10,14. En los HUECOS.
  Mi error medido: yo me saltaba 3,7,11,15 y tocaba justo encima del kick.
  Y: "ser gordo no es ser lo más grave posible — lo que se siente gordo está
  entre 80 y 120 Hz". El sub es sensación física, no gordura.

EL BAJO ES EL KICK (Swedish House Mafia, "One")
  "Ese sonido era sólo un kick, metido a un sampler y loopeado a una velocidad
  altísima." Si el bajo ES el kick, comparten timbre y resonancias — dejan de
  pelearse por definición. Es la solución más limpia al problema del grave.

LA NOTA PEDAL (Innerbloom + SHM + Fred again — TRES desgloses independientes)
  "Cuando una progresión tiene nota pedal, sabes que va a ser emocional."
  Una nota sostenida que NO cambia mientras los acordes debajo sí cambian.

LA MELODÍA NO SE TOCA (Swedish House Mafia)
  "El ritmo se queda igual, la melodía se queda igual — sólo construyen
  alrededor." Cuatro fases del MISMO material. Yo hacía lo contrario.

VELOCITY → CUTOFF (Fred again, "Marea")
  "Casi cada nota pega con una velocity distinta" → suave = más oscura, no
  sólo más baja. Coincide con lo medido: varía envolventes, no posiciones.

HATS (Marea + Innerbloom)
  Varían en LARGO y AFINACIÓN, no sólo volumen. Y un golpe extra cada dos.

MEZCLA (video del remix)
  "Lo más fuerte del track tiene que ser el kick."
  "El sub va mono, sin ancho."
  "He ido quitando graves a todo lo que no los necesita, desde el principio."
"""
import os, subprocess
import numpy as np
import imageio_ffmpeg
from dream_core import (SR, wav_write, sat, lp, hp, bp, master_file, ffmeter,
                        ffdecode, spectrum_pct, width_corr, sub_mono, fconv)
import kit as K
import instrumentos as I
import splice as SP
from af_voices import MIN, deg, midi_f, _ir
from groove import Groove

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '_exito'); os.makedirs(OUT, exist_ok=True)

BPM = 120.0
SPB = int(round(SR * 240.0 / BPM))
S16 = SPB / 16.0
ROOT = 57                       # La menor
BARS = 208

# ── acordes de 16 compases (Innerbloom: "no son 8, son 16")
#    i - VI - III - VII, y el último cambia en la segunda mitad
PROG_A = [0, 5, 2, 6]
PROG_B = [0, 5, 2, 4]           # el cambio que "resuelve"
PEDAL  = ROOT + 12 + MIN[4]     # ⭐ LA NOTA PEDAL: mi, sostenida sobre todo

def acorde(bar):
    p = PROG_A if (bar // 16) % 2 == 0 else PROG_B
    g = p[(bar // 4) % 4]        # 4 compases por acorde = 16 por vuelta
    return dict(raiz=ROOT + MIN[g % 7] - 24,
                tri=[deg(ROOT, g, 0, MIN), deg(ROOT, g+2, 0, MIN), deg(ROOT, g+4, 0, MIN)])

# ── LA MELODÍA — llamada y respuesta, 2 compases, NO CAMBIA EN TODO EL TRACK
#    (compás, paso16, largo16, grado, velocity)
MELODIA = [(0, 0, 3, 0, 1.00), (0, 4, 2, 2, 0.55), (0, 7, 3, 4, 0.85),
           (0, 12, 4, 2, 0.45),
           (1, 2, 3, 4, 0.95), (1, 6, 2, 2, 0.50), (1, 10, 6, 0, 0.75)]

# ══════════════════════════════════════════ EL BAJO ES EL KICK
_BASS_CACHE = {}
def bajo_del_kick(midi, dur, rng):
    """SHM 'One': loopea el kick a frecuencia de audio y se vuelve un tono
    con SU timbre. Bajo y kick comparten cuerpo — no pueden pelearse."""
    f = midi_f(midi)
    key = (round(f, 2), round(dur, 3))
    if key not in _BASS_CACHE:
        k = K.smp(K.KICK808)                       # el 808, que tiene cuerpo largo
        per = int(SR / f)                          # un ciclo = la nota
        if per < 8 or len(k) < per: return np.zeros(int(dur*SR), np.float32)
        ciclo = k[:per].astype(np.float32)
        ciclo -= np.linspace(ciclo[0], ciclo[-1], per)   # sin salto al loopear
        n = int(dur * SR)
        x = np.tile(ciclo, int(np.ceil(n/per)))[:n]
        t = np.arange(n, dtype=np.float32) / SR
        env = np.minimum(1.0, t/0.004) * np.exp(-np.maximum(0.0, t - dur*0.55)/0.05)
        x = sat(x * env, 1.35, 0.04)
        m = float(np.abs(x).max())
        _BASS_CACHE[key] = (x/m if m > 0 else x)
    return _BASS_CACHE[key].copy()

def sidechain_partido(bajo, kpos, corte=200.0, prof=0.92, rel=0.115):
    """Marsh: 'lo partí en 200 Hz — el grave se bombea al 100%, el medio pasa'.
    Ducking SÓLO debajo del corte. Los medios (la 'gordura' de 80-120... arriba)
    siguen sonando, así el bajo no desaparece."""
    n = len(bajo)
    e = np.ones(n, np.float32); m = int(rel*4*SR)
    dip = 1.0 - prof*np.exp(-np.arange(m)/(rel*SR)).astype(np.float32)
    for p in kpos:
        q = min(n, p+m)
        if q > p: e[p:q] = np.minimum(e[p:q], dip[:q-p])
    grave = lp(bajo, corte, 2) * e
    medio = bajo - lp(bajo, corte, 2)
    return grave + medio

# ── UN SOLO REVERB COMPARTIDO (Lane 8: "si mandas todo a un cuarto,
#    suena como si la música estuviera junta")
IR_SALA = _ir(3.2, 5200, 91, 0.03)
def sala(x, mix=0.3):
    return x + fconv(x, IR_SALA)[:len(x)] * mix

def seccion(nombre, bars, capas, abre, seed):
    n = bars*SPB
    B = {k: np.zeros(n, np.float32) for k in ('kick','bajo','mel','pad','pedal','perc')}
    rng = np.random.default_rng(seed)
    g = Groove('afro', S16, SR, bpm=BPM, seed=seed)
    kpos = []

    def add(b, pos, x, gain=1.0):
        pos = int(pos)
        if pos < 0: x = x[-pos:]; pos = 0
        q = min(len(b), pos+len(x))
        if q > pos: b[pos:q] += x[:q-pos]*gain

    for bar in range(bars):
        base = bar*SPB
        c = acorde(bar)
        prog = bar/max(1, bars-1)

        # ---- KICK: recto, y es lo MÁS FUERTE del track
        if 'kick' in capas:
            for beat in range(4):
                p = base + beat*4*S16
                add(B['kick'], p, K.vary(K.smp(K.KICK), rng, 0.010, 0.05), 1.0)
                kpos.append(int(p))

        # ---- BAJO: en los HUECOS 2,6,10,14 — nunca encima del kick
        if 'bajo' in capas:
            for s in (2, 6, 10, 14):
                add(B['bajo'], base + s*S16, bajo_del_kick(c['raiz']+12, (S16/SR)*1.7, rng), 0.9)

        # ---- ACORDES + NOTA PEDAL
        if 'pad' in capas and bar % 4 == 0:
            add(B['pad'], base, I.acorde('marimba', [m+12 for m in c['tri']],
                                         4*SPB/SR*0.95, rng), 0.30)
        if 'pedal' in capas and bar % 8 == 0:
            add(B['pedal'], base, I.nota('kalimba', PEDAL, 8*SPB/SR*0.9, rng, vel=0.55), 0.34)

        # ---- MELODÍA: balafón, velocity distinta por nota, SIEMPRE la misma frase
        if 'mel' in capas:
            for (mb, st, ln, gr, vel) in MELODIA:
                if bar % 2 != mb: continue
                nt = ROOT + 12 + MIN[gr % 7] + 12*(gr // 7)
                v = I.nota('balafon', nt, ln*S16/SR, rng,
                           vel=vel*(0.85+0.15*rng.random()), largo_var=0.12)
                p = int(g.pos(base, st, bar))
                if p < 0: v = v[-p:]; p = 0
                add(B['mel'], p, v, 0.55)

        # ---- DRUMS AL FINAL del orden de construcción
        if 'perc' in capas:
            for s in (4, 12):
                add(B['perc'], g.pos(base,s,bar)-0.010*SR,
                    K.vary(K.smp(K.CLAP), rng, 0.02, 0.12), 0.34*g.vel(s,bar))
            for s in range(16):
                if s % 2: continue
                # hats variando en LARGO y AFINACIÓN, no sólo volumen
                sm = K.vary(K.smp(K.HATC), rng, 0.05, 0.30)
                L = int(len(sm)*(0.55 + 0.45*rng.random()))
                sm = sm[:max(64, L)]
                add(B['perc'], g.pos(base,s,bar), sm, g.vel(s,bar)*0.26)
                if (s//2) % 2 == 1:                # el golpe EXTRA cada dos hats
                    add(B['perc'], g.pos(base,s,bar)+S16*0.5,
                        K.vary(K.smp(K.HATC), rng, 0.06, 0.4), g.vel(s,bar)*0.13)
            for s in range(2,16,4):
                add(B['perc'], g.pos(base,s,bar),
                    K.vary(K.smp(K.SHAKER), rng, 0.04, 0.28), 0.22*g.vel(s,bar))

    # ══════ MEZCLA
    B['bajo'] = sidechain_partido(B['bajo'], kpos)
    def filtra(x, cmin, cmax):
        if abre >= 0.99: return x
        return lp(x, float(cmin + (cmax-cmin)*abre), 2)

    # quitarle graves a TODO lo que no es bajo, desde el principio
    perc = hp(B['perc'], 300.0, 2)
    mel  = hp(filtra(B['mel'], 800, 12000), 200.0, 2)
    pad  = hp(filtra(B['pad'], 600, 6000), 200.0, 2)
    ped  = hp(filtra(B['pedal'], 700, 8000), 250.0, 2)

    def ancho(x, ms, seed2):
        d = int(ms*1e-3*SR)
        return np.stack([x, np.concatenate([np.zeros(d,np.float32), x[:-d]])])

    mus = (ancho(sala(mel, 0.26), 11, 1)*0.62 + ancho(sala(pad, 0.34), 17, 2)*0.50
           + ancho(sala(ped, 0.40), 23, 3)*0.42 + ancho(perc, 7, 4)*0.55)
    mix = mus + B['kick'][None,:]*1.0 + B['bajo'][None,:]*0.72   # kick = lo más fuerte
    mix = np.stack([m - bp(m, 250.0, 400.0, 2)*0.22 for m in mix])
    return sub_mono(mix, 120.0)            # sub en mono, 6 dB/oct

# ── CUATRO FASES DEL MISMO MATERIAL (SHM: la melodía no se toca)
SECCIONES = [
 ('INTRO',   32, ('kick','perc'),                                  0.35),
 ('FASE 1',  32, ('kick','bajo','perc'),                           0.55),
 ('FASE 2',  32, ('kick','bajo','perc','pad','pedal'),             0.80),
 ('FASE 3',  32, ('kick','bajo','perc','pad','pedal','mel'),       1.00),
 ('BREAK',   32, ('perc','pad','pedal','mel'),                     0.70),
 ('FASE 4',  32, ('kick','bajo','perc','pad','pedal','mel'),       1.00),
 ('SALIDA',  16, ('kick','perc','pad'),                            0.45),
]

if __name__ == '__main__':
    print(f'ÉXITO · {BARS} compases · {BARS*SPB/SR/60:.2f} min · {BPM:.0f} BPM · La menor', flush=True)
    partes = []
    for i,(nom,bars,capas,abre) in enumerate(SECCIONES):
        print(f'  … {nom:8s} {bars:>3} comp  filtros {abre*100:3.0f}%  {"+".join(capas)}', flush=True)
        partes.append(seccion(nom, bars, capas, abre, 90+i*6))
    x = np.concatenate(partes, axis=1)
    x = np.stack([sat(x[0],1.02,0.015), sat(x[1],1.02,0.015)])
    x *= 0.92/max(1e-9, float(np.abs(x).max()))

    raw = os.path.join(OUT,'raw.wav'); wav_write(raw, x)
    fin = os.path.join(OUT,'exito.wav')
    hist = master_file(raw, fin, target_i=-11.0, ceiling_db=-1.0)
    os.remove(raw)
    m4a = os.path.join(OUT,'exito.m4a')
    subprocess.run([FF,'-y','-v','error','-i',fin,'-c:a','aac_at','-b:a','256k',
                    '-movflags','+faststart',m4a], check=True)
    Iu,lra,tp = ffmeter(fin)
    y = ffdecode(fin); mono = 0.5*(y[0]+y[1])
    rms = float(np.sqrt((mono.astype(np.float64)**2).mean())); pk = float(np.abs(y).max())
    w,c,cs = width_corr(y)
    print(f'\nMASTER {Iu} LUFS · LRA {lra} · TP {tp}')
    print(f'CREST {20*np.log10(pk/rms):.1f} dB · ancho {w:.3f} · corr {c:.3f} · graves-mono {cs:.3f}')
    print(f'ESPECTRO {spectrum_pct(mono)}')
    os.remove(fin)
    print(f'\n  {m4a}')
