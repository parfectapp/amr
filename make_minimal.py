#!/usr/bin/env python3
# AMR — MINIMAL SET: ~1h de las pistas más minimal/hipnóticas del catálogo, en azul.
# Selecciona por bajo brillo (menos agudos = más deep/dub/minimal), transiciones largas.
import os, subprocess, re, json, sys
import numpy as np, imageio_ffmpeg
import make_set, make_sesion

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'session-src')
OUT_WAV = os.path.join(HERE, 'masters', 'amr-minimal.wav')
M4A = os.path.join(HERE, 'audio', 'amr-minimal.m4a')
XF = 10.0                       # transiciones largas, hipnóticas
TARGET = 60*60                  # ~1 hora
EXCLUDE = ['wish you were here']
BLUE='#2E6FB0'; BLUE_LT='#5B9BD5'; BLUE_DK='#1a4a7a'

def build_cmd(order):
    n=len(order); parts=[]
    for i in range(n):
        parts.append(f'[{i}:a]aresample=44100,aformat=channel_layouts=stereo,dynaudnorm=f=220:g=10[a{i}]')
    prev='a0'
    for i in range(1,n):
        out='premix' if i==n-1 else f'x{i}'
        parts.append(f'[{prev}][a{i}]acrossfade=d={XF}:c1=tri:c2=tri[{out}]'); prev=out
    master=("highpass=f=24,equalizer=f=50:t=q:w=0.9:g=1.2,equalizer=f=250:t=q:w=1.3:g=-1.5,"
            "equalizer=f=7000:t=h:w=0.7:g=1,acompressor=threshold=-17dB:ratio=2:attack=30:release=280:makeup=2,"
            "loudnorm=I=-12:TP=-1.0:LRA=12,alimiter=level_out=0.96:limit=0.96")
    parts.append(f'[premix]{master}[m]')
    cmd=[FF,'-y']
    for t in order: cmd+=['-i',t['path']]
    cmd+=['-filter_complex',';'.join(parts),'-map','[m]','-c:a','pcm_s16le',OUT_WAV]
    return cmd

if __name__=='__main__':
    FINAL = '--finalize' in sys.argv
    files=sorted([os.path.join(SRC,f) for f in os.listdir(SRC) if f.endswith('.mp3')])
    files=[f for f in files if not any(x in os.path.basename(f).lower() for x in EXCLUDE)]
    print(f'Analizando {len(files)} pistas…', flush=True)
    tracks=[]
    for f in files:
        a=make_sesion.analyze(f); d=make_sesion.dur_of(f)
        if d<60: continue
        tracks.append(dict(path=f, title=make_sesion.clean_title(f), dur=d, **a))
    # selección MINIMAL: menor brillo primero (más deep/hipnótico), hasta ~1h
    tracks.sort(key=lambda t: t['bright'])
    sel=[]; tot=0
    for t in tracks:
        if tot >= TARGET: break
        sel.append(t); tot += t['dur']
    # orden dentro del set: arco suave de energía
    order=make_sesion.arc_order(sel)
    total=sum(t['dur'] for t in order)-XF*(len(order)-1)
    print(f'MINIMAL SET — {len(order)} pistas, ~{int(total//60)} min:', flush=True)
    for i,t in enumerate(order): print(f'  {i+1:2d}. {t["title"][:34]:34s} bright={t["bright"]:.3f} e={t["rms"]:.3f}', flush=True)

    if not FINAL:
        print('\nMezclando…', flush=True)
        r=subprocess.run(build_cmd(order), capture_output=True, text=True)
        if r.returncode!=0: print(r.stderr[-3000:]); raise SystemExit(1)
    secs=int(make_sesion.dur_of(OUT_WAV))
    br=max(96, min(160, int(95*1024*1024*8/secs/1000)))
    if not FINAL or not os.path.exists(M4A):
        subprocess.run([FF,'-y','-i',OUT_WAV,'-c:a','aac','-b:a',f'{br}k',M4A], capture_output=True)
    print(f'WAV {secs//60}:{secs%60:02d} · m4a {br}k = {os.path.getsize(M4A)//1024//1024} MB', flush=True)
    off=[0.0]
    for i in range(1,len(order)):
        off.append(round(max(0, off[-1]+order[i-1]['dur']-XF),1))
    raw=subprocess.run([FF,'-v','quiet','-i',OUT_WAV,'-ac','1','-ar','2000','-f','f32le','-'],capture_output=True).stdout
    x=np.frombuffer(raw,dtype='<f4'); W=720; seg=max(1,len(x)//W)
    pk=np.abs(x[:seg*W]).reshape(W,seg).max(axis=1); pk=(pk/(pk.max() or 1)).round(3).tolist()
    meta=dict(id='amr-minimal', title='MINIMAL SET', kicker='DEEP & HYPNOTIC', tracks=len(order),
              dur=secs, titles=[t['title'] for t in order], offsets=off,
              file='audio/amr-minimal.m4a', art='art/amr-minimal.png', edition=10, peaks=pk, color='blue')
    open(os.path.join(HERE,'minimal.js'),'w').write('window.AMR_MIN='+json.dumps(meta, ensure_ascii=False)+';\n')
    make_set.make_cover(pk, len(order), secs, title='MINIMAL SET', kicker='DEEP & HYPNOTIC', out='amr-minimal',
                        accent=BLUE, accent_lt=BLUE_LT, accent_dk=BLUE_DK)
    print(f'minimal.js + portada azul OK — {secs//60}:{secs%60:02d}', flush=True)
