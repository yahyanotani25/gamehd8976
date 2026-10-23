"""Synthesise the film's original music bed -> audio/music.wav.

A minor, 120 BPM, Am-F-C-G. Sections restart their beat grid on story
beats so the drops land on the picture:

  0.00-2.45   build: filtered groove opening up, pad swell        (grid 0.45)
  2.45-12.74  groove A                                            (grid 2.45)
  12.74       tape stop on "fail"
  12.74-16.46 tension: dark pad, ticking clock, heartbeat kick    (grid 12.74)
  16.46-24.90 groove B on "Breaker"                               (grid 16.46)
  24.90-29.30 outro: brighter, crash on the cut                   (grid 24.90)
  29.30       final chord hit, rings out, fades by 31.0

    python audio/music.py
"""
import os
import numpy as np
from dsp import (SR, secs, noise, exp_env, glide, phase, saw, lp, hp, bp, sweep_filter, sat, pan, reverb,
                 fade, peak_norm, write, adsr, place, db, rng)

HERE = os.path.dirname(os.path.abspath(__file__))
DUR = 31.0
N = int(DUR * SR) + SR * 3  # room for tails; trimmed at the end
BEAT = 0.5
STEP = BEAT / 4
BAR = BEAT * 4

T_DROP, T_FAIL, T_BREAKER, T_OUTRO, T_FINAL = 2.45, 12.74, 16.46, 24.90, 29.30


