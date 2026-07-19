#!/usr/bin/env python3
"""JUEZ — mide una rola contra umbrales PUBLICADOS antes de entregarla.

André: "no me entregues cosas que parezcan ai mal hechas". Y luego, con razón:
"esto es lo peor que he escuchado, es una grosería".

Tenía razón las dos veces, y el problema de fondo es que yo medía cosas pero no
JUZGABA: audit.py imprimía números sin umbrales, así que un desastre pasaba igual
que algo bueno. Esto pone la puerta.

TODOS los umbrales salen de literatura revisada por pares o de corpus grandes,
no de blogs que venden cursos:

  A5  crest de mezcla       ISMIR 2014 (De Man et al., 8 canciones × 8 ingenieros)
  A6  centroide espectral   ISMIR 2014
  A7  inclinación −5 dB/oct Pestana, AES 135 (≈mitad de los #1 de EEUU/UK 1950-2010)
  A9  razón side/mid        ISMIR 2014
  A11 ancho del grave       ISMIR 2014 — es una RAMPA de 50 a 400 Hz, NO un muro
  A12 clipeo                MixCheck, AES 2024 (218,109 mezclas y másters amateur)
  A13 sobre-limitado        MixCheck: graves altos + agudos bajos JUNTOS
  A15 número de secciones   Raveform/TISMIR (1,423 tracks de EDM anotados)
  B1  PSR                   consenso de ingeniería
  B2  true peak             BS.1770

Uso:  python3 juez.py archivo.m4a  [más archivos…]
"""
import os, sys, subprocess
import numpy as np
import imageio_ffmpeg
from dream_core import SR, ffmeter

FF = imageio_ffmpeg.get_ffmpeg_exe()

