"""Find the raw-proxy frame that best matches a reference frame (ORB + homography inliers).
usage: match_frames.py REF.mp4 ref_time PROXY.mp4 [step]
prints best proxy time, inliers, homography."""
import sys, cv2, numpy as np, subprocess
def grab(path, t, w=640, h=360):
    raw = subprocess.run(['ffmpeg','-v','error','-ss',f'{t:.3f}','-i',path,'-frames:v','1','-vf',f'scale={w}:{h}','-f','rawvideo','-pix_fmt','bgr24','-'],capture_output=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(h,w,3) if len(raw)==w*h*3 else None
def frames(path, step=0.2):
    raw = subprocess.run(['ffmpeg','-v','error','-i',path,'-vf',f'fps={1/step},scale=640:360','-f','rawvideo','-pix_fmt','bgr24','-'],capture_output=True).stdout
    n = len(raw)//(640*360*3)
    return [np.frombuffer(raw[i*640*360*3:(i+1)*640*360*3],np.uint8).reshape(360,640,3) for i in range(n)]
orb = cv2.ORB_create(3000)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
def score(a, b):
    ka, da = orb.detectAndCompute(cv2.cvtColor(a,cv2.COLOR_BGR2GRAY), None)
    kb, db = orb.detectAndCompute(cv2.cvtColor(b,cv2.COLOR_BGR2GRAY), None)
    if da is None or db is None: return 0, None
    m = bf.match(da, db)
    if len(m) < 8: return 0, None
    pa = np.float32([ka[x.queryIdx].pt for x in m]); pb = np.float32([kb[x.trainIdx].pt for x in m])
    H, mask = cv2.findHomography(pb, pa, cv2.RANSAC, 4.0)
    return (int(mask.sum()) if mask is not None else 0), H
if __name__ == '__main__':
    ref, rt, prx = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    step = float(sys.argv[4]) if len(sys.argv) > 4 else 0.2
    a = grab(ref, rt)
    fs = frames(prx, step)
    best = max(((score(a, f)[0], i) for i, f in enumerate(fs)))
    print(f'ref={rt} best_t={best[1]*step + step/2:.2f} inliers={best[0]} of {len(fs)} frames')
