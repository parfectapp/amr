#!/usr/bin/env python3
"""Publica FICCIÓN (single sci-fi): m4a + ficcion.js."""
import os, json, subprocess
import numpy as np, imageio_ffmpeg
from dream_core import ffmeter, ffdecode, SR

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'masters', 'amr-ficcion.wav')

def enc(src, dst):
    subprocess.run([FF, '-y', '-v', 'error', '-i', src, '-c:a', 'aac_at', '-b:a', '256k',
                    '-movflags', '+faststart', dst], check=True)

def peaks(path, W=360):
    raw = subprocess.run([FF, '-v', 'error', '-i', path, '-ac', '1', '-ar', '4410',
                          '-f', 'f32le', '-'], capture_output=True).stdout
    x = np.abs(np.frombuffer(raw, dtype='<f4'))
    seg = len(x) // W
    pk = x[:seg * W].reshape(W, seg).max(axis=1)
    return (pk / (pk.max() or 1)).round(3).tolist()

if __name__ == '__main__':
    m4a = os.path.join(HERE, 'audio', 'amr-ficcion.m4a')
    enc(SRC, m4a)
    I, lra, tp = ffmeter(m4a)
    dur = round(len(ffdecode(m4a, mono=True)) / SR, 1)
    meta = dict(id='amr-ficcion', title='FICCIÓN', kicker='THE SINGLE · SCI-FI DISCO',
                dur=dur, file='audio/amr-ficcion.m4a', art='art/ficcion.svg',
                edition=20, bpm=127, key='D MIN', peaks=peaks(m4a))
    with open(os.path.join(HERE, 'ficcion.js'), 'w') as f:
        f.write('window.AMR_FICCION=' + json.dumps(meta) + ';')
    print(f'ficcion.js · {dur}s · {I} LUFS · LRA {lra} · TP {tp} · {os.path.getsize(m4a)//1048576} MB')
