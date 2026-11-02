"""Local HTTP relay so ffmpeg can seek inside Google Drive files without downloading
them: http://127.0.0.1:PORT/<drive file id> -> drive.usercontent.google.com.

Drive answers open-ended ranges ("bytes=X-", what ffmpeg sends) and plain GETs of big
files with an HTML page, but serves closed ranges reliably, so every request is
served as a stream of closed range fetches (RELAY_CHUNK bytes, default 1 MB; retried), stopping when ffmpeg
hangs up.   usage: drive_relay.py [port]"""
import http.server, re, socketserver, sys, threading, time
import requests

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
URL = 'https://drive.usercontent.google.com/download?id={}&export=download&confirm=t'
CHUNK = int(__import__("os").environ.get("RELAY_CHUNK", 1 << 20))
_local = threading.local()
_sizes = {}


def sess():
    if not hasattr(_local, 's'):
        _local.s = requests.Session()
    return _local.s


def get_range(fid, a, b, tries=8):
    for k in range(tries):
        try:
            r = sess().get(URL.format(fid), headers={'Range': f'bytes={a}-{b}'}, timeout=90)
            if r.status_code == 206 and 'text/html' not in r.headers.get('Content-Type', ''):
                return r
        except requests.RequestException:
            pass
        time.sleep(1.5 * (k + 1))
    return None


def size_of(fid):
    if fid not in _sizes:
        r = get_range(fid, 0, 0)
        if r is None:
            return None
        _sizes[fid] = int(r.headers['Content-Range'].split('/')[-1])
    return _sizes[fid]


class H(http.server.BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass

    def _serve(self, body):
        fid = self.path.strip('/').split('?')[0]
        total = size_of(fid)
        if total is None:
            self.send_error(502)
            return
        a, b, partial = 0, total - 1, False
        m = re.match(r'bytes=(\d*)-(\d*)', self.headers.get('Range', ''))
        if m:
            partial = True
            if m.group(1):
                a = int(m.group(1))
                b = int(m.group(2)) if m.group(2) else total - 1
            else:  # suffix range
                a = max(0, total - int(m.group(2)))
        b = min(b, total - 1)
        if a > b:
            self.send_response(416)
            self.send_header('Content-Range', f'bytes */{total}')
            self.end_headers()
            return
        self.send_response(206 if partial else 200)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Type', 'application/octet-stream')
        self.send_header('Content-Length', str(b - a + 1))
        if partial:
            self.send_header('Content-Range', f'bytes {a}-{b}/{total}')
        self.end_headers()
        if not body:
            return
        pos = a
        try:
            while pos <= b:
                r = get_range(fid, pos, min(b, pos + CHUNK - 1))
                if r is None:
                    break
                self.wfile.write(r.content)
                pos += len(r.content)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self):
        self._serve(True)

    def do_HEAD(self):
        self._serve(False)


class T(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == '__main__':
    T(('127.0.0.1', PORT), H).serve_forever()
