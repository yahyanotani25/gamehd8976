// 3D maps: terrain from a 16-bit heightmap + colour imagery, cloud layers,
// glowing routes, pins/markers. World convention: Y up, X east, -Z north.
import * as THREE from 'three';
import * as A from './anim.js';
import * as media from './media.js';
import { loadMap, sampleMap } from './png.js';
import * as TX from './textures.js';

const lin3 = (c) => { const k = new THREE.Color(c); return new THREE.Vector3(k.r, k.g, k.b); };

// Web-Mercator metres for a lon/lat.
export function mercator(lon, lat) {
  const R = 6378137;
  return [R * A.rad(lon), R * Math.log(Math.tan(Math.PI / 4 + A.rad(lat) / 2))];
}

// Terrain mesh.
//   dir          folder with bounds.json + heightmap_u16le.bin|heightmap.png + imagery.jpg
//                (the format written by tools/map_rasters.py), or give:
//   height, encoding ('png16' | 'terrarium' | 'u16le'), heightSize [w, h] (for .bin),
//   range [min_m, max_m] (png16/u16le), groundSize [w_m, h_m], color (URL), bounds {west,east,south,north}
//   size         world width in units (default 100); depth follows the ground aspect
//   exaggeration vertical exaggeration (1.15)
//   segments     mesh columns (384)
//   shade        0 = imagery as is, 1 = fully relit by the sun (default 0.55)
//   sun          direction [x, y, z]; sunColor, ambient (colours)
//   haze         { color, density (per world unit), height (world y where haze thins), falloff }
//   snow         { above (m), slope (max deg), color, amount, noise }
//   colorImage   'imagery.jpg' (file in dir), maxTex 4096, saturation, exposure
export async function terrain(o = {}) {
  let meta = null;
  if (o.dir) meta = await (await fetch(`${o.dir}/bounds.json`)).json();
  const hm = meta?.layers?.heightmap;
  const range = o.range ?? (hm ? [hm.min_m, hm.max_m] : [0, 1000]);
  let map;
  if (o.dir) {
    try { map = await loadMap(`${o.dir}/heightmap_u16le.bin`, { width: hm.width, height: hm.height }); }
    catch { map = await loadMap(`${o.dir}/heightmap.png`); }
  } else map = await loadMap(o.height, { encoding: o.encoding, width: o.heightSize?.[0], height: o.heightSize?.[1] });
  // elevation in metres
  const elev = new Float32Array(map.data.length);
  for (let i = 0; i < elev.length; i++) elev[i] = map.metres ? map.data[i] : range[0] + map.data[i] * (range[1] - range[0]);
  const em = { width: map.width, height: map.height, data: elev };
  const gs = o.groundSize ?? (meta ? [meta.size_ground_km_at_center.width * 1000, meta.size_ground_km_at_center.height * 1000] : [10000, 10000 * map.height / map.width]);
  const sizeX = o.size ?? 100, sizeZ = (sizeX * gs[1]) / gs[0];
  const mPerUnit = gs[0] / sizeX;
  let minE = Infinity; for (const v of elev) if (v < minE) minE = v;
  const base = o.base ?? minE;
  const exag = o.exaggeration ?? 1.15;

  // mesh
  const nx = Math.max(2, o.segments ?? 384), nz = Math.max(2, Math.round((nx * sizeZ) / sizeX));
  const geo = new THREE.PlaneGeometry(sizeX, sizeZ, nx - 1, nz - 1);
  geo.rotateX(-Math.PI / 2);
  const aE = new Float32Array(nx * nz);
  for (let z = 0; z < nz; z++) for (let x = 0; x < nx; x++) aE[z * nx + x] = sampleMap(em, x / (nx - 1), z / (nz - 1)) - base;
  geo.setAttribute('aElev', new THREE.BufferAttribute(aE, 1));
  geo.computeBoundingSphere();
  geo.boundingSphere.radius += ((range[1] - base) / mPerUnit) * exag * 3; // displaced in the shader
  // gradient map (slopes, metres/metre) from the full-resolution heightmap
  const W0 = map.width, H0 = map.height, pxm = gs[0] / W0, pzm = gs[1] / H0;
  const grad = new Float32Array(W0 * H0 * 4);
  for (let y = 0; y < H0; y++) for (let x = 0; x < W0; x++) {
    const xl = Math.max(0, x - 1), xr = Math.min(W0 - 1, x + 1), yu = Math.max(0, y - 1), yd = Math.min(H0 - 1, y + 1);
    const gx = (elev[y * W0 + xr] - elev[y * W0 + xl]) / ((xr - xl) * pxm);
    const gz = (elev[yd * W0 + x] - elev[yu * W0 + x]) / ((yd - yu) * pzm);
    const i = ((H0 - 1 - y) * W0 + x) * 4; // DataTexture row 0 = bottom (v = 0 = south)
    grad[i] = gx; grad[i + 1] = gz; grad[i + 2] = elev[y * W0 + x]; grad[i + 3] = 1;
  }
  const gradTex = new THREE.DataTexture(grad, W0, H0, THREE.RGBAFormat, THREE.FloatType);
  gradTex.minFilter = gradTex.magFilter = THREE.LinearFilter; gradTex.needsUpdate = true;
  const colorTex = o.color ? await media.texture(o.color, { maxSize: o.maxTex ?? 4096 }) : o.dir ? await media.texture(`${o.dir}/${o.colorImage ?? 'imagery.jpg'}`, { maxSize: o.maxTex ?? 4096 }) : null;

  const haze = o.haze ?? {}, snow = o.snow ?? {};
  const sun = new THREE.Vector3(...(o.sun ?? [-0.5, 0.65, -0.35])).normalize();
  const uniforms = {
    tColor: { value: colorTex }, tGrad: { value: gradTex }, uHasColor: { value: colorTex ? 1 : 0 },
    uVScale: { value: exag / mPerUnit }, uExag: { value: exag },
    uSun: { value: sun }, uSunColor: { value: lin3(o.sunColor ?? '#fff1de').multiplyScalar(o.sunIntensity ?? 1.15) }, uAmbient: { value: lin3(o.ambient ?? '#6f8796').multiplyScalar(0.55) },
    uShade: { value: o.shade ?? 0.55 }, uExposure: { value: o.exposure ?? 0 }, uSat: { value: o.saturation ?? 1 },
    uHazeColor: { value: lin3(haze.color ?? '#8FA3AE') }, uHazeDensity: { value: haze.density ?? 0.006 }, uHazeHeight: { value: haze.height ?? 0 }, uHazeFalloff: { value: haze.falloff ?? 0.15 },
    uSnowAbove: { value: snow.above ?? 1e9 }, uSnowSlope: { value: Math.cos(A.rad(snow.slope ?? 35)) }, uSnowColor: { value: lin3(snow.color ?? '#D6DEE2') }, uSnowAmt: { value: snow.amount ?? 0 }, uSnowNoise: { value: snow.noise ?? 0.5 },
    tNoise: { value: TX.noise({ size: 256, scale: 8, octaves: 4, seed: 41 }) },
    tCloud: { value: TX.noise({ size: 512, scale: 3, octaves: 5, seed: 17 }) }, uCloudAmt: { value: 0 }, uCloudScale: { value: 0.01 }, uCloudOff: { value: new THREE.Vector2() }, uCloudCover: { value: 0.5 },
    uBase: { value: base }, uOpacity: { value: 1 },
  };
  const material = new THREE.ShaderMaterial({
    uniforms,
    vertexShader: /* glsl */`
      attribute float aElev; uniform float uVScale;
      varying vec2 vUv; varying vec3 vWorld; varying float vElev;
      void main(){
        vUv = uv; vElev = aElev;
        vec3 p = position + vec3(0.0, aElev * uVScale, 0.0);
        vec4 w = modelMatrix * vec4(p, 1.0); vWorld = w.xyz;
        gl_Position = projectionMatrix * viewMatrix * w;
      }`,
    fragmentShader: /* glsl */`
      uniform sampler2D tColor, tGrad, tNoise, tCloud; uniform float uHasColor, uExag, uShade, uExposure, uSat, uHazeDensity, uHazeHeight, uHazeFalloff, uSnowAbove, uSnowSlope, uSnowAmt, uSnowNoise, uCloudAmt, uCloudScale, uCloudCover, uBase, uOpacity;
      uniform vec3 uSun, uSunColor, uAmbient, uHazeColor, uSnowColor; uniform vec2 uCloudOff;
      varying vec2 vUv; varying vec3 vWorld; varying float vElev;
      void main(){
        vec4 g = texture2D(tGrad, vUv);
        vec3 n = normalize(mat3(modelMatrix) * vec3(-g.x * uExag, 1.0, -g.y * uExag));
        vec3 alb = uHasColor > 0.5 ? texture2D(tColor, vUv).rgb : vec3(0.18, 0.2, 0.19);
        float lam = max(dot(n, normalize(uSun)), 0.0);
        vec3 lit = alb * (uAmbient + uSunColor * lam) * 1.6;
        vec3 c = mix(alb, lit, uShade);
        float elevM = g.z;
        if (uSnowAmt > 0.0) {
          float nz = texture2D(tNoise, vWorld.xz * 0.05).r;
          float hs = smoothstep(uSnowAbove - 60.0, uSnowAbove + 60.0, elevM + (nz - 0.5) * 240.0 * uSnowNoise);
          float sl = smoothstep(uSnowSlope - 0.06, uSnowSlope + 0.06, n.y);
          vec3 sc = uSnowColor * (uAmbient * 0.9 + uSunColor * lam) * 1.25;
          c = mix(c, sc, hs * sl * uSnowAmt);
        }
        if (uCloudAmt > 0.0) {
          float cl = texture2D(tCloud, vWorld.xz * uCloudScale + uCloudOff).r;
          c *= 1.0 - uCloudAmt * smoothstep(uCloudCover - 0.08, uCloudCover + 0.12, cl);
        }
        c *= exp2(uExposure);
        float l = dot(c, vec3(0.2126, 0.7152, 0.0722)); c = mix(vec3(l), c, uSat);
        float dist = length(vWorld - cameraPosition);
        float hf = exp(-max(vWorld.y - uHazeHeight, 0.0) * uHazeFalloff);
        float f = 1.0 - exp(-pow(dist * uHazeDensity, 2.0));
        f = clamp(f * mix(0.55, 1.0, hf), 0.0, 1.0);
        c = mix(c, uHazeColor, f);
        gl_FragColor = vec4(c, uOpacity);
      }`,
    transparent: false,
  });
  const mesh = new THREE.Mesh(geo, material);
  mesh.frustumCulled = false;
  const group = new THREE.Group();
  group.add(mesh);

  // CPU height query (world units, before the group transform)
  const heightAt = (x, z) => {
    const u = x / sizeX + 0.5, v = z / sizeZ + 0.5;
    return (sampleMap(em, A.clamp(u), A.clamp(v)) - base) * uniforms.uVScale.value;
  };
  const bl = meta?.bounds_lonlat ?? o.bounds;
  const bm = meta?.bounds_mercator_m;
  const self = {
    group, mesh, material, uniforms, sizeX, sizeZ, mPerUnit, base, range, meta,
    heightAt,
    // world point (group space) on the ground for lon/lat (needs bounds)
    lonLatToWorld(lon, lat, lift = 0) {
      let u, v;
      if (bm) { const [mx, my] = mercator(lon, lat); u = (mx - bm.west) / (bm.east - bm.west); v = (bm.north - my) / (bm.north - bm.south); }
      else { u = (lon - bl.west) / (bl.east - bl.west); v = (bl.north - lat) / (bl.north - bl.south); }
      const x = (u - 0.5) * sizeX, z = (v - 0.5) * sizeZ;
      return new THREE.Vector3(x, heightAt(x, z) + lift, z);
    },
    metresToUnits: (m) => m / mPerUnit,
    setExaggeration(e) { uniforms.uVScale.value = e / mPerUnit; uniforms.uExag.value = e; },
    setHaze(h = {}) { if (h.color) uniforms.uHazeColor.value.copy(lin3(h.color)); if (h.density !== undefined) uniforms.uHazeDensity.value = h.density; if (h.height !== undefined) uniforms.uHazeHeight.value = h.height; if (h.falloff !== undefined) uniforms.uHazeFalloff.value = h.falloff; },
    setOpacity(a) { uniforms.uOpacity.value = a; const tr = a < 0.999; if (material.transparent !== tr) { material.transparent = tr; material.needsUpdate = true; } group.visible = a > 0.001; },
    // Shadows from a kit.clouds layer: call after clouds.update(t).
    cloudShadow(clouds, amount = 0.35) {
      uniforms.uCloudAmt.value = amount; uniforms.tCloud.value = clouds.noiseTex;
      uniforms.uCloudScale.value = clouds.uniforms.uScale.value; uniforms.uCloudOff.value.copy(clouds.uniforms.uOff.value); uniforms.uCloudCover.value = clouds.uniforms.uCover.value;
    },
  };
  return self;
}

