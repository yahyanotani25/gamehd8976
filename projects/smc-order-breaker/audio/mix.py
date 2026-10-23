"""Mix the voice-over, music bed and SFX cues into the film's soundtrack.

    python audio/mix.py [--out ../out/mix.wav]

Inputs: data/vo.mp3 (the owner's voice-over), audio/music.wav,
audio/sfx/*.wav + palette.json, audio/cues.json (node audio/collect_cues.mjs).
Writes stems next to the mix (vo/music/sfx) for later rebalancing.
"""
import argparse
import json
import os
import subprocess
import numpy as np
import pyloudnorm as pyln
import scipy.signal as ss
from dsp import SR, read, write, place, repitch, db, fade, hp

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DUR = 31.0

# Target loudness of each sound at its loudest moment (momentary, 400 ms
# LUFS), before the cue's own gain. The voice sits around -16 LUFS.
TARGET = dict(final=-16, impact=-20, boom=-20, whoosh=-22, stamp=-23, ding=-24, crack=-24, riser=-25,
              shimmer=-27, flip=-27, swipe=-27, click=-27, blip=-27, drone=-27, pop=-30, grow=-31, tick=-34)
VO_LUFS = -16.0
MUSIC_LUFS = -25.0      # music bed loudness before ducking
DUCK_DB = 7.0           # extra music reduction while the voice speaks
DRONE_END = 16.46       # the tension drone gives way to the breaker reveal


def lufs(x):
    return pyln.Meter(SR).integrated_loudness(x)


def peak_momentary(x, name):
    """Loudest 400 ms window of a sound (the drone: of its audible part)."""
    if name == 'drone':
        x = x[int(5.3 * SR):int(9.0 * SR)]
    w = int(0.4 * SR)
    if len(x) < w:
        x = np.concatenate([x, np.zeros((w - len(x), 2))])
    m = pyln.Meter(SR, block_size=0.4)
    vals = [m.integrated_loudness(x[i:i + w]) for i in range(0, len(x) - w + 1, int(0.05 * SR)) if np.abs(x[i:i + w]).max() > 1e-5]
    return max(vals)


def master_vo(src, dst):
    chain = ('highpass=f=75,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3400:t=q:w=1.2:g=2.5,'
             'equalizer=f=9500:t=h:w=0.7:g=2,deesser=i=0.35,'
             'acompressor=threshold=-22dB:ratio=3:attack=4:release=90:makeup=2,aresample=48000')
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', src, '-af', chain, '-ac', '2',
                    '-c:a', 'pcm_f32le', dst], check=True)


def envelope(x, attack=0.03, release=0.28):
    """Peak-follower envelope of a stereo signal, 0..1 relative to its max."""
    a = np.abs(x).max(axis=1)
    win = int(0.02 * SR)
    a = np.sqrt(np.convolve(a ** 2, np.ones(win) / win, 'same'))
    ka, kr = np.exp(-1 / (attack * SR)), np.exp(-1 / (release * SR))
    # run the one-pole follower on a decimated signal for speed, then upsample
    step = 48
    d = a[::step]
    e = np.zeros_like(d)
    for i in range(1, len(d)):
        k = ka ** step if d[i] > e[i - 1] else kr ** step
        e[i] = k * e[i - 1] + (1 - k) * d[i]
    e = np.interp(np.arange(len(a)), np.arange(len(d)) * step, e)
    return e / (e.max() + 1e-9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(ROOT, 'out', 'mix.wav'))
    ap.add_argument('--cues', default=os.path.join(HERE, 'cues.json'))
    args = ap.parse_args()
    out_dir = os.path.dirname(os.path.abspath(args.out))
    os.makedirs(out_dir, exist_ok=True)
    n = int(DUR * SR)

    # voice-over
    vo_path = os.path.join(out_dir, 'vo_master.wav')
    master_vo(os.path.join(ROOT, 'data', 'vo.mp3'), vo_path)
    vo = np.zeros((n, 2))
    place(vo, read(vo_path), 0.0)
    vo *= db(VO_LUFS - lufs(vo))

    # music, ducked under the voice
    music = np.zeros((n, 2))
    place(music, read(os.path.join(HERE, 'music.wav')), 0.0)
    music *= db(MUSIC_LUFS - lufs(music))
    # carve a little room for the voice
    music = music - 0.25 * ss.sosfilt(ss.butter(2, [1500, 4000], 'band', fs=SR, output='sos'), music, axis=0)
    env = np.clip(envelope(vo) * 2.2, 0, 1)
    music *= db(-DUCK_DB * env)[:, None]

    # sfx
    palette = json.load(open(os.path.join(HERE, 'sfx', 'palette.json')))
    cues = json.load(open(args.cues))
    sfx = np.zeros((n, 2))
    cache = {}
    for c in cues:
        name = c['sfx']
        if name not in cache:
            raw = read(os.path.join(HERE, 'sfx', palette[name]['file']))
            cache[name] = raw * db(TARGET.get(name, -28) - peak_momentary(raw, name))
        x = repitch(cache[name], c.get('pitch', 0))
        k = 2 ** (c.get('pitch', 0) / 12)
        hit = palette[name]['hit'] / k
        x = x * db(c.get('gain', 0))
        if name == 'drone':
            # play from the cue until the breaker reveal (or the cue's dur), fading out
            end = c.get('dur', max(0.5, DRONE_END - c['t']))
            x = x[: int((hit + end) * SR)]
            x = fade(x, 0, min(0.6, end / 2))
        place(sfx, x, c['t'] - hit)

    mix = vo + music + sfx
    for name, stem in (('vo', vo), ('music', music), ('sfx', sfx)):
        write(os.path.join(out_dir, f'stem_{name}.wav'), stem)
    pre = os.path.join(out_dir, 'premix.wav')
    write(pre, mix)

    # master: glue compression, limiter, loudness to -14 LUFS / -1 dBTP (two-pass loudnorm)
    chain = 'acompressor=threshold=-18dB:ratio=2:attack=10:release=150:makeup=1,alimiter=limit=0.95:attack=3:release=50'
    meas = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', pre, '-af', chain + ',loudnorm=I=-14:TP=-1.0:LRA=9:print_format=json',
                           '-f', 'null', '-'], capture_output=True, text=True).stderr
    j = json.loads(meas[meas.rindex('{'):meas.rindex('}') + 1])
    ln = (f"loudnorm=I=-14:TP=-1.0:LRA=9:measured_I={j['input_i']}:measured_TP={j['input_tp']}:"
          f"measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', pre, '-af', chain + ',' + ln + ',aresample=48000',
                    '-c:a', 'pcm_s24le', args.out], check=True)
    print(f'{len(cues)} cues -> {args.out}')
    print('stem loudness: vo %.1f, music %.1f, sfx %.1f LUFS' % (lufs(vo), lufs(music), lufs(sfx) if np.any(sfx) else -99))


if __name__ == '__main__':
    main()
