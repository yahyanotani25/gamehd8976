"""Synthesise the SFX palette into audio/sfx/ and write palette.json.

Each entry records `hit`: the offset (s) of the sound's transient or peak,
which the mixer lines up with the cue time. The owner's own whoosh, click
and drone come from the repo's sfx/ library.

    python audio/sfx.py
"""
import json
import os
import numpy as np
from dsp import (SR, secs, noise, exp_env, glide, phase, saw, lp, hp, bp, sweep_filter, sat, to_stereo,
                 pan, reverb, fade, peak_norm, write, read, trim_silence, db, adsr, rng)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'sfx')
LIB = os.path.abspath(os.path.join(HERE, '..', '..', '..', 'sfx'))  # repo-level owner library


def sine_drop(f0, f1, dur, decay, curve=6):
    n = int(dur * SR)
    return np.sin(phase(glide(f0, f1, n, curve))) * exp_env(n, 0.001, decay)


def pop():
    # glossy "plop": a quick pitch-dropping sine + a tiny click, short room
    n = int(0.16 * SR)
    body = sine_drop(1150, 380, 0.16, 0.045, curve=9)
    click = hp(noise(n, 1), 3000) * exp_env(n, 0.0005, 0.004) * 0.35
    x = body * 0.9 + click
    return peak_norm(reverb(to_stereo(x, 0.15), 0.12, dur=0.5, decay=0.12), -3), 0.002


def grow():
    # rising zip as a candle forms: band-swept noise + an upward sine, soft tick at the end
    dur = 0.26
    n = int(dur * SR)
    t = secs(dur)
    fc = 600 * (8 ** (t / dur))
    zip_ = sweep_filter(noise(n, 2), fc, 'band', q=4) * np.sin(np.pi * t / dur) ** 1.5
    tone = np.sin(phase(glide(260, 900, n, 2))) * np.sin(np.pi * t / dur) * 0.35
    tick = np.zeros(n)
    k = int(0.22 * SR)
    tick[k:k + 400] = hp(noise(400, 3), 2500) * exp_env(400, 0.0003, 0.003)
    x = zip_ * 1.4 + tone + tick * 0.8
    return peak_norm(reverb(to_stereo(x, 0.3), 0.15, dur=0.6, decay=0.15), -4), 0.0


def tick():
    n = int(0.05 * SR)
    x = bp(noise(n, 4), 2200, 7000) * exp_env(n, 0.0003, 0.006)
    x += np.sin(2 * np.pi * 2600 * secs(0.05)) * exp_env(n, 0.0005, 0.01) * 0.4
    return peak_norm(reverb(to_stereo(x), 0.1, dur=0.4, decay=0.08), -6), 0.001


def impact():
    # punchy cinematic hit: pitched sub thump + transient + low-mid body + tail
    dur = 1.4
    n = int(dur * SR)
    sub = sine_drop(140, 42, dur, 0.32, curve=7)
    body = lp(noise(n, 5), 900) * exp_env(n, 0.001, 0.09) * 0.9
    snap = bp(noise(n, 6), 1500, 9000) * exp_env(n, 0.0005, 0.025) * 0.8
    x = sat(sub * 1.1 + body + snap, 1.6)
    return peak_norm(reverb(to_stereo(x, 0.2), 0.22, dur=1.6, decay=0.45), -1), 0.003


def boom():
    # heavy downbeat: deep sub drop with distortion + rumble
    dur = 2.6
    n = int(dur * SR)
    sub = sine_drop(95, 28, dur, 0.85, curve=4)
    rumble = lp(noise(n, 7), 220) * exp_env(n, 0.005, 0.6) * 1.2
    snap = bp(noise(n, 8), 800, 6000) * exp_env(n, 0.0005, 0.04) * 0.9
    x = sat(sub * 1.3 + rumble + snap, 2.2)
    return peak_norm(reverb(to_stereo(x, 0.25), 0.25, dur=2.4, decay=0.8), -1), 0.004


