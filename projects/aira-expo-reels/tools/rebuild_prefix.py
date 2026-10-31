"""Rebuild the first N seconds of a Sony XAVC S clip (ILCE-7SM3, HD 100p) from a
prefix of its bytes, without the moov index (Sony writes it at the end).

Why: Google Drive throttles large downloads of the 25 GB footage zip ("quota
exceeded") but still serves small ranges, and zip members are deflate streams, so a
clip can only be read from its start. These files have a fixed layout after the
mdat header, repeating per 48-frame GOP (0.48 s at 100p):

    rtmd metadata   48 x 19456 bytes = 933888   (samples start 00 1c 01 00)
    video           48 access units, AVC length-prefixed NAL units (AUD first)
    audio LPCM      92160 bytes (48 kHz, 2 ch, 16 bit, 0.48 s)

The video NAL units are rewritten as an Annex-B stream, with the SPS/PPS taken
from a complete clip recorded with the same settings, and remuxed to MP4 at 100 fps.

usage:
  rebuild_prefix.py --ref C0001.MP4 --entries zip_entries.json --out raw/ C0142:2.1 C0126:4.0 ...
  rebuild_prefix.py --ref C0001.MP4 --local C0001.MP4 --out /tmp/test C0001:2.4   # self-test
"""
import argparse, json, os, struct, subprocess, sys, time, zlib

# The footage zip's direct-download URL is kept out of the repo (it links to the
# client's raw footage): set AIRA_ZIP_URL, e.g.
#   https://drive.usercontent.google.com/download?id=<file id>&export=download&confirm=t
URL = os.environ.get("AIRA_ZIP_URL", "")
CHUNK = 4 << 20          # Drive still serves 4 MB ranges when larger ones hit the quota
RTMD = 933888
AUDIO = 92160
SIG = b'\x00\x1c\x01\x00'
GOP = 48


BUDGET = [int(os.environ.get('FETCH_BUDGET', '600'))]  # total request cap: be gentle with a throttled file


def fetch(a, b, tries=40):
    for k in range(tries):
        if BUDGET[0] <= 0:
            raise IOError('request budget exhausted')
        BUDGET[0] -= 1
        r = subprocess.run(['curl', '-sS', '-L', '-r', f'{a}-{b}', '-w', '\n%{http_code}', URL], capture_output=True)
        body, _, code = r.stdout.rpartition(b'\n')
        if r.returncode == 0 and code.strip() == b'206' and len(body) == b - a + 1:
            return body
        time.sleep(2.5)
    raise IOError(f'range {a}-{b} failed')


class RemoteMember:
    """Sequentially decompressed zip member, fetched in small verified ranges."""

    def __init__(self, entry):
        hdr = fetch(entry['off'], entry['off'] + 29)
        nl, xl = struct.unpack('<HH', hdr[26:30])
        self.pos = entry['off'] + 30 + nl + xl
        self.end = self.pos + entry['csize'] - 1
        self.dec = zlib.decompressobj(-15) if entry['method'] == 8 else None
        self.buf = bytearray()
        self.fetched = 0

    def ensure(self, n):
        while len(self.buf) < n and self.pos <= self.end:
            b = fetch(self.pos, min(self.end, self.pos + CHUNK - 1))
            self.pos += len(b)
            self.fetched += len(b)
            self.buf += self.dec.decompress(b) if self.dec else b
        return len(self.buf) >= n


class LocalMember:
    def __init__(self, path):
        self.buf = open(path, 'rb').read()
        self.fetched = 0

    def ensure(self, n):
        return len(self.buf) >= n


def ref_param_sets(ref_mp4):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', ref_mp4, '-map', '0:v:0', '-c', 'copy', '-bsf:v',
                          'h264_mp4toannexb', '-frames:v', '1', '-f', 'h264', '-'], capture_output=True, check=True).stdout
    out, i = [], 0
    starts = []
    while True:
        j = raw.find(b'\x00\x00\x01', i)
        if j < 0:
            break
        starts.append(j + 3)
        i = j + 3
    for k, s in enumerate(starts):
        e = (starts[k + 1] - 3) if k + 1 < len(starts) else len(raw)
        nal = raw[s:e].rstrip(b'\x00')
        if nal and (nal[0] & 0x1f) in (7, 8):
            out.append(nal)
    assert out, 'no SPS/PPS in reference'
    return out