// Cloud layer: stacked horizontal noise cards that drift; fade when the camera
// gets close so a fly-through reads as passing through mist.
//   size [w, d], y (height), layers, opacity, cover (0..1, lower = more cloud), scale (noise cycles per unit), wind [x, z] units/s
export function clouds({ size = [120, 90], y = 12, layers = 3, spacing = 0.6, opacity = 0.7, cover = 0.52, scale = 0.012, wind = [0.25, 0.08], color = '#E9EEF0', shade = '#7d8c96', seed = 17, fadeNear = 6 } = {}) {
  const noiseTex = TX.noise({ size: 512, scale: 3, octaves: 5, seed });
  const group = new THREE.Group();
  const uniforms = { uOff: { value: new THREE.Vector2() }, uScale: { value: scale }, uCover: { value: cover } };
  const mats = [];
  for (let i = 0; i < layers; i++) {
    const m = new THREE.ShaderMaterial({
      uniforms: { ...uniforms, tNoise: { value: noiseTex }, uLayer: { value: i / Math.max(1, layers - 1) }, uOpacity: { value: opacity / Math.sqrt(layers) }, uColor: { value: lin3(color) }, uShade: { value: lin3(shade) }, uFadeNear: { value: fadeNear }, uSize: { value: new THREE.Vector2(...size) } },
      vertexShader: `varying vec3 vW; varying vec2 vP; void main(){ vP = position.xy; vec4 w = modelMatrix * vec4(position,1.0); vW = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`,
      fragmentShader: `uniform sampler2D tNoise; uniform vec2 uOff, uSize; uniform float uScale, uCover, uLayer, uOpacity, uFadeNear; uniform vec3 uColor, uShade; varying vec3 vW; varying vec2 vP;
        void main(){
          vec2 p = vW.xz * uScale + uOff;
          float n = texture2D(tNoise, p).r * 0.65 + texture2D(tNoise, p * 2.7 + 0.37 + uOff * 0.6).r * 0.35;
          float d = smoothstep(uCover - 0.1 * (1.0 - uLayer), uCover + 0.18, n);
          vec2 e = abs(vP) / (uSize * 0.5);
          float edge = 1.0 - smoothstep(0.7, 1.0, max(e.x, e.y));
          float cd = length(vW - cameraPosition);
          float near = smoothstep(uFadeNear * 0.3, uFadeNear, cd);
          vec3 c = mix(uShade, uColor, smoothstep(0.3, 0.9, n) * (0.6 + 0.4 * uLayer));
          gl_FragColor = vec4(c, d * uOpacity * edge * near);
        }`,
      transparent: true, depthWrite: false, side: THREE.DoubleSide,
    });
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(size[0], size[1]), m);
    mesh.rotation.x = -Math.PI / 2;
    mesh.position.y = y + i * spacing;
    mesh.renderOrder = 10 + i;
    group.add(mesh);
    mats.push(m);
  }
  return {
    group, uniforms, noiseTex,
    update(t) { uniforms.uOff.value.set(wind[0] * t * scale, wind[1] * t * scale); },
    setOpacity(a) { mats.forEach((m) => { m.uniforms.uOpacity.value = (opacity / Math.sqrt(layers)) * a; }); group.visible = a > 0.001; },
  };
}

