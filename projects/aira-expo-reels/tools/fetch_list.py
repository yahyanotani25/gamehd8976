"""Download a list of Drive video files once Drive serves them, then make review proxies.

The list file (kept outside the repo, it holds Drive file IDs) has one clip per line:
    KEY  ID1  [ID2 ...]      ('-' = no id); each ID is tried in order (e.g. a copy, then the original)

Works in rounds: each round asks Drive once per remaining clip (Drive answers "Quota
exceeded" / a sign-in redirect while a file is blocked) and downloads the ones it
serves, as closed ranges into OUT/KEY.MP4 (resumable via .part, checked against the
size Drive reports); then waits --wait seconds. Exits 0 when every clip is on disk,
3 after --max-wait seconds with clips still blocked, 2 if free disk would fall under
--min-free GB.

  python3 tools/fetch_list.py LIST OUT [--proxy-dir DIR] [--wait 900] [--max-wait 7000]
"""
import argparse, os, shutil, subprocess, sys, time
import requests

URL = 'https://drive.usercontent.google.com/download?id={}&export=download&confirm=t'
CHUNK = 32 << 20
S = requests.Session()


def log(*a):
    print(time.strftime('%H:%M:%S'), *a, flush=True)


def get(fid, a, b, tries=6):
    """bytes a..b of a Drive file -> (content, total) or (None, reason)"""
    reason = 'error'
    for k in range(tries):
        try:
            r = S.get(URL.format(fid), headers={'Range': f'bytes={a}-{b}'}, timeout=120, allow_redirects=False)
            if r.status_code == 206 and 'text/html' not in r.headers.get('Content-Type', ''):
                return r.content, int(r.headers['Content-Range'].split('/')[-1])
            if r.status_code in (301, 302, 303):
                return None, 'private (sign-in redirect)'
            if 'Quota exceeded' in r.text[:400]:
                return None, 'quota exceeded'
            reason = f'http {r.status_code}'
        except requests.RequestException as e:
            reason = type(e).__name__
        time.sleep(2 * (k + 1))
    return None, reason


def proxy(src, dst):
    """640 px long side, keyframe every 10 frames, for contact sheets / face framing"""
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf',
                    "scale='if(gt(iw,ih),640,-2)':'if(gt(iw,ih),-2,640)'", '-an', '-c:v', 'libx264',
                    '-preset', 'veryfast', '-crf', '23', '-g', '10', dst], check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('list')
    ap.add_argument('out')
    ap.add_argument('--proxy-dir')
    ap.add_argument('--wait', type=int, default=900)
    ap.add_argument('--max-wait', type=int, default=7000)
    ap.add_argument('--min-free', type=float, default=1.5)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.proxy_dir:
        os.makedirs(a.proxy_dir, exist_ok=True)
    rows = []
    for line in open(a.list):
        p = line.split()
        if p:
            rows.append((p[0], [i for i in p[1:] if i != '-']))
    t_start = time.time()
    while True:
        todo = [(k, ids) for k, ids in rows if not os.path.exists(os.path.join(a.out, k + '.MP4'))]
        if not todo:
            log('all done')
            return
        got, why = 0, {}
        for k, ids in todo:
            r = fetch(k, ids, a)
            if r == 'space':
                sys.exit(2)
            if r == 'done':
                got += 1
                if a.proxy_dir:
                    proxy(os.path.join(a.out, k + '.MP4'), os.path.join(a.proxy_dir, k + '.mp4'))
            else:
                why[r] = why.get(r, 0) + 1
        left = len(todo) - got
        log(f'round: {got} downloaded, {left} still blocked ' + str(why))
        if left == 0:
            continue
        if time.time() - t_start + a.wait > a.max_wait:
            log('giving up for now')
            sys.exit(3)
        time.sleep(a.wait)


def fetch(k, ids, a):
    """download one clip from the first id that serves it -> 'done' | 'space' | reason"""
    dst = os.path.join(a.out, k + '.MP4')
    part = dst + '.part'
    reason = 'no id'
    for fid in ids:
        first, total = get(fid, 0, 0, tries=1)
        if first is None:
            reason = total
            continue
        free = shutil.disk_usage(a.out).free / 1e9
        have = os.path.getsize(part) if os.path.exists(part) else 0
        if free - (total - have) / 1e9 < a.min_free:
            log(f'{k}: needs {(total - have) / 1e9:.2f} GB, only {free:.2f} GB free - stopping')
            return 'space'
        pos = have
        with open(part, 'ab') as f:
            while pos < total:
                data, _ = get(fid, pos, min(total, pos + CHUNK) - 1)
                if data is None:
                    break
                f.write(data)
                pos += len(data)
        if pos == total:
            os.replace(part, dst)
            log(f'{k}: {total / 1e6:.0f} MB')
            return 'done'
        log(f'{k}: interrupted at {pos / 1e6:.0f}/{total / 1e6:.0f} MB (resumes next round)')
        reason = 'interrupted'
    return reason

if __name__ == '__main__':
    main()
