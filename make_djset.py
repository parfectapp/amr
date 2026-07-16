#!/usr/bin/env python3
"""MEGA SET v2 — mezcla de DJ real: las mejores de MONUMENTS × DELIRIO.
Todo beatmatcheado a 121 BPM (atempo), overlaps de 12 compases con
filter-in (lowpass que se abre) en la entrante y EQ-out (highpass progresivo
+ fade equal-power) en la saliente. Como una mixer, no una playlist."""
import os, json, subprocess, wave, sys
import numpy as np, imageio_ffmpeg
import make_tracks as mt

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
FF = imageio_ffmpeg.get_ffmpeg_exe()
TMP = os.path.join(HERE, '_djset_tmp'); os.makedirs(TMP, exist_ok=True)

BPM = 121.0
BAR = 240.0 / BPM                      # 1.983471 s
BARS_S = lambda n: n * BAR
OV = 12                                # overlap: 12 compases (~24 s)

def load_meta(fn):
    s = open(fn).read()
    return json.loads(s[s.index('=') + 1:s.rstrip().rstrip(';').rindex('}') + 1])

tul = load_meta('tulum.js')
TOFF = tul['offsets']; TDUR = tul['dur']

def sh(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-600:]); sys.exit(1)

def load_wav(path):
    w = wave.open(path)
    n = w.getnframes()
    x = np.frombuffer(w.readframes(n), dtype='<i2').astype(np.float32) / 32768.0
    return x.reshape(-1, w.getnchannels()).T.copy()   # (2, N)

# ---------- preparar segmentos ----------
def delirio_seg(name, sec_idx, bars):
    """extrae [offset, offset+bars] del master de DELIRIO (ya a 121)."""
    out = os.path.join(TMP, f'd-{name}.wav')
    if not os.path.exists(out):
        start = TOFF[sec_idx]
        dur = min(BARS_S(bars), TDUR - start)
        sh([FF, '-y', '-v', 'error', '-ss', f'{start:.4f}', '-t', f'{dur:.4f}',
            '-i', 'masters/amr-tulum.wav', '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', out])
    return out

def monuments_seg(name, src_bpm, skip_bars, use_bars):
    """rola de MONUMENTS re-tempada a 121 y recortada [skip, skip+use] bars (post-tempo)."""
    out = os.path.join(TMP, f'm-{name}.wav')
    if not os.path.exists(out):
        ratio = BPM / src_bpm
        full = os.path.join(TMP, f'm-{name}-full.wav')
        sh([FF, '-y', '-v', 'error', '-i', f'masters/amr-{name}.wav',
            '-filter:a', f'atempo={ratio:.6f}', '-ar', '44100', '-ac', '2', '-c:a', 'pcm_s16le', full])
        sh([FF, '-y', '-v', 'error', '-ss', f'{BARS_S(skip_bars):.4f}', '-t', f'{BARS_S(use_bars):.4f}',
            '-i', full, '-c:a', 'pcm_s16le', out])
        os.remove(full)
    return out

# el set: (título, loader, bars_al_aire)
SET = [
    ('LLEGADA',    lambda: delirio_seg('llegada', 0, 96),    96),
    ('PLINTH',     lambda: monuments_seg('001-plinth', 118, 1, 83), 83),
    ('ATLAS',      lambda: delirio_seg('atlas', 1, 112),     112),
    ('MONOLITH',   lambda: monuments_seg('002-monolith', 112, 1, 79), 79),
    ('METRONOMO',  lambda: delirio_seg('metronomo', 4, 112), 112),
    ('VESSEL',     lambda: monuments_seg('003-vessel', 122, 1, 87), 87),
    ('TARDE',      lambda: delirio_seg('tarde', 5, 112),     112),
    ('SINCRONIA',  lambda: delirio_seg('sincronia', 9, 128), 128),
    ('STRATA',     lambda: monuments_seg('004-strata', 116, 1, 85), 85),
    ('PERDIDOS',   lambda: delirio_seg('perdidos', 10, 112), 112),
    ('ADORAR',     lambda: delirio_seg('adorar', 11, 112),   112),
    ('PIANO VIEJO',lambda: delirio_seg('pianoviejo', 13, 128), 128),
    ('AMANECER',   lambda: delirio_seg('amanecer', 15, 999), None),   # hasta el final del álbum
]

