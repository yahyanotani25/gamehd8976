"""Extract selected entries from the remote zip via HTTP range requests.
usage: rget.py entries.json outdir name1 [name2 ...]   (names relative, e.g. C0001.MP4)
"""
import sys, json, os, struct, subprocess, zlib
# The footage zip's direct-download URL is kept out of the repo (it links to the
# client's raw footage): set AIRA_ZIP_URL, e.g.
#   https://drive.usercontent.google.com/download?id=<file id>&export=download&confirm=t
URL = os.environ.get("AIRA_ZIP_URL", "")

def fetch(start, end):
    out = subprocess.run(["curl", "-sS", "-L", "--retry", "8", "--retry-all-errors", "-r", f"{start}-{end}", URL],
                         capture_output=True, check=True).stdout
    if len(out) != end - start + 1:
        raise IOError(f"short read {len(out)} vs {end-start+1}")
    return out

def extract(e, outpath):
    hdr = fetch(e['off'], e['off'] + 29)
    sig, ver, flag, meth, t, d, crc, cs, us, nl, xl = struct.unpack('<IHHHHHIIIHH', hdr)
    assert sig == 0x04034b50, hex(sig)
    data_start = e['off'] + 30 + nl + xl
    data_end = data_start + e['csize'] - 1
    tmp = outpath + '.part'
    if e['method'] == 0:
        cmd = ["curl", "-sS", "-L", "--retry", "8", "--retry-all-errors", "-r", f"{data_start}-{data_end}", URL, "-o", tmp]
        subprocess.run(cmd, check=True)
    else:
        dec = zlib.decompressobj(-15)
        p = subprocess.Popen(["curl", "-sS", "-L", "--retry", "8", "-r", f"{data_start}-{data_end}", URL], stdout=subprocess.PIPE)
        crcv = 0; n = 0
        with open(tmp, 'wb') as f:
            while True:
                chunk = p.stdout.read(4 << 20)
                if not chunk: break
                o = dec.decompress(chunk)
                crcv = zlib.crc32(o, crcv); n += len(o); f.write(o)
            o = dec.flush(); crcv = zlib.crc32(o, crcv); n += len(o); f.write(o)
        if p.wait() != 0: raise IOError('curl failed')
        if n != e['size']: raise IOError(f"size mismatch {n} vs {e['size']}")
        if e.get('crc') is not None and crcv != e['crc']: raise IOError('crc mismatch')
    os.replace(tmp, outpath)

if __name__ == '__main__':
    entries = {os.path.basename(x['name']): x for x in json.load(open(sys.argv[1]))}
    outdir = sys.argv[2]; os.makedirs(outdir, exist_ok=True)
    for name in sys.argv[3:]:
        op = os.path.join(outdir, name)
        if os.path.exists(op): continue
        extract(entries[name], op)
        print('ok', name, flush=True)
