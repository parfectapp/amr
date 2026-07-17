#!/usr/bin/env python3
"""dream_core.py — núcleo DSP del motor v2 (post-auditoría).

Arregla con física, no con fe, los cinco defectos medidos en el catálogo:
  1. hueco de medios (10-20% en 150Hz-2k vs 25-40% en refs) → saturación por etapas
  2. mono absoluto (width 0.000)                            → descorrelación L/R banda-limitada
  3. LRA 1.0 (ladrillo)                                     → macro-dinámica (trabajo del builder)
  4. -12 LUFS con true peak +9.8                            → master: ganancia global + limitador
  5. timbre chiptune                                        → drift/detune/saturación (builder)

El banco de pruebas (__main__) imprime números MEDIDOS; para loudness el juez
es el ebur128 de ffmpeg (BS.1770 real), no mi aproximación.
"""
import os, subprocess, struct
import numpy as np, imageio_ffmpeg

FF = imageio_ffmpeg.get_ffmpeg_exe()
SR = 44100

# ------------------------------------------------------------------ util audio
def ffdecode(path, mono=False):
    cmd = [FF, '-v', 'error', '-i', path, '-ac', '1' if mono else '2',
           '-ar', str(SR), '-f', 'f32le', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    x = np.frombuffer(raw, dtype='<f4')
    return x if mono else np.ascontiguousarray(x.reshape(-1, 2).T)

def wav_write(path, LR):
    """WAV float32 estéreo sin depender del módulo wave (que sólo hace int)."""
    LR = np.asarray(LR, dtype=np.float32)
    inter = np.empty(LR.shape[1] * 2, dtype='<f4')
    inter[0::2] = LR[0]; inter[1::2] = LR[1]
    data = inter.tobytes()
    with open(path, 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + len(data)) + b'WAVE')
        f.write(b'fmt ' + struct.pack('<IHHIIHH', 16, 3, 2, SR, SR * 8, 8, 32))
        f.write(b'data' + struct.pack('<I', len(data)))
        f.write(data)

def ffmeter(path):
    """LUFS-I, LRA, true peak — medidos por ffmpeg (la verdad, no mi estimado)."""
    out = subprocess.run([FF, '-hide_banner', '-i', path, '-af', 'ebur128=peak=true',
                          '-f', 'null', '-'], capture_output=True, text=True).stderr
    tail = out[-2000:]
    def grab(sec, key):
        seg = tail.split(sec, 1)
        if len(seg) < 2: return None
        for ln in seg[1].splitlines()[:4]:
            if key in ln:
                try: return float(ln.split(key)[1].split()[0])
                except ValueError: return None
        return None
    return (grab('Integrated loudness', 'I:'),
            grab('Loudness range', 'LRA:'),
            grab('True peak', 'Peak:'))

# ------------------------------------------------------------------ FIR + OLA
_FIRS = {}