def midi(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# chords as MIDI notes: pad voicing, bass root, arp tones
CHORDS = {
    'Am': dict(pad=[57, 60, 64, 69], bass=33, arp=[69, 72, 76, 81]),
    'F': dict(pad=[53, 57, 60, 65], bass=29, arp=[65, 69, 72, 77]),
    'C': dict(pad=[55, 60, 64, 67], bass=36, arp=[67, 72, 76, 79]),
    'G': dict(pad=[55, 59, 62, 67], bass=31, arp=[67, 71, 74, 79]),
}
PROG = ['Am', 'F', 'C', 'G']


def bus():
    return np.zeros((N, 2))


# ---------------------------------------------------------------- instruments
def kick(vel=1.0):
    n = int(0.5 * SR)
    body = np.sin(phase(glide(165, 48, n, 9))) * exp_env(n, 0.001, 0.17)
    click = hp(noise(n, 21), 2500) * exp_env(n, 0.0003, 0.004) * 0.4
    return pan(sat(body + click, 1.4) * vel, 0)


def clap(vel=1.0, seed=0):
    n = int(0.45 * SR)
    x = np.zeros(n)
    for i, d in enumerate([0, 0.011, 0.023]):
        k = int(d * SR)
        m = int(0.02 * SR)
        x[k:k + m] += bp(noise(m, 30 + i + seed), 900, 5000) * exp_env(m, 0.0005, 0.006)
    k = int(0.03 * SR)
    x[k:] += bp(noise(n - k, 40 + seed), 1000, 4500) * exp_env(n - k, 0.001, 0.09) * 0.7
    return pan(x * vel, 0.05)


def hat(vel=1.0, open_=False, seed=0, p=0.0):
    n = int((0.35 if open_ else 0.08) * SR)
    x = hp(noise(n, 50 + seed), 7500, 4) * exp_env(n, 0.0005, 0.12 if open_ else 0.018)
    return pan(x * vel, p)


def b808(freq, dur, vel=1.0):
    n = int((dur + 0.15) * SR)
    f = glide(freq * 1.6, freq, n, 40)
    x = np.sin(phase(f)) * adsr(n, 0.003, 0.4, 0.55, 0.12, hold=dur)
    # extra drive so the 808's harmonics carry on phone speakers
    return pan(sat(x * 1.3, 2.8) * vel, 0)


def pluck(freq, vel=1.0, bright=1.0, p=0.0):
    n = int(0.45 * SR)
    x = saw(freq, n, max_h=int(26 * bright), decay_per_h=9 / bright)
    x *= exp_env(n, 0.002, 0.16)
    return pan(x * vel, p)


def pad(notes, dur, cutoff=1500, vel=1.0, seed=0):
    n = int((dur + 0.6) * SR)
    l = np.zeros(n)
    r = np.zeros(n)
    rr = rng(seed)
    for m in notes:
        f = midi(m)
        for det, side in [(-0.11, l), (0.0, None), (0.12, r)]:
            v = saw(f * 2 ** (det / 12), n, max_h=18, t0=rr.random() * 6)
            if side is None:
                l += v * 0.7
                r += v * 0.7
            else:
                side += v
    env = adsr(n, 0.25, 0.6, 0.85, 0.5, hold=dur)
    x = np.stack([lp(l, cutoff, 2), lp(r, cutoff, 2)], axis=1) * env[:, None]
    return x * vel / (len(notes) * 2.4)


def crash(vel=1.0):
    n = int(2.4 * SR)
    x = hp(noise(n, 61), 4500, 2) * exp_env(n, 0.002, 0.7)
    x += bp(noise(n, 62), 3000, 9000) * exp_env(n, 0.002, 0.25) * 0.5
    return pan(x * vel, -0.1) * 0.5 + pan(np.roll(x, 200) * vel, 0.1) * 0.5


def delay(x, t=STEP * 3, fb=0.32, mix=0.35, ping=True):
    out = x.copy()
    d = int(t * SR)
    tap = x.copy()
    for i in range(1, 6):
        tap = np.roll(tap, d, axis=0) * fb
        tap[:d] = 0
        if ping:
            tap = tap[:, ::-1]
        out += tap * mix
    return out


# ---------------------------------------------------------------- arrangement
def groove(buses, start, end, *, intensity=1.0, chord_off=0, filt=None, arp_oct=0, hats16=False, seed=0):
    """Place a groove on buses between start and end, grid starting at start."""
    kb, db_, hb, bb, ab, pb, sc = (buses[k] for k in ('kick', 'drums', 'hats', 'bass', 'arp', 'pad', 'side'))
    bars = int(np.ceil((end - start) / BAR))
    r = rng(seed)
    for b in range(bars):
        t0 = start + b * BAR
        ch = CHORDS[PROG[(b + chord_off) % 4]]
        # pad for the bar
        if t0 < end:
            seg = pad(ch['pad'], min(BAR, end - t0), cutoff=filt or 1700, vel=0.9 * intensity, seed=seed + b)
            place(pb, seg, t0)
        for s in range(16):
            t = t0 + s * STEP
            if t >= end - 1e-6:
                break
            if s in (0, 6, 8) or (s == 11 and b % 2 == 1):
                place(kb, kick(1.0 if s in (0, 8) else 0.8), t)
                place(sc, np.ones((1, 2)), t)  # sidechain trigger marker
            if s in (4, 12):
                place(db_, clap(0.85, seed=s + b), t)
            if s % 2 == 0 or (hats16 and r.random() < 0.6) or (s >= 13 and b % 2 == 1):
                acc = 0.55 if s % 4 == 2 else 0.35
                place(hb, hat(acc * (0.8 + 0.4 * r.random()), seed=int(r.random() * 9), p=0.25), t)
            if s == 14 and b % 2 == 0:
                place(hb, hat(0.35, open_=True, seed=3, p=-0.2), t)
            # 808 follows the kick
            if s in (0, 6, 8) or (s == 11 and b % 2 == 1):
                length = {0: 0.7, 6: 0.22, 8: 0.6, 11: 0.3}[s]
                note = ch['bass'] + (12 if s == 11 else 0)
                place(bb, b808(midi(note), min(length, end - t), 0.95), t)
            # 16th-note pluck arpeggio, up-down through the chord
            pattern = [0, 1, 2, 3, 2, 1, 2, 3]
            m = ch['arp'][pattern[s % 8]] + 12 * arp_oct
            place(ab, pluck(midi(m), (0.5 if s % 4 == 0 else 0.33) * intensity, bright=1.0 + 0.3 * arp_oct, p=(s % 2 - 0.5) * 0.5), t)


def sidechain_env(markers, depth=0.55, release=0.22):
    """Gain curve that ducks on every kick (markers bus holds 1s at kick times)."""
    hits = np.where(markers[:, 0] > 0.5)[0]
    g = np.ones(len(markers))
    tail = int(release * SR * 4)
    curve = 1 - depth * np.exp(-np.arange(tail) / (release * SR))
    for h in hits:
        e = min(len(g), h + tail)
        g[h:e] = np.minimum(g[h:e], curve[: e - h])
    return g[:, None]


def tape_stop(x, at, dur=0.4):
    """Slow the music to a halt starting at `at`, silence after."""
    i0 = int(at * SR)
    n = int(dur * SR)
    rate = np.linspace(1, 0, n) ** 1.5
    pos = i0 + np.cumsum(rate)
    seg = np.stack([np.interp(pos, np.arange(len(x)), x[:, c]) for c in range(2)], axis=1)
    seg *= np.linspace(1, 0, n)[:, None] ** 0.5
    out = x.copy()
    out[i0:] = 0
    out[i0:i0 + n] = seg
    return out


def main():
    names = ('kick', 'drums', 'hats', 'bass', 'arp', 'pad', 'side')
    g = {k: bus() for k in names}

    # build: one bar of groove from 0.45 under a sweeping low-pass
    g_build = {k: bus() for k in names}
    groove(g_build, T_DROP - BAR, T_DROP, intensity=0.8, chord_off=3, seed=1)
    build = sum(g_build[k] for k in ('kick', 'drums', 'hats', 'bass', 'arp')) + g_build['pad']
    i0, i1 = int((T_DROP - BAR) * SR), int(T_DROP * SR)
    t = np.arange(i1 - i0) / (i1 - i0)
    seg = build[i0:i1]
    fc = 250 * (24 ** (t ** 1.6))
    seg = np.stack([sweep_filter(seg[:, c], fc, 'low', q=1.2) for c in range(2)], axis=1)
    build_part = np.zeros_like(build)
    build_part[i0:i1] = seg * np.linspace(0.6, 1.0, i1 - i0)[:, None]

    # grooves
    groove(g, T_DROP, T_FAIL + 0.5, intensity=1.0, seed=2)
    gB = {k: bus() for k in names}
    groove(gB, T_BREAKER, T_OUTRO, intensity=1.0, chord_off=0, seed=3, hats16=True)
    gO = {k: bus() for k in names}
    groove(gO, T_OUTRO, T_FINAL, intensity=1.15, chord_off=0, arp_oct=1, hats16=True, filt=2600, seed=4)

    def mixdown(bs):
        sc = sidechain_env(bs['side'])
        drums = bs['kick'] * 0.85 + bs['drums'] * 0.85 + bs['hats'] * 0.4
        bass = bs['bass'] * 0.42
        arp = delay(hp(bs['arp'], 280), mix=0.3) * 0.42
        padx = bs['pad'] * 1.15
        music = drums + bass * sc + (arp + padx) * sc
        return music, (arp + padx * 0.8 + bs['drums'] * 0.3)

    mA, sendA = mixdown(g)
    mA = tape_stop(mA, T_FAIL, 0.42)
    sendA = tape_stop(sendA, T_FAIL, 0.42)
    mB, sendB = mixdown(gB)
    mO, sendO = mixdown(gO)

    # tension break: dark low pad, heartbeat kick, ticking clock
    tens = bus()
    tlen = T_BREAKER - T_FAIL
    place(tens, fade(pad([45, 52, 57], tlen + 0.2, cutoff=520, vel=1.3, seed=70), 0.6, 0.5), T_FAIL + 0.15)
    for b in range(int(tlen / BEAT) + 1):
        t = T_FAIL + 0.35 + b * BEAT
        if t < T_BREAKER - 0.2:
            place(tens, lp(kick(0.5), 300) * (0.9 if b % 2 == 0 else 0.55), t)
    for s in range(int(tlen / (STEP * 2))):
        t = T_FAIL + 0.3 + s * STEP * 2
        if t < T_BREAKER - 0.05:
            place(tens, hat(0.28 if s % 2 == 0 else 0.16, seed=s % 5, p=0.35 if s % 2 else -0.35), t)
    # reverse swell into the breaker reveal
    sw = pad(CHORDS['Am']['pad'] + [76], 1.3, cutoff=2400, vel=1.6, seed=71)
    sw = reverb(sw, 0.6, dur=1.8, decay=0.6)[: int(1.5 * SR)][::-1]
    place(tens, fade(sw, 0.3, 0.0), T_BREAKER - 1.5)

    # outro crash and the final chord
    fin = bus()
    place(fin, crash(0.9), T_OUTRO)
    place(fin, crash(1.0), T_FINAL)
    place(fin, kick(1.2), T_FINAL)
    place(fin, b808(midi(33), 1.4, 1.0) * 0.7, T_FINAL)
    place(fin, pad(CHORDS['Am']['pad'] + [76, 81], 1.4, cutoff=3200, vel=1.5, seed=80) * 0.8, T_FINAL)
    for i, m in enumerate([69, 72, 76, 81, 84]):
        place(fin, pluck(midi(m), 0.4, bright=1.3, p=(i - 2) * 0.3) * 0.5, T_FINAL + i * 0.06)

    dry = build_part + mA + mB + mO + tens + fin
    # pad swell under the hook
    pre = bus()
    place(pre, fade(pad(CHORDS['Am']['pad'], 2.2, cutoff=700, vel=0.9, seed=91), 0.3, 0.4) * 0.5, 0.0)
    dry += pre
    send = sendA + sendB + sendO + fin * 0.4 + pre * 0.5
    wet = reverb(send, 1.0, dur=2.6, decay=0.75, damp=7000)[:N]
    music = dry + wet * 0.22
    music = hp(music, 28)
    # gentle glue + fade at the very end
    music = sat(music * 0.9, 1.15)
    music = music[: int(DUR * SR)]
    music = fade(music, 0.005, 1.0)
    music = peak_norm(music, -1.0)
    write(os.path.join(HERE, 'music.wav'), music)
    print('music.wav', f'{len(music) / SR:.2f}s')


if __name__ == '__main__':
    main()