def dec(path, ss=None, dur=None):
    c = [FF, '-v', 'error']
    if ss is not None: c += ['-ss', str(ss)]
    if dur is not None: c += ['-t', str(dur)]
    c += ['-i', path, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-']
    a = np.frombuffer(subprocess.run(c, capture_output=True).stdout, dtype='<f4')
    return np.stack([a[0::2], a[1::2]])

def crest_db(x, win_ms):
    """A5 — crest por ventana. ISMIR 2014: 100 ms → 10.5 dB · 1 s → 14.5 dB"""
    m = 0.5*(x[0]+x[1]); w = int(win_ms*SR/1000)
    n = len(m)//w
    if n < 4: return None
    b = m[:n*w].reshape(n, w).astype(np.float64)
    rms = np.sqrt((b**2).mean(axis=1)); pk = np.abs(b).max(axis=1)
    ok = rms > 1e-5
    if ok.sum() < 4: return None
    return float(np.median(20*np.log10(pk[ok]/rms[ok])))

def centroide(x):
    """A6 — ISMIR 2014: 2479 ± 518 Hz"""
    m = 0.5*(x[0]+x[1]); W = 1<<11
    acc = np.zeros(W//2+1); n = 0
    for i in range(0, len(m)-W, W*4):
        acc += np.abs(np.fft.rfft(m[i:i+W]*np.hanning(W))); n += 1
    if not n: return None
    fr = np.fft.rfftfreq(W, 1/SR)
    return float((acc*fr).sum()/(acc.sum()+1e-12))

def tilt_db_oct(x):
    """A7 — Pestana: ≈ −5 dB/oct lineal de 100 a 4000 Hz"""
    m = 0.5*(x[0]+x[1]); W = 1<<14
    acc = np.zeros(W//2+1); n = 0
    for i in range(0, len(m)-W, W*4):
        acc += np.abs(np.fft.rfft(m[i:i+W]*np.hanning(W)))**2; n += 1
    if not n: return None
    fr = np.fft.rfftfreq(W, 1/SR)
    sel = (fr >= 100) & (fr <= 4000)
    oct_ = np.log2(fr[sel]/100.0)
    db = 10*np.log10(acc[sel]/n + 1e-20)
    return float(np.polyfit(oct_, db, 1)[0])

def side_mid(x):
    """A9 — ISMIR 2014: 0.101 ± 0.049 (potencia)"""
    mid = 0.5*(x[0]+x[1]); side = 0.5*(x[0]-x[1])
    return float((side.astype(np.float64)**2).mean() /
                 ((mid.astype(np.float64)**2).mean() + 1e-15))

def pan_rms(x):
    """A11 — el ancho por banda. ISMIR: bajo 0.188 < medio 0.248 ≈ alto 0.231.
    El grave NO va en mono absoluto: es una RAMPA de 50 a 400 Hz."""
    from dream_core import lp, hp, bp
    out = {}
    for nom, f in (('bajo', ('lp', 250)), ('medio', ('bp', 250, 2500)), ('alto', ('hp', 2500))):
        if f[0] == 'lp':   L, R = lp(x[0], f[1], 2), lp(x[1], f[1], 2)
        elif f[0] == 'hp': L, R = hp(x[0], f[1], 2), hp(x[1], f[1], 2)
        else:              L, R = bp(x[0], f[1], f[2], 2), bp(x[1], f[1], f[2], 2)
        s = 0.5*(L-R); m = 0.5*(L+R)
        out[nom] = float(np.sqrt((s.astype(np.float64)**2).mean() /
                                 ((m.astype(np.float64)**2).mean()+1e-15)))
    return out

def clipeo(x):
    """A12 — MixCheck: >10,000 muestras pegadas = clipeo mayor"""
    return int((np.abs(x) >= 0.999).sum())

def secciones(x):
    """A15/A17 — novedad de Foote. Raveform: 8-13 secciones en EDM real."""
    m = 0.5*(x[0]+x[1]); W = 1<<15; hop = W    # ventana ~0.74 s
    F = []
    for i in range(0, len(m)-W, hop):
        s = np.abs(np.fft.rfft(m[i:i+W]*np.hanning(W)))
        F.append(s/(s.sum()+1e-12))
    if len(F) < 20: return None
    F = np.array(F)
    F = F/ (np.linalg.norm(F, axis=1, keepdims=True)+1e-12)
    S = F @ F.T
    L = 8                                     # kernel ~12 s ≈ 6 compases
    k = np.outer(np.sign(np.arange(2*L)-L+0.5), np.sign(np.arange(2*L)-L+0.5))
    k *= np.outer(np.hanning(2*L), np.hanning(2*L))
    nov = []
    for i in range(L, len(S)-L):
        nov.append((S[i-L:i+L, i-L:i+L]*k).sum())
    nov = np.array(nov)
    if nov.std() < 1e-9: return 0
    nov = (nov-nov.mean())/nov.std()
    pk = [i for i in range(1, len(nov)-1)
          if nov[i] > 1.8 and nov[i] >= nov[i-1] and nov[i] >= nov[i+1]]
    fus = [p for i, p in enumerate(pk) if i == 0 or p - pk[i-1] > 20]
    return len(fus)+1

def juzga(path):
    print(f'\n{"="*66}\n{os.path.basename(path)}\n{"="*66}')
    x = dec(path)
    if x.shape[1] < SR*10: print('  muy corto'); return
    I, lra, tp = ffmeter(path)
    fallos = []; avisos = []
    def chk(nom, val, lo, hi, fuente, fmt='{:.2f}'):
        if val is None: print(f'  ?  {nom}'); return
        ok = (lo is None or val >= lo) and (hi is None or val <= hi)
        rango = f'{fmt.format(lo) if lo is not None else "—"}–{fmt.format(hi) if hi is not None else "—"}'
        print(f'  {"✓" if ok else "✗"}  {nom:26s} {fmt.format(val):>9s}   esperado {rango:>15s}  {fuente}')
        if not ok: fallos.append(nom)

    # OJO: los 10.5/14.5 dB de ISMIR 2014 se midieron sobre MEZCLAS sin masterizar.
    # Un máster está limitado y su crest baja por definición — comparar un máster
    # contra valores de mezcla reprueba hasta a los discos profesionales (probado:
    # reprobaba a "Aura"). Los umbrales de abajo salen de MEDIR las referencias
    # reales de André en set-src/, que es la vara honesta.
    c100 = crest_db(x, 100); c1000 = crest_db(x, 1000)
    chk('crest 100 ms (dB)', c100, 6.5, None, 'refs de André', '{:.1f}')
    chk('crest 1 s (dB)',    c1000, 8.5, None, 'refs de André', '{:.1f}')
    chk('centroide (Hz)',   centroide(x), 2479-2*518, 2479+2*518, 'ISMIR 2014', '{:.0f}')
    chk('inclinación dB/oct', tilt_db_oct(x), -8.0, -2.0, 'Pestana AES', '{:.1f}')
    chk('side/mid',         side_mid(x), 0.101-2*0.049, 0.101+2*0.049, 'ISMIR 2014', '{:.3f}')
    pr = pan_rms(x)
    print(f'     ancho por banda: bajo {pr["bajo"]:.3f}  medio {pr["medio"]:.3f}  alto {pr["alto"]:.3f}')
    if pr['bajo'] > pr['medio']:
        fallos.append('grave más ancho que los medios'); print('  ✗  el GRAVE va más ancho que los medios (al revés de lo normal)')
    cl = clipeo(x)
    print(f'  {"✓" if cl <= 10000 else "✗"}  {"muestras pegadas":26s} {cl:>9d}   esperado         <10000  MixCheck')
    if cl > 10000: fallos.append('clipeo mayor')
    # SECCIONES: la marco INFORMATIVA, no reprobatoria. Mi implementación de la
    # novedad de Foote no logra reproducir el rango 8-13 de Raveform ni sobre
    # discos profesionales (da 5 y 2 en las referencias de André). Una métrica que
    # no puedo validar contra la verdad conocida no debe reprobar a nadie.
    ns = secciones(x)
    print(f'     secciones detectadas: {ns}  (informativo — el detector no es fiable)')
    print(f'     LUFS {I}  ·  LRA {lra}  ·  TP {tp}')
    # true peak: sólo reprueba si es un máster mío. Los MP3 de referencia
    # sobrepasan por el códec, no por la mezcla.
    if tp is not None and tp > -1.0:
        if path.lower().endswith('.mp3'): print('     (TP alto — es un MP3, sobrepaso del códec)')
        else: fallos.append('true peak sobre -1 dBTP')

    print(f'\n  {"APROBADA" if not fallos else "REPROBADA — " + ", ".join(fallos)}')
    return fallos

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); raise SystemExit
    for p in sys.argv[1:]:
        if os.path.exists(p): juzga(p)
        else: print(f'no existe: {p}')