def fir_from_gain(gain_fn, ntaps=4097):
    """FIR fase lineal desde una curva de magnitud (muestreo + ventana)."""
    nfft = 1 << 14
    f = np.fft.rfftfreq(nfft, 1 / SR)
    H = gain_fn(f).astype(np.float64)
    h = np.fft.irfft(H, nfft)
    h = np.roll(h, ntaps // 2)[:ntaps] * np.hanning(ntaps)
    return h.astype(np.float32)

def fconv(x, h, align=0):
    """Convolución overlap-add por bloques (memoria plana aunque x sea de 8 min)."""
    x = np.asarray(x, dtype=np.float32)
    lh = len(h)
    N = 1 << 17
    step = N - lh + 1
    H = np.fft.rfft(h, N)
    y = np.zeros(len(x) + lh - 1, dtype=np.float32)
    for i in range(0, len(x), step):
        seg = x[i:i + step]
        y[i:i + len(seg) + lh - 1] += np.fft.irfft(np.fft.rfft(seg, N) * H, N)[:len(seg) + lh - 1].astype(np.float32)
    return y[align:align + len(x)]

def _filt(x, kind, *args):
    key = (kind,) + args
    if key not in _FIRS:
        if kind == 'lp':
            fc, o = args; g = lambda f: 1 / np.sqrt(1 + (f / max(fc, 1.0)) ** (2 * o))
        elif kind == 'hp':
            fc, o = args; g = lambda f: 1 / np.sqrt(1 + (max(fc, 1.0) / np.maximum(f, 1e-6)) ** (2 * o))
        else:
            f1, f2, o = args
            g = lambda f: (1 / np.sqrt(1 + (np.maximum(f1, 1.0) / np.maximum(f, 1e-6)) ** (2 * o))
                           / np.sqrt(1 + (f / max(f2, 1.0)) ** (2 * o)))
        _FIRS[key] = fir_from_gain(g)
    h = _FIRS[key]
    return fconv(x, h, align=len(h) // 2)

def lp(x, fc, order=4):  return _filt(x, 'lp', float(fc), int(order))
def hp(x, fc, order=4):  return _filt(x, 'hp', float(fc), int(order))
def bp(x, f1, f2, order=4): return _filt(x, 'bp', float(f1), float(f2), int(order))

# ------------------------------------------------------------------ saturación
def sat(x, drive=2.4, asym=0.15):
    """tanh con término cuadrático: impares + pares. El DC del término par se quita."""
    x = np.asarray(x, dtype=np.float32)
    y = x + asym * x * x
    y = np.tanh(drive * y)
    y -= y.mean()
    return (y / np.tanh(drive)).astype(np.float32)

def sat_warm(x, d1=1.7, d2=2.6):
    """dos etapas con LP entre medio — armónicos que se re-saturan, como en análogo."""
    a = sat(x, d1, 0.14)
    a = lp(a, 9000, 2)
    return sat(a, d2, 0.08)

# ------------------------------------------------------------------ estéreo
def _decorr_ir(seed, ms=22.0):
    """IR de magnitud ~plana y fase aleatoria: descorrelaciona sin colorear."""
    n = int(SR * ms / 1000)
    rng = np.random.default_rng(seed)
    ph = rng.uniform(-np.pi, np.pi, n // 2 + 1)
    ph[0] = 0.0
    h = np.fft.irfft(np.exp(1j * ph), n) * np.hanning(n)
    h /= np.sqrt((h ** 2).sum()) + 1e-12
    return h.astype(np.float32)

def widen(x, amount=0.5, lo=220.0, hi=11000.0, seed=7):
    """mono → estéreo: lateral descorrelacionada, banda-limitada (el sub no se toca)."""
    d = fconv(x, _decorr_ir(seed)) - fconv(x, _decorr_ir(seed + 101))
    side = bp(d, lo, hi) * (amount * 0.5)
    return np.stack([x + side, x - side])

def sub_mono(LR, fc=120.0):
    """el low end SIEMPRE al centro: highpass al canal lateral y recombina."""
    m = 0.5 * (LR[0] + LR[1]); s = 0.5 * (LR[0] - LR[1])
    s = hp(s, fc, 4)
    return np.stack([m + s, m - s])

def pingpong(x, beat_s, fb=0.42, mix=0.22, taps=7, damp=4200.0, seed=0):
    """delay 3/8 alternando L/R con LP progresivo — el 'dub delay' del género."""
    d = int(beat_s * 0.75 * SR)
    L = np.array(x, dtype=np.float32); R = np.array(x, dtype=np.float32)
    tap = np.asarray(x, dtype=np.float32)
    for k in range(1, taps + 1):
        tap = lp(tap, damp, 2) * fb
        sh = np.zeros_like(x); sh[k * d:] = tap[:len(x) - k * d] if k * d < len(x) else 0
        if k % 2 == 1: R += sh * mix
        else:          L += sh * mix
    return np.stack([L, R])

def stereo_verb(x, decay_s=2.2, mix=0.16, tone=5200.0, seed=3):
    """reverb estéreo barata: dos IRs de ruido exponencial descorrelacionadas."""
    n = int(decay_s * SR)
    out = []
    for i, sd in enumerate((seed, seed + 77)):
        rng = np.random.default_rng(sd)
        ir = rng.standard_normal(n).astype(np.float32) * np.exp(-np.linspace(0, 6.5, n)).astype(np.float32)
        ir = lp(ir, tone, 2)
        ir /= np.sqrt((ir ** 2).sum()) + 1e-12
        out.append(x + fconv(x, ir) * mix * 3.2)
    return np.stack(out)

# ------------------------------------------------------------------ limitador
def limit(LR, ceiling_db=-1.3, look_ms=5.0, rel_ms=160.0, dec=32):
    """limitador lookahead con envolvente diezmada (rápido) + tanh de seguridad."""
    c = 10 ** (ceiling_db / 20)
    LR = np.asarray(LR, dtype=np.float32)
    pk = np.max(np.abs(LR), axis=0)
    n = len(pk)
    nb = n // dec + 1
    pkb = np.zeros(nb, dtype=np.float32)
    full = (n // dec) * dec
    if full:
        pkb[:n // dec] = pk[:full].reshape(-1, dec).max(axis=1)
    if full < n:
        pkb[-1] = pk[full:].max()
    look_b = max(1, int(look_ms / 1000 * SR / dec))
    from numpy.lib.stride_tricks import sliding_window_view
    padded = np.concatenate([pkb, np.full(look_b, pkb[-1] if nb else 0, dtype=np.float32)])
    envb = sliding_window_view(padded, look_b + 1).max(axis=1)[:nb]
    gt = np.minimum(1.0, c / np.maximum(envb, 1e-9))
    rel = np.exp(-dec / (SR * rel_ms / 1000))
    g = np.empty(nb, dtype=np.float32)
    prev = 1.0
    for i in range(nb):                      # nb = n/32 → barato incluso en sets largos
        v = gt[i]
        prev = v if v < prev else prev * rel + v * (1 - rel)
        g[i] = prev
    gain = np.interp(np.arange(n), np.arange(nb) * dec + dec / 2, g).astype(np.float32)
    y = LR * gain[None, :]
    return (c * np.tanh(y / c)).astype(np.float32)

def _master_pass(in_wav, out_wav, gain, ceiling_db, chunk_s=30.0, ctx_s=1.0):
    ctx = int(ctx_s * SR)
    carry = np.zeros((2, 0), dtype=np.float32)
    tmp = out_wav + '.pcm'
    with open(tmp, 'wb') as f:
        for xs in _stream_wav(in_wav, chunk_s):
            blk = np.concatenate([carry, xs * gain], axis=1)
            y = limit(blk, ceiling_db)
            skip = carry.shape[1]
            f.write(_interleave(y[:, skip:]))
            carry = blk[:, -ctx:] if blk.shape[1] > ctx else blk
    _pcm_to_wav(tmp, out_wav)
    os.remove(tmp)

def master_file(in_wav, out_wav, target_i=-8.0, ceiling_db=-1.3, max_pass=5):
    """master en streaming: ganancia global + limit(), ITERANDO — el limitador se
    come loudness, así que se re-mide y se sobre-compensa (1.4x) hasta clavar el target."""
    I0, _, _ = ffmeter(in_wav)
    gain = 10 ** ((target_i - I0) / 20)
    hist = [I0]
    for _ in range(max_pass):
        _master_pass(in_wav, out_wav, gain, ceiling_db)
        I1, _, _ = ffmeter(out_wav)
        hist.append(I1)
        if I1 is None or abs(I1 - target_i) < 0.3:
            break
        gain *= 10 ** (1.4 * (target_i - I1) / 20)
    return hist

def _stream_wav(path, chunk_s):
    cmd = [FF, '-v', 'error', '-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    nb = int(chunk_s * SR) * 2 * 4
    try:
        while True:
            raw = p.stdout.read(nb)
            if not raw: break
            x = np.frombuffer(raw, dtype='<f4')
            m = len(x) // 2
            if not m: break
            yield np.ascontiguousarray(x[:m * 2].reshape(-1, 2).T)
    finally:
        p.stdout.close(); p.wait()

def _interleave(LR):
    inter = np.empty(LR.shape[1] * 2, dtype='<f4')
    inter[0::2] = LR[0]; inter[1::2] = LR[1]
    return inter.tobytes()

def _pcm_to_wav(pcm, wav):
    size = os.path.getsize(pcm)
    with open(wav, 'wb') as f:
        f.write(b'RIFF' + struct.pack('<I', 36 + size) + b'WAVE')
        f.write(b'fmt ' + struct.pack('<IHHIIHH', 16, 3, 2, SR, SR * 8, 8, 32))
        f.write(b'data' + struct.pack('<I', size))
        with open(pcm, 'rb') as src:
            while True:
                b = src.read(1 << 20)
                if not b: break
                f.write(b)

# ------------------------------------------------------------------ métricas
def spectrum_pct(x):
    win = 1 << 15
    acc = np.zeros(win // 2 + 1); c = 0
    for i in range(0, len(x) - win, win * 2):
        acc += np.abs(np.fft.rfft(x[i:i + win] * np.hanning(win))); c += 1
    fr = np.fft.rfftfreq(win, 1 / SR); tot = acc.sum() or 1
    B = [('sub', 20, 60), ('bass', 60, 150), ('lowmid', 150, 500),
         ('mid', 500, 2000), ('himid', 2000, 6000), ('air', 6000, 16000)]
    return {n: round(float(acc[(fr >= a) & (fr < b)].sum() / tot * 100), 1) for n, a, b in B}

def width_corr(LR):
    L, R = LR[0].astype(np.float64), LR[1].astype(np.float64)
    m = (L + R) / 2; s = (L - R) / 2
    w = float((s ** 2).mean() / ((m ** 2).mean() + 1e-12))
    corr = float(np.corrcoef(L, R)[0, 1])
    Lb, Rb = lp(L.astype(np.float32), 110, 4), lp(R.astype(np.float32), 110, 4)
    cs = float(np.corrcoef(Lb.astype(np.float64), Rb.astype(np.float64))[0, 1])
    return round(w, 3), round(corr, 3), round(cs, 3)

# ------------------------------------------------------------------ banco de pruebas
if __name__ == '__main__':
    import tempfile
    rng = np.random.default_rng(1)
    t8 = np.arange(8 * SR) / SR

    print('== 1. SATURACIÓN: ¿pone presencia (500Hz-4k) un bajo filtrado tipo motor viejo? ==')
    f0 = 82.41
    saw = ((f0 * t8) % 1.0 * 2 - 1).astype(np.float32) * 0.5
    old = lp(saw, 300, 4)                       # así sonaba el bajo del motor viejo
    new = sat_warm(hp(old, 25, 2) * 2.2) * 0.5  # mismo bajo, corrido caliente
    def presencia(x):
        s = spectrum_pct(x)
        return s['mid'] + s['himid']
    po, pn = presencia(old), presencia(new)
    print(f'   viejo: presencia {po:.1f}%  |  saturado: {pn:.1f}%   {"OK" if pn > po * 2 and pn > 10 else "FALLA"}')

    print('== 2. ESTÉREO: widen (bus) + sub mono (mezcla) ==')
    perc = rng.standard_normal(8 * SR).astype(np.float32) * (np.sin(2 * np.pi * 2 * t8) > 0.7)
    kick = np.sin(2 * np.pi * 50 * t8).astype(np.float32) * 0.5
    bus = widen(perc * 0.3, amount=0.55)
    wb, cb, _ = width_corr(bus)
    LR = sub_mono(bus + kick[None, :], 120)
    w, c, cs = width_corr(LR)
    ok = 0.05 <= wb <= 0.35 and cs > 0.97
    print(f'   bus: width={wb} corr={cb}  |  mezcla: width={w} corr_sub={cs}   {"OK" if ok else "FALLA"}')

    print('== 3. MASTER: mezcla callada → -8 LUFS sin clipear ==')
    mix = (sat_warm(saw * 0.8) * 0.25 + perc * 0.12 + kick * 0.3)
    env = 0.55 + 0.45 * np.sin(2 * np.pi * t8 / 8.0) ** 2     # algo de macro-dinámica
    LRm = widen(mix * env.astype(np.float32) * 0.12, amount=0.4)
    tmpd = tempfile.mkdtemp()
    raw_w = os.path.join(tmpd, 'raw.wav'); out_w = os.path.join(tmpd, 'mst.wav')
    wav_write(raw_w, LRm)
    hist = master_file(raw_w, out_w, target_i=-8.0, ceiling_db=-1.3)
    I1, lra1, tp1 = ffmeter(out_w)
    ok = I1 is not None and abs(I1 - (-8.0)) < 0.7 and tp1 is not None and tp1 <= -0.8
    print(f'   pasos {hist} → {I1} LUFS, TP {tp1} dBTP   {"OK" if ok else "FALLA"}')
    print('listo')
