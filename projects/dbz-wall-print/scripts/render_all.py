"""Render all frames with N worker processes (interleaved), resumable."""
import sys, os, subprocess
S = sys.argv[1]; out = sys.argv[2]; nw = int(sys.argv[3]) if len(sys.argv) > 3 else 4
os.makedirs(out, exist_ok=True)
todo = [t for t in range(896) if not os.path.exists(f"{out}/{t:04d}.png")]
procs = []
for k in range(nw):
    part = todo[k::nw]
    if not part: continue
    lst = ",".join(str(t) for t in part)
    procs.append(subprocess.Popen([sys.executable, "-I", os.path.join(os.path.dirname(os.path.abspath(__file__)), "compositor.py"), S, out, lst + ","],
                                  stdout=open(f"{out}/../render_{k}.log", "w"), stderr=subprocess.STDOUT))
for p in procs: p.wait()
missing = [t for t in range(896) if not os.path.exists(f"{out}/{t:04d}.png")]
print("done; missing", len(missing), missing[:10])