def crack():
    # glass crack: sharp transient, scattered bright shards and ringing partials
    dur = 1.2
    n = int(dur * SR)
    r = rng(9)
    x = bp(noise(n, 10), 1800, 12000) * exp_env(n, 0.0003, 0.02) * 1.2
    for k in range(70):
        at = int((r.random() ** 2.2) * 0.45 * SR)
        m = int(0.012 * SR)
        if at + m < n:
            x[at:at + m] += bp(noise(m, 100 + k), 2500, 11000) * exp_env(m, 0.0002, 0.003) * (0.9 - at / n)
    # short glassy pings scattered through the first 0.3 s
    for k in range(24):
        f = 3000 + r.random() * 7000
        at = int((r.random() ** 1.5) * 0.3 * SR)
        m = int(0.12 * SR)
        x[at:at + m] += np.sin(2 * np.pi * f * secs(0.12)) * exp_env(m, 0.0005, 0.015 + r.random() * 0.03) * 0.18
    out = np.zeros((n, 2))
    out += pan(x * 0.7, -0.3) + pan(np.roll(x, 37) * 0.7, 0.3)
    return peak_norm(reverb(out, 0.3, dur=1.5, decay=0.4), -2), 0.0


def stamp():
    dur = 0.6
    n = int(dur * SR)
    thump = sine_drop(110, 55, dur, 0.09, curve=8)
    slap = bp(noise(n, 11), 500, 3500) * exp_env(n, 0.0005, 0.03)
    x = sat(thump * 1.2 + slap * 0.9, 1.5)
    return peak_norm(reverb(to_stereo(x, 0.1), 0.18, dur=0.7, decay=0.18), -2), 0.002


def bell(f, dur, decay, seed=0):
    t = secs(dur)
    # harmonic 2:1 FM keeps it a clean bell rather than a clang
    mod = np.sin(2 * np.pi * f * 2.0 * t) * 0.9 * np.exp(-t / (decay * 0.35))
    x = np.sin(2 * np.pi * f * t + mod) * np.exp(-t / decay)
    x += np.sin(2 * np.pi * f * 2.01 * t) * np.exp(-t / (decay * 0.4)) * 0.25
    return x


def ding():
    # positive UI chime: two bright FM bell notes a fifth apart
    dur = 2.6
    n = int(dur * SR)
    x = bell(1318.5, dur, 0.5)
    y = np.zeros(n)
    k = int(0.055 * SR)
    y[k:] = bell(1975.5, dur, 0.55)[: n - k]
    out = pan(x, -0.15) + pan(y * 0.8, 0.2)
    return peak_norm(reverb(out, 0.35, dur=1.8, decay=0.5), -4), 0.002


def blip():
    # radar-ish ping with two echoes
    dur = 0.9
    n = int(dur * SR)
    t = secs(0.09)
    p = np.sin(phase(glide(1500, 1900, len(t), 3))) * exp_env(len(t), 0.002, 0.03)
    x = np.zeros(n)
    for i, (d, g) in enumerate([(0, 1), (0.16, 0.45), (0.32, 0.2)]):
        k = int(d * SR)
        x[k:k + len(p)] += p * g
    return peak_norm(reverb(to_stereo(x, 0.2), 0.25, dur=1.0, decay=0.3), -6), 0.002


def swipe():
    # quick air swish peaking at 0.12 s
    dur = 0.32
    n = int(dur * SR)
    t = secs(dur)
    fc = 900 * (6 ** (t / dur))
    env = np.exp(-((t - 0.12) / 0.06) ** 2)
    x = sweep_filter(noise(n, 12), fc, 'band', q=1.4) * env * 2.2
    return peak_norm(reverb(pan(x, -0.2) + pan(np.roll(x, 90), 0.25), 0.15, dur=0.6, decay=0.15), -4), 0.12


