// Photographs and footage in 3D.
//   photoPlane  — a still on a plane; with a depth map it becomes a 2.5D
//                 camera-projection mesh (true parallax), with edge cutting and
//                 a background fill layer; per-photo grade; "paper print" mode.
//   photoLayers — background plate + RGBA cut-out layers at different depths,
//                 scale-compensated so they line up from the projector.
//   videoPlane  — an extracted image sequence on a plane (see media.video).
import * as THREE from 'three';
import * as A from './anim.js';
import * as media from './media.js';
import { loadMap, sampleMap } from './png.js';
import * as TX from './textures.js';

// Shared GLSL for the photo material (injected into Basic/Standard materials).
const VERT_PARS = /* glsl */`
  attribute float aDepth;
  uniform vec3 uProj; uniform float uRelief;
  varying float vDepth;
`;
const VERT_MAIN = /* glsl */`
  vDepth = aDepth;
  { float dz = max(uProj.z - transformed.z, 1e-3);
    transformed += (uProj - transformed) * clamp(aDepth * uRelief / dz, 0.0, 0.97); }
`;
const FRAG_PARS = /* glsl */`
  uniform float uExposure, uBright, uContrast, uSat, uTintAmt, uOpacityP, uGamma, uPrint, uFibre, uMaskOn, uMaskInvert, uCutAlpha;
  uniform vec3 uTint, uPaper;
  uniform vec4 uPhotoRect, uCrop;
  uniform sampler2D tMaskP, tFibre;
  varying float vDepth;
  vec3 pToS(vec3 c){ c = max(c, 0.0); return mix(c * 12.92, 1.055 * pow(c, vec3(1.0/2.4)) - 0.055, step(0.0031308, c)); }
  vec3 pToL(vec3 c){ c = max(c, 0.0); return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
`;
const FRAG_MAP = /* glsl */`
  {
    vec2 puv = (vMapUv - uPhotoRect.xy) / uPhotoRect.zw;
    float inPhoto = step(0.0, puv.x) * step(puv.x, 1.0) * step(0.0, puv.y) * step(puv.y, 1.0);
    vec2 tuv = vec2(mix(uCrop.x, uCrop.z, clamp(puv.x, 0.0, 1.0)), mix(1.0 - uCrop.w, 1.0 - uCrop.y, clamp(puv.y, 0.0, 1.0)));
    vec4 texel = texture2D(map, tuv);
    vec3 c = texel.rgb * exp2(uExposure);
    vec3 s = pToS(c);
    s = pow(max(s, 0.0), vec3(uGamma));
    s = (s - 0.5) * uContrast + 0.5 + uBright;
    float l = dot(s, vec3(0.2126, 0.7152, 0.0722));
    s = mix(vec3(l), s, uSat);
    s = mix(s, s * uTint, uTintAmt);
    c = pToL(s);
    float a = texel.a;
    if (uMaskOn > 0.5) { float m = texture2D(tMaskP, tuv).r; a *= uMaskInvert > 0.5 ? 1.0 - m : m; }
    if (uPrint > 0.5) {
      vec3 fib = texture2D(tFibre, vMapUv * vec2(3.0, 3.0 * uPhotoRect.w / uPhotoRect.z)).rgb;
      c *= mix(vec3(1.0), fib / 0.93, uFibre);
      vec3 paperC = uPaper * fib / 0.93;
      c = mix(paperC, c, inPhoto);
      a = mix(1.0, a, inPhoto);
    }
    if (uCutAlpha > 0.0 && a < uCutAlpha) discard;
    diffuseColor.rgb *= c;
    diffuseColor.a *= a * uOpacityP;
  }
`;

