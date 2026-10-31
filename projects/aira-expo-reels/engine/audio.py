"""Music + SFX mix for a reel, mastered to -14 LUFS integrated / -1 dBTP.

Matches the reference's audio shape:
  * opening: silence, then the music fades in quickly (reference 0.35-0.60 s);
  * logo reveal: a hit as the flare starts (reference 11.30 s, +16 dB over the bed),
    the music runs through the eclipse and fades out as the card appears
    (11.75-11.95 s) - the logo card itself is silent.
"""
import os, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MUSIC_DIR = os.path.join(ROOT, 'audio', 'music')
SFX_DIR = os.path.abspath(os.path.join(ROOT, '..', '..', 'sfx'))
TRACKS = json.load(open(os.path.join(ROOT, 'audio', 'tracks.json')))


def music_file(key):
    """Mixkit tracks are fetched on demand (not stored in the repo: the licence
    allows use in videos, not redistribution of the audio files themselves)."""
    t = TRACKS[key]
    path = os.path.join(MUSIC_DIR, os.path.basename(t['url']))
    if not os.path.exists(path):
        os.makedirs(MUSIC_DIR, exist_ok=True)
        subprocess.run(['curl', '-sS', '-L', '--fail', '-o', path, t['url']], check=True)
    return path


def beat_times(key):
    return TRACKS[key]['beats']


def loudness(path):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', path, '-af', 'loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json',
                        '-f', 'null', '-'], capture_output=True, text=True)
    return json.loads(r.stderr[r.stderr.rfind('{'):r.stderr.rfind('}') + 1])


def mix(out_wav, track, start, total, fade_in=(0.30, 0.15), music_out=None, sfx=()):
    """track: key in tracks.json; start: track time at reel t=0; total: reel length.
    music_out: (t_end, fade) - music is silent from t_end (logo card); None lets
    it run to the end with a 1.2 s fade.
    sfx: [(file in the repo's /sfx, reel time of its peak, peak offset in file, gain dB)]."""
    src = music_file(track)
    fi_st, fi_d = fade_in
    if music_out:
        t_end, fo = music_out
        mf = f'afade=t=out:st={t_end - fo:.3f}:d={fo:.3f}'
        mdur = t_end + 0.05
    else:
        mf = f'afade=t=out:st={total - 1.2:.3f}:d=1.2'
        mdur = total
    inputs = ['-ss', f'{start:.3f}', '-t', f'{mdur:.3f}', '-i', src]
    flt = [f'[0:a]aresample=48000,aformat=channel_layouts=stereo,'
           f'volume=0:enable=lt(t\\,{fi_st:.3f}),afade=t=in:st={fi_st:.3f}:d={fi_d:.3f},{mf}[m]']
    labels = ['[m]']
    for i, (name, t_peak, off, g) in enumerate(sfx, start=1):
        inputs += ['-i', os.path.join(SFX_DIR, name)]
        delay = max(0, int(round((t_peak - off) * 1000)))
        flt.append(f'[{i}:a]aresample=48000,aformat=channel_layouts=stereo,volume={g}dB,'
                   f'adelay={delay}|{delay}[s{i}]')
        labels.append(f'[s{i}]')
    flt.append(f'{"".join(labels)}amix=inputs={len(labels)}:normalize=0:duration=longest,'
               f'apad=whole_dur={total:.3f},atrim=0:{total:.3f}[pre]')
    tmp = out_wav + '.pre.wav'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(flt), '-map', '[pre]',
                    '-c:a', 'pcm_s24le', tmp], check=True)
    m = loudness(tmp)
    ln = (f"loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af', ln + ',aresample=48000', '-c:a', 'pcm_s24le',
                    out_wav], check=True)
    os.remove(tmp)
    return out_wav