def mdat_start(m):
    m.ensure(1 << 20)
    i = 0
    while True:
        sz, typ = struct.unpack('>I4s', m.buf[i:i + 8])
        hdr = 8
        if sz == 1:
            sz = struct.unpack('>Q', m.buf[i + 8:i + 16])[0]
            hdr = 16
        if typ == b'mdat':
            return i + hdr
        i += sz


def rebuild(m, seconds, ps, h264_path):
    q = mdat_start(m)
    gops_needed = int(seconds / 0.48) + 2
    with open(h264_path, 'wb') as f:
        f.write(b''.join(b'\x00\x00\x00\x01' + p for p in ps))
        for g in range(gops_needed):
            if not m.ensure(q + RTMD + 16):
                return g
            assert m.buf[q:q + 4] == SIG and m.buf[q + 19456:q + 19460] == SIG, f'rtmd signature missing at GOP {g}'
            q += RTMD
            aus = 0
            nals = []
            while True:
                if not m.ensure(q + 8):
                    return g
                L = struct.unpack('>I', m.buf[q:q + 4])[0]
                t = m.buf[q + 4] & 0x1f
                if t == 9:
                    if aus == GOP:
                        raise ValueError('more than 48 access units in a GOP chunk')
                    aus += 1
                m.ensure(q + 4 + L + AUDIO + 8)
                nals.append(bytes(m.buf[q + 4:q + 4 + L]))
                q += 4 + L
                if aus == GOP and m.buf[q + AUDIO:q + AUDIO + 4] == SIG \
                        and m.buf[q + AUDIO + 19456:q + AUDIO + 19460] == SIG:
                    break
            f.write(b''.join(b'\x00\x00\x00\x01' + n for n in nals))
            q += AUDIO
    return gops_needed


def remux(h264_path, mp4_path):
    """A raw Annex-B stream carries no timestamps and a plain remux gets the B-frame
    order wrong, so decode it in the decoder's own (presentation) order and re-encode
    to a visually lossless intermediate with clean 100 fps timestamps."""
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-f', 'h264', '-i', h264_path, '-fps_mode', 'passthrough',
                            '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-'], stdout=subprocess.PIPE)
    enc = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', '1920x1080',
                          '-r', '100', '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '8', '-g', '50',
                          '-bf', '0', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709',
                          '-color_range', 'tv', mp4_path], stdin=dec.stdout)
    dec.wait()
    if enc.returncode or dec.returncode:
        raise RuntimeError('remux failed')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', required=True)
    ap.add_argument('--entries')
    ap.add_argument('--local')
    ap.add_argument('--out', required=True)
    ap.add_argument('clips', nargs='+')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    ps = ref_param_sets(a.ref)
    entries = {os.path.basename(e['name']): e for e in json.load(open(a.entries))} if a.entries else {}
    for spec in a.clips:
        clip, secs = spec.split(':')
        secs = float(secs)
        t0 = time.time()
        m = LocalMember(a.local) if a.local else RemoteMember(entries[clip + '.MP4'])
        h264 = os.path.join(a.out, clip + '.prefix.h264')
        g = rebuild(m, secs, ps, h264)
        mp4 = os.path.join(a.out, clip + '.MP4')
        remux(h264, mp4 + '.tmp.mp4')
        os.replace(mp4 + '.tmp.mp4', mp4)
        os.remove(h264)
        json.dump(dict(clip=clip, gops=g, seconds=g * 0.48, fetched_bytes=m.fetched,
                       note='prefix rebuild (no audio): see tools/rebuild_prefix.py'),
                  open(os.path.join(a.out, clip + '.prefix.json'), 'w'))
        print(f'{clip}: {g} GOPs = {g * 0.48:.2f}s, fetched {m.fetched / 1e6:.1f} MB, {time.time() - t0:.0f}s', flush=True)


if __name__ == '__main__':
    main()