def flip():
    # card flip: two fast air swishes and a plastic click as it lands
    dur = 0.55
    n = int(dur * SR)
    t = secs(dur)
    fc = 1400 + 2600 * np.sin(np.pi * np.clip(t / 0.4, 0, 1))
    env = np.exp(-((t - 0.1) / 0.05) ** 2) + 0.8 * np.exp(-((t - 0.26) / 0.05) ** 2)
    x = sweep_filter(noise(n, 13), fc, 'band', q=1.6) * env * 1.8
    k = int(0.4 * SR)
    m = int(0.03 * SR)
    x[k:k + m] += bp(noise(m, 14), 1500, 6000) * exp_env(m, 0.0003, 0.005) * 1.3
    x[k:k + m] += np.sin(2 * np.pi * 900 * secs(0.03)) * exp_env(m, 0.0005, 0.008) * 0.5
    return peak_norm(reverb(pan(x, 0.15) + pan(np.roll(x, 60), -0.15), 0.18, dur=0.6, decay=0.16), -4), 0.05


def shimmer():
    # gold sparkle: a cascade of tiny high pings
    dur = 1.6
    n = int(dur * SR)
    r = rng(15)
    out = np.zeros((n, 2))
    notes = [2093, 2637, 3136, 3951, 4186, 5274, 6272]
    for k in range(26):
        at = int((k / 26) ** 1.3 * 0.55 * SR)
        f = notes[int(r.random() * len(notes))] * (1 + (r.random() - 0.5) * 0.004)
        m = int(0.5 * SR)
        if at + m > n:
            continue
        p = np.sin(2 * np.pi * f * secs(0.5)) * exp_env(m, 0.001, 0.06 + r.random() * 0.1) * (1 - k / 30)
        out[at:at + m] += pan(p, r.random() * 1.6 - 0.8)
    return peak_norm(reverb(out, 0.45, dur=2.0, decay=0.6, damp=9000), -6), 0.004


def riser():
    # 1.1 s build that ends exactly at the cue: rising filtered noise + pitch sweep
    dur = 1.1
    n = int(dur * SR)
    t = secs(dur)
    k = (t / dur) ** 2.2
    fc = 300 * (40 ** (t / dur))
    nz = sweep_filter(noise(n, 16), fc, 'band', q=1.1) * k * 1.6
    tone = saw(glide(110, 880, n, 1.2), n, max_h=12) * k * 0.25
    x = nz + lp(tone, 4000)
    x = fade(x, 0, 0.01)
    out = pan(x, -0.1) + pan(np.roll(x, 120), 0.1)
    return peak_norm(out, -4), dur


def final():
    # the closing hit: impact + boom + shimmer layered
    a, _ = impact()
    b, _ = boom()
    c, _ = shimmer()
    n = max(len(a), len(b), len(c))
    out = np.zeros((n, 2))
    out[: len(a)] += a * 0.9
    out[: len(b)] += b * 0.8
    out[: len(c)] += c * 0.6
    return peak_norm(out, -1), 0.004


def owner(name, hit, gain_db=0.0):
    x = read(os.path.join(LIB, name))
    return peak_norm(x * db(gain_db), -1), hit


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    gens = dict(pop=pop, grow=grow, tick=tick, impact=impact, boom=boom, crack=crack, stamp=stamp, ding=ding,
                blip=blip, swipe=swipe, flip=flip, shimmer=shimmer, riser=riser, final=final)
    palette = {}
    for name, g in gens.items():
        x, hit = g()
        x = trim_silence(x, -80)
        write(os.path.join(OUT, f'{name}.wav'), x)
        palette[name] = {'file': f'{name}.wav', 'hit': round(hit, 4), 'dur': round(len(x) / SR, 3), 'source': 'synth'}
    # the owner's library: whoosh peaks 0.894 s in, click's first hit 0.158 s,
    # the drone is silent for its first 5.29 s
    for name, f, hit in [('whoosh', 'whoosh.mp3', 0.894), ('click', 'click-double.mp3', 0.158), ('drone', 'low-drone.mp3', 5.29)]:
        x, h = owner(f, hit)
        write(os.path.join(OUT, f'{name}.wav'), x)
        palette[name] = {'file': f'{name}.wav', 'hit': h, 'dur': round(len(x) / SR, 3), 'source': f'owner sfx/{f}'}
    with open(os.path.join(OUT, 'palette.json'), 'w') as fh:
        json.dump(palette, fh, indent=1)
    for k, v in palette.items():
        print(f"{k:8s} hit {v['hit']:.3f}s  dur {v['dur']:.2f}s  {v['source']}")
