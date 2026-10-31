"""Bulk pass: extract each clip from the remote zip, build a review proxy, keep originals within a budget."""
import sys, json, os, subprocess, threading, queue, shutil, time
sys.path.insert(0, os.path.dirname(__file__))
from rget import extract

SP = sys.argv[1]
entries = json.load(open(os.path.join(SP, 'listing/entries.json')))
byname = {os.path.basename(e['name']): e for e in entries}
RAW = os.path.join(SP, 'raw'); PRX = os.path.join(SP, 'proxy'); XML = os.path.join(SP, 'raw_xml')
for d in (RAW, PRX, XML): os.makedirs(d, exist_ok=True)
BUDGET = float(sys.argv[2]) * 1e9 if len(sys.argv) > 2 else 20e9
lock = threading.Lock()
kept = sum(os.path.getsize(os.path.join(RAW, f)) for f in os.listdir(RAW) if f.endswith('.MP4'))
log = open(os.path.join(SP, 'bulk.log'), 'a')

def L(*a):
    with lock:
        print(time.strftime('%H:%M:%S'), *a, file=log, flush=True)

clips = sorted(n for n in byname if n.endswith('.MP4'))
xmls = sorted(n for n in byname if n.endswith('.XML'))
q = queue.Queue()
for c in clips:
    if not os.path.exists(os.path.join(PRX, c[:-4] + '.mp4')):
        q.put(c)

def worker():
    global kept
    while True:
        try: c = q.get_nowait()
        except queue.Empty: return
        stem = c[:-4]
        prx = os.path.join(PRX, stem + '.mp4')
        orig = os.path.join(RAW, c)
        try:
            if not os.path.exists(prx):
                if not os.path.exists(orig):
                    extract(byname[c], orig)
                subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', orig, '-map', '0:v:0', '-map', '0:a:0?',
                                '-vf', 'fps=25,scale=640:360:flags=bicubic', '-c:v', 'libx264', '-preset', 'veryfast',
                                '-crf', '26', '-g', '25', '-c:a', 'aac', '-b:a', '64k', '-ac', '1',
                                prx + '.tmp.mp4'], check=True)
                os.replace(prx + '.tmp.mp4', prx)
            if os.path.exists(orig):
                sz = os.path.getsize(orig)
                with lock:
                    keep = kept + sz <= BUDGET
                    if keep: kept += sz
                if not keep:
                    os.remove(orig)
                L('done', c, 'kept' if keep else 'proxy-only', f'{kept/1e9:.1f}GB')
            else:
                L('done', c, 'proxy-only (prev)')
        except Exception as ex:
            L('FAIL', c, repr(ex))

# sidecars first (tiny)
for x in xmls:
    if not os.path.exists(os.path.join(XML, x)):
        try: extract(byname[x], os.path.join(XML, x))
        except Exception as ex: L('FAIL', x, repr(ex))
L('xml done', len(xmls))
ts = [threading.Thread(target=worker) for _ in range(3)]
for t in ts: t.start()
for t in ts: t.join()
L('ALL DONE')