function photoMaterial({ map, lit = false, fog = false, side = THREE.FrontSide, transparent = false, rough = 0.62 }) {
  const m = lit
    ? new THREE.MeshStandardMaterial({ map, roughness: rough, metalness: 0, side, fog, transparent })
    : new THREE.MeshBasicMaterial({ map, side, fog, transparent });
  const uniforms = {
    uProj: { value: new THREE.Vector3(0, 0, 10) }, uRelief: { value: 0 },
    uExposure: { value: 0 }, uBright: { value: 0 }, uContrast: { value: 1 }, uSat: { value: 1 }, uTintAmt: { value: 0 }, uOpacityP: { value: 1 }, uGamma: { value: 1 },
    uPrint: { value: 0 }, uFibre: { value: 0.18 }, uMaskOn: { value: 0 }, uMaskInvert: { value: 0 }, uCutAlpha: { value: 0 },
    uTint: { value: new THREE.Vector3(1, 1, 1) }, uPaper: { value: new THREE.Vector3(0.9, 0.87, 0.81) },
    uPhotoRect: { value: new THREE.Vector4(0, 0, 1, 1) }, uCrop: { value: new THREE.Vector4(0, 0, 1, 1) },
    tMaskP: { value: null }, tFibre: { value: null },
  };
  m.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, uniforms);
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\n' + VERT_PARS)
      .replace('#include <begin_vertex>', '#include <begin_vertex>\n' + VERT_MAIN);
    sh.fragmentShader = sh.fragmentShader.replace('#include <common>', '#include <common>\n' + FRAG_PARS)
      .replace('#include <map_fragment>', FRAG_MAP);
  };
  m.customProgramCacheKey = () => 'photo' + (lit ? 'L' : 'U');
  m.userData.uniforms = uniforms;
  return m;
}
// Black occluder with the same displacement (for the selective-glow pass).
function occluderMaterial(uniforms) {
  const m = new THREE.MeshBasicMaterial({ color: 0x000000 });
  m.onBeforeCompile = (sh) => {
    sh.uniforms.uProj = uniforms.uProj; sh.uniforms.uRelief = uniforms.uRelief;
    sh.vertexShader = sh.vertexShader.replace('#include <common>', '#include <common>\n' + VERT_PARS)
      .replace('#include <begin_vertex>', '#include <begin_vertex>\n' + VERT_MAIN);
  };
  m.customProgramCacheKey = () => 'photoOcc';
  return m;
}

function setAdjust(u, a = {}) {
  if (a.exposure !== undefined) u.uExposure.value = a.exposure;
  if (a.brightness !== undefined) u.uBright.value = a.brightness;
  if (a.contrast !== undefined) u.uContrast.value = a.contrast;
  if (a.saturation !== undefined) u.uSat.value = a.saturation;
  if (a.gamma !== undefined) u.uGamma.value = a.gamma;
  if (a.tint !== undefined) { const c = new THREE.Color(a.tint); const s = [c.r, c.g, c.b].map((v) => v ** (1 / 2.2)); const l = Math.max(0.05, s[0] * 0.2126 + s[1] * 0.7152 + s[2] * 0.0722); u.uTint.value.set(s[0] / l, s[1] / l, s[2] / l); }
  if (a.tintAmount !== undefined) u.uTintAmt.value = a.tintAmount;
}

// Box-blur a grid in place (radius r cells), `passes` times.
function blurGrid(g, nx, ny, r, passes = 2) {
  const tmp = new Float32Array(g.length);
  for (let p = 0; p < passes; p++) {
    for (let y = 0; y < ny; y++) for (let x = 0; x < nx; x++) {
      let s = 0, n = 0;
      for (let k = -r; k <= r; k++) { const xx = Math.min(nx - 1, Math.max(0, x + k)); s += g[y * nx + xx]; n++; }
      tmp[y * nx + x] = s / n;
    }
    for (let y = 0; y < ny; y++) for (let x = 0; x < nx; x++) {
      let s = 0, n = 0;
      for (let k = -r; k <= r; k++) { const yy = Math.min(ny - 1, Math.max(0, y + k)); s += tmp[yy * nx + x]; n++; }
      g[y * nx + x] = s / n;
    }
  }
}
// Min filter (pushes foreground edges back: the background surface behind holes).
function minGrid(g, nx, ny, r) {
  const out = new Float32Array(g.length);
  for (let y = 0; y < ny; y++) for (let x = 0; x < nx; x++) {
    let m = Infinity;
    for (let dy = -r; dy <= r; dy++) for (let dx = -r; dx <= r; dx++) {
      const xx = Math.min(nx - 1, Math.max(0, x + dx)), yy = Math.min(ny - 1, Math.max(0, y + dy));
      m = Math.min(m, g[yy * nx + xx]);
    }
    out[y * nx + x] = m;
  }
  return out;
}

