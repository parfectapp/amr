#!/usr/bin/env python3
"""¿Se puede convertir folk gringo en voz de afro-house? Demostración, no argumento.

André escuchó los pasajes de 30 s del acervo MusicBox y dijo "no me gustan".
Tiene razón: 30 segundos de banjo de Apalaches suenan a banjo de Apalaches.

La apuesta: en CHOPS de 0.25 s una sílaba pierde su género. Y la técnica está
documentada en la propia Keinemusik — el único sample de voz "de mundo" que se
le conoce a Rampa es Le Mystère des Voix Bulgares en "The Church": una grabación
etnográfica vieja, procesada hasta que deja de sonar a lo que era.

Cadena que se aplica a cada chop:
  1. pitch por resample (baja/sube y borra el timbre de "grabación vieja")
  2. estiramiento granular para sostener la vocal (la fuente dura 0.25 s)
  3. pasabanda en la zona de formantes + realce
  4. gate al grid con el swing AFRO que eligió André
  5. reverb DUCKEADO (la técnica de mayor valor del research de Anyma)
  6. saturación suave

Salida: _demo/voz-ab.m4a
  0:00  el chop CRUDO, tal como viene del archivo
  0:08  el mismo chop procesado, solo
  0:16  en contexto: sobre el groove afro con batería real
"""
import os, glob, subprocess
import numpy as np
import imageio_ffmpeg
from dream_core import SR, wav_write, sat, widen, sub_mono, lp, hp, bp, fconv
import kit as K
from groove import Groove
import af_voices as A

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '_demo'); os.makedirs(OUT, exist_ok=True)
PACK = os.path.join(HERE, '_samples', 'musicbox', 'one_shots')
BPM = 120.0
SPB = int(round(SR * 240.0 / BPM)); S16 = SPB / 16.0


def dec(path):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR),
                          '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.frombuffer(raw, dtype='<f4').astype(np.float32)
    nz = np.nonzero(np.abs(x) > 2e-3)[0]
    if len(nz): x = x[nz[0]:]
    m = float(np.abs(x).max())
    return x / m if m > 0 else x


def vocalidad(x):
    """¿Este chop trae vocal cantada? A 0.25 s no hay ritmo silábico que medir,
    así que se busca estructura de formantes: energía en 300-3400 Hz y un
    espectro con picos marcados (la voz los tiene; una cuerda frotada es más plana)."""
    if len(x) < 1024: return 0.0
    W = 1 << 11
    sp = np.abs(np.fft.rfft(x[:W] * np.hanning(min(W, len(x[:W])))
                            if len(x) >= W else np.pad(x, (0, W - len(x)))))
    fr = np.fft.rfftfreq(W, 1.0 / SR)
    tot = sp.sum() + 1e-12
    form = sp[(fr >= 300) & (fr <= 3400)].sum() / tot
    agudo = sp[fr > 5000].sum() / tot
    b = sp[(fr >= 200) & (fr <= 4000)]
    picos = float(b.max() / (b.mean() + 1e-12))          # cuán picudo es
    return float(form * 1.0 + min(picos / 40.0, 1.0) * 0.8 - agudo * 1.2)


def estira(x, factor, grano=0.045):
    """Estiramiento granular: sostiene la vocal sin cambiarle el tono."""
    g = int(grano * SR); hop_in = g // 2
    n_out = int(len(x) * factor)
    out = np.zeros(n_out + g, np.float32)
    win = np.hanning(g).astype(np.float32)
    hop_out = int(hop_in * factor)
    pos_in = 0; pos_out = 0
    while pos_out + g < len(out) and pos_in + g < len(x):
        out[pos_out:pos_out + g] += x[pos_in:pos_in + g] * win
        pos_in += hop_in; pos_out += hop_out
    m = float(np.abs(out).max())
    return (out / m if m > 0 else out)[:n_out]


def pitch(x, semis):
    """Pitch por resample. Cambia tono Y duración — que es justo lo que borra
    el timbre de 'grabación vieja'."""
    r = 2.0 ** (semis / 12.0)
    n = int(len(x) / r)
    if n < 8: return x
    idx = np.minimum(len(x) - 1, (np.arange(n) * r)).astype(np.int32)
    return x[idx]


def procesa(x, semis=-5, largo_s=0.55, gate_hz=0.0):
    """La cadena completa: de sílaba folk a textura de afro-house."""
    y = pitch(x, semis)
    obj = int(largo_s * SR)
    if len(y) < obj: y = estira(y, obj / max(1, len(y)))
    y = y[:obj]
    t = np.arange(len(y), dtype=np.float32) / SR
    y = bp(y, 220.0, 3600.0, 2)                          # zona de formantes
    y += hp(y, 2000.0, 2) * 0.25                          # un poco de aire
    env = np.minimum(1.0, t / 0.02) * np.minimum(1.0, np.maximum(0.0, largo_s - t) / 0.18)
    y = y * env
    if gate_hz > 0:                                       # trance-gate opcional
        g = (0.35 + 0.65 * ((t * gate_hz) % 1.0 < 0.55)).astype(np.float32)
        y = y * lp(g, 700.0, 1)
    y = sat(y, 1.25, 0.05)
    return A.duck_rev(y * 0.5, A.IR_VAST, mix=0.85, depth=0.75)   # reverb duckeado


