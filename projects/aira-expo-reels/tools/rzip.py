"""Remote zip reader over HTTP range requests (curl-backed)."""
import sys, io, zipfile, subprocess, json, os

# The footage zip's direct-download URL is kept out of the repo (it links to the
# client's raw footage): set AIRA_ZIP_URL, e.g.
#   https://drive.usercontent.google.com/download?id=<file id>&export=download&confirm=t
URL = os.environ.get("AIRA_ZIP_URL", "")
SIZE = 25184400915

def fetch(start, end):
    out = subprocess.run(["curl", "-sS", "-L", "--retry", "5", "-r", f"{start}-{end}", URL],
                         capture_output=True, check=True).stdout
    if len(out) != end - start + 1:
        raise IOError(f"short read {len(out)} vs {end-start+1}")
    return out

class RangeFile(io.RawIOBase):
    def __init__(self, size, block=1 << 20):
        self.size, self.pos, self.block, self.cache = size, 0, block, {}
    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos
    def _blk(self, i):
        if i not in self.cache:
            s = i * self.block
            e = min(self.size, s + self.block) - 1
            self.cache[i] = fetch(s, e)
        return self.cache[i]
    def read(self, n=-1):
        if n is None or n < 0: n = self.size - self.pos
        n = min(n, self.size - self.pos)
        out = bytearray()
        while n > 0:
            i, o = divmod(self.pos, self.block)
            b = self._blk(i)[o:o + n]
            out += b; self.pos += len(b); n -= len(b)
        return bytes(out)
    def readinto(self, buf):
        d = self.read(len(buf)); buf[:len(d)] = d; return len(d)

if __name__ == "__main__":
    rf = RangeFile(SIZE)
    zf = zipfile.ZipFile(rf)
    rows = []
    for zi in zf.infolist():
        rows.append(dict(name=zi.filename, size=zi.file_size, csize=zi.compress_size,
                         method=zi.compress_type, off=zi.header_offset, date=list(zi.date_time)))
    json.dump(rows, open(sys.argv[1], "w"), indent=1)
    print(len(rows), "entries")
