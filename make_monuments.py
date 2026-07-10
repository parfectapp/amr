#!/usr/bin/env python3
# AMR — el vinilo completo de MONUMENTS: las 5 rolas encadenadas + masterizado + portada vinilo.
import os, subprocess, json, re, wave
import numpy as np, imageio_ffmpeg
import make_set

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
ROLAS = ['amr-001-plinth','amr-002-monolith','amr-003-vessel','amr-004-strata','amr-005-ghost']
TITLES = ['TINTO','BARRICA','COSECHA','RESERVA','POSO']
WAVS = [os.path.join(HERE,'masters',r+'.wav') for r in ROLAS]
OUT_WAV = os.path.join(HERE,'masters','amr-monuments-side.wav')
M4A = os.path.join(HERE,'audio','amr-monuments-side.m4a')
XF = 2.5

MASTER = ("highpass=f=24,equalizer=f=55:t=q:w=0.9:g=1.5,equalizer=f=200:t=q:w=1.4:g=-2,"
          "equalizer=f=9000:t=h:w=0.7:g=2,acompressor=threshold=-16dB:ratio=2:attack=25:release=250:makeup=2,"
          "loudnorm=I=-11:TP=-1.0:LRA=11,alimiter=level_out=0.97:limit=0.97")

def build():
    n=len(WAVS); parts=[]
    for i in range(n):
        parts.append(f'[{i}:a]aresample=44100,aformat=channel_layouts=stereo[a{i}]')
    prev='a0'
    for i in range(1,n):
        out='mix' if i==n-1 else f'x{i}'
        parts.append(f'[{prev}][a{i}]acrossfade=d={XF}:c1=tri:c2=tri[{out}]'); prev=out
    fg=';'.join(parts)+f';[mix]{MASTER}[m]'
    cmd=[FF,'-y']
    for w in WAVS: cmd+=['-i',w]
    cmd+=['-filter_complex',fg,'-map','[m]','-c:a','pcm_s16le',OUT_WAV]
    return cmd

if __name__=='__main__':
    print('Encadenando + masterizando MONUMENTS…', flush=True)
    r=subprocess.run(build(), capture_output=True, text=True)
    if r.returncode!=0: print(r.stderr[-2500:]); raise SystemExit(1)
    info=subprocess.run([FF,'-i',OUT_WAV],capture_output=True,text=True).stderr
    m=re.search(r'Duration: (\d+):(\d+):(\d+)',info); secs=int(m.group(1))*3600+int(m.group(2))*60+int(m.group(3))
    subprocess.run([FF,'-y','-i',OUT_WAV,'-c:a','aac','-b:a','160k',M4A],capture_output=True)
    print(f'WAV {secs//60}:{secs%60:02d}  m4a {os.path.getsize(M4A)//1024//1024}MB')
    w=wave.open(OUT_WAV); x=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(float).reshape(-1,2).mean(axis=1)
    W=720; seg=len(x)//W; pk=np.abs(x[:seg*W]).reshape(W,seg).max(axis=1); pk=(pk/pk.max()).round(3).tolist()
    meta=dict(id='amr-monuments-side', title='MONUMENTS', kicker='THE EP', tracks=5, dur=secs,
              titles=TITLES, file='audio/amr-monuments-side.m4a', art='art/amr-monuments-side.png', edition=50, peaks=pk)
    open(os.path.join(HERE,'monuments.js'),'w').write('window.AMR_MON='+json.dumps(meta)+';\n')
    make_set.make_cover(pk, 5, secs, title='MONUMENTS', kicker='THE EP', out='amr-monuments-side')
    print('monuments.js + portada vinilo OK — dur', f'{secs//60}:{secs%60:02d}')