// Build a (nx-1) x (ny-1) segment plane with per-vertex depth; drop triangles
// across depth jumps larger than edgeCut.
function depthPlane(w, h, nx, ny, depthGrid, edgeCut = 0) {
  const geo = new THREE.PlaneGeometry(w, h, nx - 1, ny - 1);
  // PlaneGeometry rows run top (v = 1) to bottom; depthGrid rows run top to bottom too.
  geo.setAttribute('aDepth', new THREE.BufferAttribute(depthGrid ?? new Float32Array(nx * ny), 1));
  if (depthGrid && edgeCut > 0) {
    const idx = [];
    for (let y = 0; y < ny - 1; y++) for (let x = 0; x < nx - 1; x++) {
      const a = y * nx + x, b = a + nx, c = b + 1, d = a + 1;
      const tri = (i, j, k) => {
        const da = depthGrid[i], db = depthGrid[j], dc = depthGrid[k];
        if (Math.max(da, db, dc) - Math.min(da, db, dc) <= edgeCut) idx.push(i, j, k);
      };
      tri(a, b, d); tri(b, c, d);
    }
    geo.setIndex(idx);
  }
  return geo;
}

// Photo on a plane. Returns a handle; add handle.group to the scene group.
// Options (all optional except src/texture):
//   src | texture        image URL, or an existing texture (video) with aspect
//   w, h                 world size (give one; the other follows the aspect)
//   depth                depth map URL (16-bit PNG best; white = near unless invert)
//   relief               world units the nearest pixel comes forward (default 0.12 * projector distance)
//   projFov              vertical fov (deg) of the projector that frames the photo height (default 32.3 = 35 mm)
//   segs                 mesh columns for depth mode (default 256)
//   invert, depthGamma, depthBlur (cells)   depth conditioning
//   edgeCut              drop triangles spanning a depth jump > this (0..1 depth units, e.g. 0.05)
//   fill                 true | URL: background layer behind cut edges (same photo or an inpainted plate)
//   mask                 URL of a mask (white = keep), e.g. holes for windows; maskInvert
//   cutout               use the image alpha (PNG cut-outs) with alpha blending
//   crop                 [u0, v0, u1, v1] in image coordinates (v down)
//   adjust               { exposure, brightness, contrast, saturation, gamma, tint, tintAmount }
//   opacity, lit (lighting/shadows), fog, maxSize, side
//   print                { border (fraction of the short side, 0.06), paper colour, fibre (0.18),
//                          curl (0..1), shadow (opacity, 0.35), shadowBlur }  — evidence-print look
export async function photoPlane(o = {}) {
  let map = o.texture?.isTexture ? o.texture : o.texture?.texture;
  if (!map) map = await media.texture(o.src, { maxSize: o.maxSize ?? 4096 });
  const img = map.image || {};
  const crop = o.crop ?? [0, 0, 1, 1];
  const aspect = o.aspect ?? (((img.width || 16) * (crop[2] - crop[0])) / ((img.height || 9) * (crop[3] - crop[1])));
  let w = o.w, h = o.h;
  if (w && !h) h = w / aspect; else if (h && !w) w = h * aspect; else if (!w && !h) { h = 1; w = aspect; }
  const projFov = o.projFov ?? 32.3;
  const D = o.projector ?? (h / 2) / Math.tan(A.rad(projFov) / 2);
  const relief = o.relief ?? (o.depth ? 0.12 * D : 0);
  const group = new THREE.Group();

  // geometry
  const pr = o.print;
  let geo, depthGrid = null, nx = 2, ny = 2, fillGeo = null;
  let pw = w, ph = h, rect = [0, 0, 1, 1];
  if (pr) {
    const b = (pr.border ?? 0.06) * Math.min(w, h);
    pw = w + 2 * b; ph = h + 2 * b;
    rect = [b / pw, b / ph, w / pw, h / ph];
  }
  if (o.depth) {
    const dm = await loadMap(o.depth);
    nx = Math.max(2, o.segs ?? 256); ny = Math.max(2, Math.round(nx / (pw / ph)));
    depthGrid = new Float32Array(nx * ny);
    for (let y = 0; y < ny; y++) for (let x = 0; x < nx; x++) {
      const u = x / (nx - 1), v = y / (ny - 1);
      const pu = (u - rect[0]) / rect[2], pv = (v - rect[1]) / rect[3];
      const iu = A.lerp(crop[0], crop[2], A.clamp(pu)), iv = A.lerp(crop[1], crop[3], A.clamp(pv));
      let d = sampleMap(dm, iu, iv);
      if (o.invert) d = 1 - d;
      depthGrid[y * nx + x] = Math.pow(A.clamp(d), o.depthGamma ?? 1);
    }
    if (o.depthBlur) blurGrid(depthGrid, nx, ny, Math.round(o.depthBlur), 2);
    geo = depthPlane(pw, ph, nx, ny, depthGrid, o.edgeCut ?? 0);
    if (o.fill) fillGeo = depthPlane(pw, ph, nx, ny, minGrid(depthGrid, nx, ny, Math.max(2, Math.round(nx * 0.015))), 0);
  } else {
    const n = pr ? 40 : 1;
    geo = depthPlane(pw, ph, n + 1, Math.max(2, Math.round((n * ph) / pw) + 1), null, 0);
  }
  if (pr && (pr.curl ?? 0.5) > 0) {
    const p = geo.attributes.position, k = (pr.curl ?? 0.5) * Math.min(pw, ph) * 0.05;
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i) / (pw / 2), y = p.getY(i) / (ph / 2);
      p.setZ(i, p.getZ(i) + k * (0.65 * Math.pow(Math.abs(x), 3) + 0.35 * Math.pow(Math.abs(y), 3) + 0.4 * Math.max(0, x * -y) ** 2));
    }
    p.needsUpdate = true;
    geo.computeVertexNormals();
  }

  const transparent = !!o.cutout || (o.opacity ?? 1) < 1;
  const material = photoMaterial({ map, lit: o.lit ?? !!pr, fog: o.fog ?? false, side: o.side ?? (pr ? THREE.DoubleSide : THREE.FrontSide), transparent });
  const u = material.userData.uniforms;
  u.uProj.value.set(0, 0, D); u.uRelief.value = relief;
  u.uPhotoRect.value.set(...rect); u.uCrop.value.set(...crop);
  if (pr) {
    u.uPrint.value = 1; u.uFibre.value = pr.fibre ?? 0.18;
    const pc = new THREE.Color(pr.paper ?? '#ECE6D8'); u.uPaper.value.set(pc.r, pc.g, pc.b);
    u.tFibre.value = TX.paper({ size: 512, seed: 5, tone: '#ffffff' });
  }
  if (o.mask) { u.tMaskP.value = await media.texture(o.mask, { data: true, maxSize: o.maxSize ?? 4096 }); u.uMaskOn.value = 1; u.uMaskInvert.value = o.maskInvert ? 1 : 0; u.uCutAlpha.value = 0.5; }
  if (o.cutout) { material.depthWrite = false; u.uCutAlpha.value = 0.004; }
  setAdjust(u, o.adjust);
  u.uOpacityP.value = o.opacity ?? 1;
  const mesh = new THREE.Mesh(geo, material);
  mesh.userData.glowOccluder = occluderMaterial(u);
  mesh.castShadow = !!(o.castShadow ?? pr); mesh.receiveShadow = !!(o.receiveShadow ?? false);
  group.add(mesh);

  let fillMesh = null;
  if (fillGeo) {
    const fmap = typeof o.fill === 'string' ? await media.texture(o.fill, { maxSize: o.maxSize ?? 4096 }) : map;
    const fm = photoMaterial({ map: fmap, lit: o.lit ?? false, fog: o.fog ?? false });
    const fu = fm.userData.uniforms;
    fu.uProj.value.copy(u.uProj.value); fu.uRelief.value = relief; fu.uCrop.value.set(...crop); fu.uPhotoRect.value.set(...rect);
    setAdjust(fu, o.adjust);
    fillMesh = new THREE.Mesh(fillGeo, fm);
    fillMesh.position.z = -0.002 * D;
    fillMesh.renderOrder = -1;
    fillMesh.userData.glowOccluder = occluderMaterial(fu);
    group.add(fillMesh);
  }

  let shadow = null;
  if (pr && (pr.shadow ?? 0.35) > 0) {
    const sm = new THREE.MeshBasicMaterial({ map: TX.softRect(30), color: 0x000000, transparent: true, opacity: pr.shadow ?? 0.35, depthWrite: false });
    shadow = new THREE.Mesh(new THREE.PlaneGeometry(pw * 1.22, ph * 1.22), sm);
    shadow.position.set(pw * 0.025, -ph * 0.035, -Math.min(pw, ph) * 0.01);
    shadow.renderOrder = -2;
    group.add(shadow);
  }

  const handle = {
    group, mesh, fill: fillMesh, shadow, material, uniforms: u, map, w, h, printW: pw, printH: ph, aspect, projector: D, relief,
    setOpacity(a) {
      for (const m of [material, fillMesh?.material].filter(Boolean)) {
        m.userData.uniforms.uOpacityP.value = a;
        const tr = a < 0.999 || !!o.cutout;
        if (m.transparent !== tr) { m.transparent = tr; m.needsUpdate = true; }
      }
      if (shadow) shadow.material.opacity = (pr.shadow ?? 0.35) * a;
      group.visible = a > 0.001;
    },
    setAdjust(a) { setAdjust(u, a); if (fillMesh) setAdjust(fillMesh.material.userData.uniforms, a); },
    setRelief(r) { u.uRelief.value = r; if (fillMesh) fillMesh.material.userData.uniforms.uRelief.value = r; },
    // Camera placement relative to the projector (world space, honours the group
    // transform): push (0..1 toward the plane), truck [dx, dy] world units,
    // orbit [yawDeg, pitchDeg] around the plane centre. Returns { pos, target, fov }
    // for ctx.cam.set(). From the bare projector view the photo looks undistorted.
    view({ push = 0, truck = [0, 0], orbit = [0, 0], fov = projFov } = {}) {
      const d = D * (1 - push);
      const y = A.rad(orbit[0]), p = A.rad(orbit[1]);
      const local = new THREE.Vector3(truck[0] + d * Math.sin(y) * Math.cos(p), truck[1] + d * Math.sin(p), d * Math.cos(y) * Math.cos(p));
      const tgt = new THREE.Vector3(truck[0], truck[1], 0);
      group.updateMatrixWorld();
      local.applyMatrix4(group.matrixWorld); tgt.applyMatrix4(group.matrixWorld);
      return { pos: local.toArray(), target: tgt.toArray(), fov };
    },
    // World position of a point on the photo given in image fractions (u, v; v down),
    // at depth d (0 = far plane) — e.g. to pin labels or measure lines to the print.
    at(uu, vv, d = 0) {
      const x = (rect[0] + uu * rect[2] - 0.5) * pw, y = (0.5 - (rect[1] + vv * rect[3])) * ph;
      const v = new THREE.Vector3(x, y, 0);
      const k = A.clamp((d * u.uRelief.value) / D, 0, 0.97);
      v.add(new THREE.Vector3(0, 0, D).sub(v).multiplyScalar(k));
      group.updateMatrixWorld();
      return v.applyMatrix4(group.matrixWorld);
    },
  };
  return handle;
}