// Glowing route along points ([x, y, z] world, or [x, z] draped on `terrain`).
// setDraw(to, from = 0) reveals it; the tip burns brighter. On the glow layer.
export function route(points, { terrain: tr = null, lift = 0.15, color = '#C8102E', width = 0.12, intensity = 3, tip = 2, segments = 400, glowLayer = 10 } = {}) {
  let pts = points.map((p) => (p.isVector3 ? p.clone() : p.length === 2 ? new THREE.Vector3(p[0], 0, p[1]) : new THREE.Vector3(...p)));
  if (tr) {
    // resample densely and drape
    const dense = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const a = pts[i], b = pts[i + 1], n = Math.max(2, Math.ceil(a.distanceTo(b) / (width * 1.5)));
      for (let k = 0; k < n; k++) dense.push(a.clone().lerp(b, k / n));
    }
    dense.push(pts[pts.length - 1].clone());
    pts = dense.map((p) => new THREE.Vector3(p.x, tr.heightAt(p.x, p.z) + lift, p.z));
  }
  const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal');
  const geo = new THREE.TubeGeometry(curve, segments, width / 2, 8, false);
  const m = new THREE.ShaderMaterial({
    uniforms: { uColor: { value: lin3(color) }, uI: { value: intensity }, uTo: { value: 1 }, uFrom: { value: 0 }, uTip: { value: tip }, uOpacity: { value: 1 } },
    vertexShader: `varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: `uniform vec3 uColor; uniform float uI, uTo, uFrom, uTip, uOpacity; varying vec2 vUv;
      void main(){ if (vUv.x > uTo || vUv.x < uFrom) discard; float k = 1.0 + uTip * exp(-(uTo - vUv.x) * 60.0) * step(uTo, 0.999);
        gl_FragColor = vec4(uColor * uI * k * uOpacity, 1.0); }`,
  });
  const mesh = new THREE.Mesh(geo, m);
  mesh.layers.enable(glowLayer);
  return {
    group: mesh, mesh, curve, material: m,
    setDraw(to, from = 0) { m.uniforms.uTo.value = A.clamp(to); m.uniforms.uFrom.value = A.clamp(from); mesh.visible = to - from > 0.0005; },
    setOpacity(a) { m.uniforms.uOpacity.value = a; mesh.visible = a > 0.001; },
    pointAt: (p) => curve.getPointAt(A.clamp(p)),
  };
}

// 3D map pin: glowing head, thin stem, expanding ground rings.
//   marker({ color, size, stem, rings }) -> { group, set({ pulse (s since start), opacity }) }
export function marker({ color = '#C8102E', ring = '#F2EFE8', size = 0.25, stem = 1.2, rings = 3, ringMax = 4, intensity = 2.5, glowLayer = 10 } = {}) {
  const group = new THREE.Group();
  const c = lin3(color);
  const headMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(c.x, c.y, c.z).multiplyScalar(intensity) });
  const head = new THREE.Mesh(new THREE.SphereGeometry(size / 2, 24, 16), headMat);
  head.position.y = stem;
  head.layers.enable(glowLayer);
  const stemMesh = new THREE.Mesh(new THREE.CylinderGeometry(size * 0.06, size * 0.06, stem, 8), new THREE.MeshBasicMaterial({ color: new THREE.Color(ring).multiplyScalar(0.8), transparent: true, opacity: 0.8 }));
  stemMesh.position.y = stem / 2;
  group.add(head, stemMesh);
  const ringMeshes = [];
  for (let i = 0; i < rings; i++) {
    const rm = new THREE.MeshBasicMaterial({ color: new THREE.Color(ring), transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide, blending: THREE.AdditiveBlending });
    const r = new THREE.Mesh(new THREE.RingGeometry(0.96, 1, 96), rm);
    r.rotation.x = -Math.PI / 2; r.position.y = 0.02;
    group.add(r); ringMeshes.push(r);
  }
  return {
    group, head,
    // pulse: seconds since the rings started (null = no rings); stagger between rings
    set({ pulse = null, opacity = 1, stagger = 0.2, dur = 0.8 } = {}) {
      headMat.opacity = opacity; head.visible = stemMesh.visible = opacity > 0.001;
      stemMesh.material.opacity = 0.8 * opacity;
      ringMeshes.forEach((r, i) => {
        if (pulse === null) { r.visible = false; return; }
        const p = A.prog(pulse - i * stagger, 0, dur);
        const e = A.E.outExpo(p);
        r.visible = p > 0 && p < 1;
        r.scale.setScalar(Math.max(0.001, e * ringMax));
        r.material.opacity = 0.6 * (1 - p) * opacity;
      });
    },
  };
}
