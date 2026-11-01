"""Where to cut the chapter title cards (and their spoken announcements) out of the film.

For every chapter card k:
  video: drop original frames v0..v1 (the title card, including the dissolves into
         and out of it); the n frames before v0 dissolve into the n frames after v1
         (both sides are clean shots), so the film loses (v1-v0+1+n) frames.
  audio: drop exactly the same duration, placed in the music-only pauses around the
         announcement: a0..a1 (seconds, original timeline), with an equal-power
         crossfade of C seconds centred on each join. The fades never touch a word.
Word timings come from the narration transcript.
"""
import json, os, sys

FPS = 25
SR = 48000
C = 0.6           # audio crossfade length (s)
GAP_WORD = 0.2    # keep this much clear air after/before neighbouring narration
GAP_CH = 0.1      # and this much around the announcement itself

# video ranges (original frame indices) found by shot analysis
CARDS = [
    dict(ch=1, v0=269,   v1=460,   n=12),   # griffinfly still  -> cypress swamp (kept)
    dict(ch=2, v0=3774,  v1=3922,  n=12),   # fog over forest   -> eroded dry land
    dict(ch=3, v0=7435,  v1=7572,  n=12),   # "THE ATMOSPHERE" Earth (kept) -> wildfire
    dict(ch=4, v0=10748, v1=10887, n=12),   # blueprint dragonfly (kept), dimmed part removed
    dict(ch=5, v0=14660, v1=14802, n=12),   # dragonfly wings + question -> wetland reeds
    dict(ch=6, v0=18056, v1=18217, n=12),   # aerial canopy     -> "A smaller insect..." (kept)
    dict(ch=7, v0=20176, v1=20324, n=12),   # sunlit forest     -> river swamp aerial
]


def plan(transcript_path):
    tr = json.load(open(transcript_path))
    segs = tr["segments"]
    words = [w for s in segs for w in s["words"]]
    out = []
    for c in CARDS:
        t0, t1 = c["v0"] / FPS, (c["v1"] + 1) / FPS
        # the announcement is the transcript sentence that starts with "Chapter"
        # inside the card ("Chapter three, The Invisible Clue." is one sentence even
        # though the narrator pauses at the comma)
        seg = next(sg for sg in segs if sg["text"].strip().lower().startswith("chapter") and t0 - 1 <= sg["start"] <= t1)
        i = next(k for k, w in enumerate(words) if w is seg["words"][0])
        j = next(k for k, w in enumerate(words) if w is seg["words"][-1])
        ch_s, ch_e = words[i]["s"], words[j]["e"]
        prev_e = words[i - 1]["e"] if i > 0 else 0.0
        next_s = words[j + 1]["s"]
        D_frames = c["v1"] - c["v0"] + 1 + c["n"]
        D = D_frames / FPS
        # feasible a1 range, then a0 = a1 - D must also be feasible; take the latest a1
        a1_lo, a1_hi = ch_e + GAP_CH + C / 2, next_s - GAP_WORD - C / 2
        a0_lo, a0_hi = (prev_e + GAP_WORD + C / 2) if i > 0 else C / 2, ch_s - GAP_CH - C / 2
        lo, hi = max(a1_lo, a0_lo + D), min(a1_hi, a0_hi + D)
        assert lo <= hi, (c["ch"], "no room for the audio cut", lo, hi, D)
        a1 = hi
        a0 = a1 - D
        # sample-exact
        a0s = int(round(a0 * SR)); a1s = a0s + D_frames * (SR // FPS)
        out.append(dict(c, D_frames=D_frames, D=D, a0=a0s / SR, a1=a1s / SR, a0s=a0s, a1s=a1s,
                        line=" ".join(w["w"].strip() for w in words[i:j + 1]), ch_s=ch_s, ch_e=ch_e,
                        prev=words[i - 1]["w"].strip() if i > 0 else "", prev_e=prev_e,
                        next=words[j + 1]["w"].strip(), next_s=next_s))
    return out


if __name__ == "__main__":
    W = sys.argv[1]
    P = plan(W + "/work/transcript.json")
    tot = 0
    for p in P:
        tot += p["D_frames"]
        print(f"Ch{p['ch']}: \"{p['line']}\"  spoken {p['ch_s']:.2f}-{p['ch_e']:.2f}")
        print(f"   video drop f{p['v0']}-f{p['v1']} (+{p['n']} dissolve) = {p['D_frames']} frames = {p['D']:.2f}s")
        print(f"   audio drop {p['a0']:.3f}-{p['a1']:.3f}  | prev '{p['prev']}' ends {p['prev_e']:.2f} (fade starts {p['a0'] - C / 2:.2f})"
              f" | next '{p['next']}' starts {p['next_s']:.2f} (fade ends {p['a1'] + C / 2:.2f})")
    print(f"total removed {tot} frames = {tot / FPS:.2f}s -> new length {23048 - tot} frames = {(23048 - tot) / FPS:.2f}s")
    json.dump(P, open(W + "/work/recut_plan.json", "w"), indent=1)