// Layered parallax: a background plate plus RGBA cut-outs at depth z (toward
// the camera), scaled so that from the projector they line up exactly.
//   layers: [{ src, z = 0, adjust, opacity, cutout (default true except the first) }]
export async function photoLayers({ layers, w, h, projFov = 32.3, maxSize = 4096, fog = false } = {}) {
  const group = new THREE.Group();
  const first = await media.texture(layers[0].src, { maxSize });
  const aspect = first.image.width / first.image.height;
  if (w && !h) h = w / aspect; else if (h && !w) w = h * aspect; else if (!w && !h) { h = 1; w = aspect; }
  const D = (h / 2) / Math.tan(A.rad(projFov) / 2);
  const out = [];
  for (let i = 0; i < layers.length; i++) {
    const L = layers[i];
    const z = L.z ?? 0, s = (D - z) / D;
    const p = await photoPlane({ src: L.src, w: w * s, h: h * s, cutout: L.cutout ?? i > 0, adjust: L.adjust, opacity: L.opacity, fog, maxSize, crop: L.crop });
    p.group.position.z = z;
    p.mesh.renderOrder = i;
    group.add(p.group);
    out.push(p);
  }
  return {
    group, layers: out, w, h, projector: D,
    view({ push = 0, truck = [0, 0], orbit = [0, 0], fov = projFov } = {}) {
      const d = D * (1 - push), y = A.rad(orbit[0]), p = A.rad(orbit[1]);
      const pos = new THREE.Vector3(truck[0] + d * Math.sin(y) * Math.cos(p), truck[1] + d * Math.sin(p), d * Math.cos(y) * Math.cos(p));
      const tgt = new THREE.Vector3(truck[0], truck[1], 0);
      group.updateMatrixWorld(); pos.applyMatrix4(group.matrixWorld); tgt.applyMatrix4(group.matrixWorld);
      return { pos: pos.toArray(), target: tgt.toArray(), fov };
    },
    setOpacity(a) { out.forEach((p) => p.setOpacity(a)); },
  };
}

// Footage on a plane: an image sequence from render/extract.sh.
//   const v = await kit.videoPlane({ dir: '/out/frames/crowd', w: 16, start: 5.6, speed: 0.5 });
//   v.show(t) every frame (global time). Other options as media.video + photoPlane.
export async function videoPlane(o = {}) {
  const v = await media.video(o);
  const p = await photoPlane({ ...o, texture: v.texture, aspect: v.aspect, depth: null });
  return { ...p, video: v, show: (t) => v.show(t), sourceTime: (t) => v.sourceTime(t) };
}