def bloque_groove(voces, bars=8, seed=5):
    """El mismo groove afro con batería real, y las voces encima."""
    n = bars * SPB + SPB
    kick = np.zeros(n, np.float32); perc = np.zeros(n, np.float32)
    vox = np.zeros(n, np.float32)
    rng = np.random.default_rng(seed)
    g = Groove('afro', S16, SR, bpm=BPM, seed=seed)

    def add(buf, pos, x, gain=1.0):
        pos = int(pos)
        if pos < 0: x = x[-pos:]; pos = 0
        e = min(len(buf), pos + len(x))
        if e > pos: buf[pos:e] += x[:e - pos] * gain

    for bar in range(bars):
        base = bar * SPB
        for beat in range(4):
            add(kick, base + beat * 4 * S16, K.vary(K.smp(K.KICK), rng, 0.010, 0.06), 0.95)
        for s in (4, 12):
            add(perc, g.pos(base, s, bar) - 0.010 * SR,
                K.vary(K.smp(K.CLAP), rng, 0.02, 0.12), 0.40 * g.vel(s, bar))
        for s in range(16):
            op = (s % 4 == 2)
            sm = K.smp(K.HATO) if op else K.smp(K.HATC)
            add(perc, g.pos(base, s, bar), K.vary(sm, rng, 0.03, 0.26),
                g.vel(s, bar) * (0.30 if s % 2 else 0.20) * (0.7 if op else 1.0))
        for s in range(2, 16, 4):
            add(perc, g.pos(base, s, bar), K.vary(K.smp(K.SHAKER), rng, 0.04, 0.28),
                0.26 * g.vel(s, bar))
        if bar % 2 == 1:
            add(perc, g.pos(base, 10, bar), K.vary(K.smp(K.CONGA_L), rng, 0.03, 0.2), 0.38)
        for s in range(16):
            if g.ghost(s, bar, rng):
                add(perc, g.pos(base, s, bar), K.vary(K.smp(K.HATC), rng, 0.05, 0.4),
                    g.ghost_vel(s, bar))
        # LA VOZ — colocada percusivamente en el grid, no como frase sostenida
        v = voces[bar % len(voces)]
        add(vox, g.pos(base, 0, bar), v, 0.9)
        if bar % 2 == 1:
            add(vox, g.pos(base, 10, bar), voces[(bar + 1) % len(voces)], 0.5)

    st = widen(perc, amount=0.42, seed=seed)
    vx = widen(vox, amount=0.7, seed=seed + 3)
    mix = st * 0.85 + vx * 0.95 + kick[None, :] * 0.95
    mix = np.stack([sat(mix[0], 1.05, 0.02), sat(mix[1], 1.05, 0.02)])
    return sub_mono(mix, 120.0)[:, :bars * SPB]


if __name__ == '__main__':
    fs = sorted(glob.glob(os.path.join(PACK, '*.mp3')))
    print(f'Revisando {len(fs)} chops en busca de vocal…', flush=True)
    cand = []
    for f in fs[::7]:                                     # muestreo, no hacen falta los 4096
        x = dec(f)
        if len(x) < 2000: continue
        cand.append((vocalidad(x), f, x))
    cand.sort(reverse=True, key=lambda c: c[0])
    top = cand[:8]
    print('Los 8 más vocales:')
    for s, f, _ in top:
        print(f'   {s:5.2f}  {os.path.basename(f)[:56]}')

    crudos = [x for _, _, x in top]
    proc = [procesa(x, semis=-5 + (i % 3) * 2, largo_s=0.5 + 0.12 * (i % 3),
                    gate_hz=(0.0 if i % 2 else 11.0)) for i, x in enumerate(crudos)]

    def seguidos(xs, hueco=0.25):
        out = []
        for x in xs:
            out.append(x); out.append(np.zeros(int(hueco * SR), np.float32))
        return np.concatenate(out)

    a = seguidos(crudos)                                  # crudo
    b = seguidos(proc)                                    # procesado
    c = bloque_groove(proc, bars=8)                       # en contexto
    a = np.stack([a, a]); b = np.stack([b, b])

    # TRES ARCHIVOS, no uno con saltos: el seek dentro de un m4a resultó poco
    # confiable en el navegador aunque el archivo esté sano y ya en memoria.
    # Cada botón toca su propio archivo desde cero — más simple y no falla.
    for nombre, y in (('voz-1-crudo', a), ('voz-2-procesado', b), ('voz-3-contexto', c)):
        y = y * (0.86 / max(1e-9, float(np.abs(y).max())))
        wav = os.path.join(OUT, nombre + '.wav'); wav_write(wav, y)
        m4a = os.path.join(OUT, nombre + '.m4a')
        subprocess.run([FF, '-y', '-v', 'error', '-i', wav, '-c:a', 'aac_at', '-b:a', '192k',
                        '-movflags', '+faststart', m4a], check=True)
        os.remove(wav)
        print(f'  {nombre}.m4a  {y.shape[1]/SR:5.1f}s')
    print('\nhttp://localhost:4274/_demo/voz.html')