def eq_blocks(x, fcs, mode):
    """aplica filtros por bloques iguales sobre x (2,N) — el movimiento de EQ del DJ."""
    n = x.shape[1]; k = len(fcs); bl = n // k
    for i, fc in enumerate(fcs):
        if fc <= 0: continue
        a, b = i * bl, (i + 1) * bl if i < k - 1 else n
        for c in (0, 1):
            x[c, a:b] = (mt.highpass if mode == 'hp' else mt.lowpass)(x[c, a:b], fc)
    return x

def build():
    bar_n = int(round(BAR * SR))
    ovn = OV * bar_n
    print('cargando y procesando %d tracks…' % len(SET), flush=True)
    segs = []
    for title, loader, bars in SET:
        x = load_wav(loader())
        # recortar a compases exactos
        nb = x.shape[1] // bar_n
        x = x[:, :nb * bar_n]
        segs.append((title, x))
        print(f'  {title:12s} {nb:4d} bars  {x.shape[1]/SR:6.1f}s', flush=True)

    total = sum(x.shape[1] for _, x in segs) - ovn * (len(segs) - 1)
    mix = np.zeros((2, total), dtype=np.float32)
    offsets = []
    pos = 0
    for i, (title, x) in enumerate(segs):
        x = x.copy()
        n = x.shape[1]
        if i > 0:                                   # HEAD: filter-in + fade equal-power
            h = min(ovn, n)
            g = np.sin(np.linspace(0, np.pi / 2, h), dtype=np.float32) ** 1.0
            x[:, :h] *= g
            half = h // 2
            x[:, :half] = eq_blocks(x[:, :half], [350, 700, 1400, 2800], 'lp')
        if i < len(segs) - 1:                       # TAIL: EQ-out + fade equal-power
            t_ = min(ovn, n)
            g = np.cos(np.linspace(0, np.pi / 2, t_), dtype=np.float32) ** 1.0
            x[:, -t_:] = eq_blocks(x[:, -t_:], [0, 130, 350, 900], 'hp')
            x[:, -t_:] *= g
        mix[:, pos:pos + n] += x
        offsets.append(round(pos / SR + (BARS_S(OV) if i > 0 else 0), 1))  # donde ya manda la nueva
        pos += n - ovn
        del x
    # master ligero (el material ya está masterizado)
    mix = mt.softclip(mix, 1.05)
    mix /= max(1e-9, np.abs(mix).max()) / 0.89
    dur = total / SR
    print(f'set total: {dur:.1f}s = {dur/60:.1f} min', flush=True)
    wavp = os.path.join(TMP, 'djset.wav')
    with wave.open(wavp, 'w') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((mix.T * 32767).astype('<i2').tobytes())
    # peaks 720
    W = 720; seg = total // W
    mono = np.abs(mix).mean(axis=0)[:seg * W].reshape(W, seg)
    pk = mono.max(axis=1); pk = (pk / pk.max()).round(3).tolist()
    return wavp, dur, offsets, pk

if __name__ == '__main__':
    wavp, dur, offsets, pk = build()
    m4a = os.path.join(HERE, 'audio', 'amr-megaset.m4a')
    sh([FF, '-y', '-v', 'error', '-i', wavp,
        '-af', 'loudnorm=I=-10.5:TP=-1.0:LRA=11',
        '-c:a', 'aac', '-b:a', '160k', '-movflags', '+faststart', m4a])
    print('M4A:', m4a, os.path.getsize(m4a) // 1024 // 1024, 'MB', flush=True)
    titles = [t for t, _, _ in SET]
    meta = dict(id='amr-megaset', title='MEGA SET', kicker='MONUMENTS × DELIRIO · ONE MIX',
                tracks=len(titles), dur=round(dur, 1), titles=titles, offsets=offsets,
                file='audio/amr-megaset.m4a', art='art/amr-megaset.svg', edition=10,
                peaks=pk, bpm=121, key=None)
    with open(os.path.join(HERE, 'megaset.js'), 'w') as f:
        f.write('window.AMR_MEGA=' + json.dumps(meta) + ';')
    print('megaset.js escrito —', len(titles), 'tracks. done', flush=True)
