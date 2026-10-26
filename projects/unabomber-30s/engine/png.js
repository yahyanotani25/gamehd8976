// Minimal PNG decoder for data maps (depth, height): keeps full 16-bit
// precision, which <img>/canvas decoding would truncate to 8 bits.
// Supports bit depth 8/16, colour types 0 (grey), 2 (RGB), 4 (grey+alpha),
// 6 (RGBA), non-interlaced. Returns { width, height, channels, depth, data }
// where data is a Uint16Array or Uint8Array of width*height*channels samples.

async function inflate(bytes) {
  const ds = new DecompressionStream('deflate');
  const stream = new Blob([bytes]).stream().pipeThrough(ds);
  return new Uint8Array(await new Response(stream).arrayBuffer());
}

export async function decodePNG(buf) {
  const u8 = new Uint8Array(buf);
  const dv = new DataView(u8.buffer, u8.byteOffset, u8.byteLength);
  if (dv.getUint32(0) !== 0x89504e47) throw new Error('not a PNG');
  let off = 8, width = 0, height = 0, bitDepth = 0, colorType = 0, interlace = 0;
  const idat = [];
  while (off < u8.length) {
    const len = dv.getUint32(off), type = String.fromCharCode(u8[off + 4], u8[off + 5], u8[off + 6], u8[off + 7]);
    const body = u8.subarray(off + 8, off + 8 + len);
    if (type === 'IHDR') {
      const b = new DataView(body.buffer, body.byteOffset, body.byteLength);
      width = b.getUint32(0); height = b.getUint32(4); bitDepth = body[8]; colorType = body[9]; interlace = body[12];
    } else if (type === 'IDAT') idat.push(body);
    else if (type === 'IEND') break;
    off += 12 + len;
  }
  if (interlace) throw new Error('interlaced PNG not supported');
  if (bitDepth !== 8 && bitDepth !== 16) throw new Error(`PNG bit depth ${bitDepth} not supported`);
  const channels = { 0: 1, 2: 3, 4: 2, 6: 4 }[colorType];
  if (!channels) throw new Error(`PNG colour type ${colorType} not supported`);
  const total = idat.reduce((s, b) => s + b.length, 0);
  const z = new Uint8Array(total);
  let p = 0;
  for (const b of idat) { z.set(b, p); p += b.length; }
  const raw = await inflate(z);
  const bpp = channels * (bitDepth / 8), stride = width * bpp;
  const out = new Uint8Array(height * stride);
  let prev = new Uint8Array(stride);
  for (let y = 0; y < height; y++) {
    const ft = raw[y * (stride + 1)];
    const line = raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1));
    const cur = out.subarray(y * stride, (y + 1) * stride);
    for (let x = 0; x < stride; x++) {
      const a = x >= bpp ? cur[x - bpp] : 0, b = prev[x], c = x >= bpp ? prev[x - bpp] : 0;
      let v = line[x];
      if (ft === 1) v += a;
      else if (ft === 2) v += b;
      else if (ft === 3) v += (a + b) >> 1;
      else if (ft === 4) { const pp = a + b - c, pa = Math.abs(pp - a), pb = Math.abs(pp - b), pc = Math.abs(pp - c); v += pa <= pb && pa <= pc ? a : pb <= pc ? b : c; }
      cur[x] = v & 255;
    }
    prev = cur;
  }
  if (bitDepth === 8) return { width, height, channels, depth: 8, data: out };
  const d16 = new Uint16Array(width * height * channels);
  for (let i = 0; i < d16.length; i++) d16[i] = (out[i * 2] << 8) | out[i * 2 + 1];
  return { width, height, channels, depth: 16, data: d16 };
}

// Fetch a data map and return a single-channel Float32Array normalised 0..1.
//   PNG 8/16-bit (first channel), terrarium-encoded RGB PNG (metres),
//   raw little-endian uint16 (.bin: pass width/height).
export async function loadMap(url, { encoding, width, height } = {}) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`map not found: ${url}`);
  const buf = await res.arrayBuffer();
  if (/\.bin$/i.test(url) || encoding === 'u16le') {
    if (!width || !height) throw new Error(`raw map ${url} needs width/height`);
    const u16 = new Uint16Array(buf);
    const f = new Float32Array(width * height);
    for (let i = 0; i < f.length; i++) f[i] = u16[i] / 65535;
    return { width, height, data: f, max: 65535 };
  }
  if (/\.png$/i.test(url) || encoding) {
    const p = await decodePNG(buf);
    const n = p.width * p.height, f = new Float32Array(n);
    if (encoding === 'terrarium') {
      // elevation_m = (R * 256 + G + B / 256) - 32768 (returned in metres, not normalised)
      for (let i = 0; i < n; i++) { const o = i * p.channels; f[i] = p.data[o] * 256 + p.data[o + 1] + p.data[o + 2] / 256 - 32768; }
      return { width: p.width, height: p.height, data: f, metres: true };
    }
    const mx = p.depth === 16 ? 65535 : 255;
    for (let i = 0; i < n; i++) f[i] = p.data[i * p.channels] / mx;
    return { width: p.width, height: p.height, data: f, max: mx };
  }
  // anything else (JPEG etc.): 8-bit via canvas, red channel
  const bmp = await createImageBitmap(new Blob([buf]), { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
  const c = new OffscreenCanvas(bmp.width, bmp.height);
  const g = c.getContext('2d');
  g.drawImage(bmp, 0, 0);
  const id = g.getImageData(0, 0, bmp.width, bmp.height).data;
  const f = new Float32Array(bmp.width * bmp.height);
  for (let i = 0; i < f.length; i++) f[i] = id[i * 4] / 255;
  return { width: bmp.width, height: bmp.height, data: f, max: 255 };
}

// Bilinear sample of a map at normalised (u, v), v = 0 at the TOP row.
export function sampleMap(m, u, v) {
  const x = Math.min(m.width - 1, Math.max(0, u * (m.width - 1))), y = Math.min(m.height - 1, Math.max(0, v * (m.height - 1)));
  const x0 = Math.floor(x), y0 = Math.floor(y), x1 = Math.min(m.width - 1, x0 + 1), y1 = Math.min(m.height - 1, y0 + 1);
  const fx = x - x0, fy = y - y0, d = m.data, w = m.width;
  const a = d[y0 * w + x0] * (1 - fx) + d[y0 * w + x1] * fx;
  const b = d[y1 * w + x0] * (1 - fx) + d[y1 * w + x1] * fx;
  return a * (1 - fy) + b * fy;
}
