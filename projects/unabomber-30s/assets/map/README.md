# Map data: US -> Montana -> Lincoln, MT -> the forest

Material for the 3D map sequence. There are four nested boxes, each in its own folder. Every raster
is **Web Mercator (EPSG:3857), north up**, and covers its box's bounds exactly, edge to edge.
Within a box, all layers (heightmap, imagery, graded imagery, topo, relief, masks) share the same
bounds, so they line up whatever their pixel size. The smaller boxes sit at exact Mercator rectangles
inside the larger ones (see `index.json`). Alignment of imagery, DEM, vectors and the US render was
checked visually (see `previews/`).

Total size is about 180 MB. Built by `tools/map_*.py`; see "Rebuild" at the end.

```
assets/map/
  index.json            all box bounds + where each box sits inside the bigger ones (UV) + point UVs
  us/                   contiguous US, 4096x2304 (16:9): dark stylised render, Montana highlight, masks, DEM
  wide/                 western Montana, ~400 x 300 km, centred on Lincoln
  regional/             Lincoln area, ~60 x 40 km, centred on Lincoln
  closeup/              forest close-up, ~10 x 7 km: Lincoln's south edge -> Stemple Pass Rd -> forested foothills
  vector/               GeoJSON: US states, Montana, US national outline, reference points
  previews/             alignment checks (imagery x DEM hillshade, with points + Montana border plotted)
```

## Boxes

| box | centre (lat, lon) | ground size | lon west..east | lat south..north | Mercator x west..east (m) | Mercator y south..north (m) |
|---|---|---|---|---|---|---|
| `us` | ~38.0, -96.0 | whole contiguous US | -127.990723 .. -64.006348 | 22.482106 .. 50.743408 | -14247862.072 .. -7125154.029 | 2569507.143 .. 6576030.417 |
| `wide` | 46.958, -112.683 | 400.3 x 300.1 km | -115.317993 .. -110.050049 | 45.592900 .. 48.288676 | -12837140.278 .. -12250715.397 | 5715349.479 .. 6155015.266 |
| `regional` | 46.958, -112.683 | 60.05 x 40.02 km | -113.078156 .. -112.287827 | 46.777963 .. 47.137425 | -12587802.692 .. -12499823.673 | 5905906.990 .. 5964534.191 |
| `closeup` | 46.9294, -112.6523 | 10.00 x 7.01 km | -112.718096 .. -112.586517 | 46.897915 .. 46.960866 | -12547721.025 .. -12533073.780 | 5925427.097 .. 5935688.768 |

Box edges are snapped to the tile pixel grid of the box's DEM zoom: z7 for `us`, z9 for `wide`,
z12 for `regional` and z14 for `closeup`. Ground sizes are measured at the box's centre latitude.
Each folder's `bounds.json` holds the full-precision numbers and per-layer details. The details
include the tile zoom, the native mosaic size, the pixel size in ground metres, elevation min/max
and the despike count.

Where each box sits inside the bigger ones (UV, origin at the top left; multiply by an image's width and height to get pixels):

| inside | box | u0 | v0 | u1 | v1 |
|---|---|---|---|---|---|
| `us` | `wide` | 0.1980598 | 0.1050824 | 0.2803915 | 0.2148199 |
| `us` | `regional` | 0.2330658 | 0.1526252 | 0.2454177 | 0.1672581 |
| `us` | `closeup` | 0.2386931 | 0.1598248 | 0.2407495 | 0.1623860 |
| `wide` | `regional` | 0.4251825 | 0.4332406 | 0.5752086 | 0.5665855 |
| `wide` | `closeup` | 0.4935317 | 0.4988482 | 0.5185089 | 0.5221879 |
| `regional` | `closeup` | 0.4555821 | 0.4920143 | 0.6220678 | 0.6670469 |

For example, in `us/us_dark_montana.png` (4096x2304) the `wide` box is the pixel rectangle x 811..1148, y 242..495.

## Files

### `us/` (contiguous US, 4096 x 2304, exact 16:9)
| file | size | what |
|---|---|---|
| `us_dark.png` | 4096x2304 RGB | Dark stylised map, no highlight. Near-black ocean; Canada and Mexico in a darker land tone; US states in slate grey with thin state lines and a brighter coast/border line; subtle terrain relief from the DEM; Great Lakes and large lakes cut out. No labels and no vignette. |
| `us_dark_montana.png` | 4096x2304 RGB | Same image with Montana highlighted: crimson fill (relief still visible), bright red-orange border and a soft red outer glow. |
| `montana_mask.png` | 4096x2304 8-bit L | Montana alpha mask (white = Montana), antialiased (3x supersampled), pixel-aligned with the two renders. |
| `montana_outline_mask.png` | 4096x2304 8-bit L | Mask of the Montana border line only (~2.3 px), for a glowing outline or a draw-on effect. |
| `us_heightmap.png` / `us_heightmap_u16le.bin` | 4096x2304 16-bit | Terrain (terrarium z7, area-resampled to the render grid). It **includes ocean bathymetry**: min -6132 m, max 4274 m. Clamp at 0 for land-only relief. |
| `bounds.json` | | bounds, encoding and the colours used |

Colours (sRGB): ocean `#090c11`, context land `#13171d`, US land `#1e242c`, state lines `#424c59`,
coast and border `#5c6876`, Montana fill `#74181c`, Montana line `#f05440`, glow `#d22c24`.

### `wide/`, `regional/`, `closeup/`
| file | wide | regional | closeup | what |
|---|---|---|---|---|
| `heightmap.png` | 1918x1438 | 2302x1534 | 1533x1074 | 16-bit grayscale PNG elevation |
| `heightmap_u16le.bin` | same | same | same | the same values as raw little-endian uint16, row-major from the top left, no header |
| DEM tile zoom / ground px | z9 / 208.7 m | z12 / 26.1 m | z14 / 6.5 m | AWS Terrain Tiles (terrarium) |
| elevation min..max | 525.0..3382.0 m | 1247.4..2867.0 m | 1367.0..2018.2 m | per-box min/max used for the encoding |
| `hillshade.png` | 1918x1438 | 2302x1534 | 1533x1074 | 8-bit hillshade from the DEM (sun azimuth 315 deg, altitude 40 deg, no exaggeration) |
| `imagery.jpg` | 7672x5752 (z11, 52 m) | 8192x5459 (z14 resampled from 9208x6136, 7.3 m) | 6132x4296 (z16, 1.6 m) | USGS orthoimagery (true colour, summer) |
| `imagery_grade_night.jpg` | same | same | same | cinematic "night/dawn" grade: cold, desaturated (~48%), slightly darker, gentle contrast, blue-teal shadows, matte blacks. The same grade is used for every box, so cuts and push-ins match. |
| `usgs_topo.jpg` | 3836x2876 (z10) | 4604x3068 (z13) | 3066x2148 (z15) | USGS Topo (labelled topo map: roads, creeks, contours) |
| `usgs_shaded_relief.jpg` | 8192x6142 (z12 resampled) | 4604x3068 (z13) | n/a | USGS 3DEP shaded relief. It is very pale at these scales, so it works best as a multiply layer. Cached tiles at z9-z11 do not exist, so `wide` uses z12. |
| `bounds.json` | | | | everything above, machine-readable |

Elevation decoding (both heightmap files): `elevation_m = min_m + value / 65535 * (max_m - min_m)`,
with `min_m` and `max_m` taken from `bounds.json -> layers.heightmap`. The quantisation step is under
5 cm in the Montana boxes and 16 cm in `us`. Terrarium tiles contain isolated spike and pit pixels, which ring around lake shores. These were
removed: a pixel more than max(40 m, 0.9 x pixel size) above or below all 8 of its neighbours was
replaced by their median. That fixed 33 pixels in `wide`, 0 in `regional`, 0 in `closeup` and 59 in `us`.

The `regional` box is 60 x 40 km around the town. It takes in the Blackfoot valley, the Scapegoat
peaks to the north (the max of 2867 m is Red Mountain, at 47.117 N, -112.739 W) and the forested hills to the south. The
`closeup` box runs from Lincoln's south edge (MT-200 and the airstrip at the top) across Gehring
Ranch Rd and Stemple Pass Rd, then up into the forested foothills of Baldy Mountain. This is the
**general area** of the cabin. The exact cabin site is not marked anywhere in this data.

### `vector/`
| file | what |
|---|---|
| `us_states_contiguous.geojson` | 48 states + DC, MultiPolygon, lon/lat (NAD83, effectively WGS84), properties `NAME, STUSPS, STATEFP, GEOID`. Census 1:5M cartographic boundaries, clipped to the shoreline, so Great Lakes water is excluded. Coordinates are rounded to 5 decimals (~1 m). |
| `montana.geojson` | Montana only (1 ring) |
| `us_nation_contiguous.geojson` | contiguous US national outline (coast + borders), 114 polygons including islands |
| `points.json` | GeoJSON points with `name, state, note`: Lincoln MT (46.95556, -112.67278), Helena MT (46.59639, -112.02639), Missoula MT (46.87436, -114.02614), Great Falls MT (47.49167, -111.28917), Chicago IL (41.88194, -87.62778), Berkeley CA (37.87167, -122.27278). From the Wikipedia/GNIS coordinates. The brief's Lincoln value (46.958, -112.683) is ~0.8 km away; either is fine at map scale. |

`index.json` also lists each point's UV in every box that contains it.

## Mapping lat/lon to pixels

Web Mercator (spherical, R = 6378137 m):

```
x = R * lon * pi/180
y = R * ln(tan(pi/4 + lat * pi/360))
u = (x - west) / (east - west)          # 0 at the left edge, 1 at the right edge
v = (north - y) / (north - south)       # 0 at the top edge, 1 at the bottom edge
px = u * imageWidth ; py = v * imageHeight
```
`west/east/south/north` are the box's `bounds_mercator_m`. The pixel convention is "area": pixel
(i, j) covers u from i/W to (i+1)/W, so its centre is at u = (i + 0.5)/W. Inverse:
`lon = x / R * 180/pi`, `lat = (2 * atan(exp(y / R)) - pi/2) * 180/pi`.

To get ground distances, multiply Mercator metres by cos(lat): 0.6825 at Lincoln. Across the `wide`
box the scale varies by about ±2.5% from north to south, and by less than 0.3% in `regional`.

```js
// map-geo.js: tiny helper (all map rasters are EPSG:3857, north up)
const R = 6378137;
export const lonLatToMerc = (lon, lat) =>
  [R * lon * Math.PI / 180, R * Math.log(Math.tan(Math.PI / 4 + lat * Math.PI / 360))];
export const mercToLonLat = (x, y) =>
  [x / R * 180 / Math.PI, (2 * Math.atan(Math.exp(y / R)) - Math.PI / 2) * 180 / Math.PI];
// b = bounds_mercator_m from <box>/bounds.json or index.json.boxes[box].bounds_mercator_m
export function lonLatToUV(lon, lat, b) {
  const [x, y] = lonLatToMerc(lon, lat);
  return [(x - b.west) / (b.east - b.west), (b.north - y) / (b.north - b.south)];
}
export const lonLatToPx = (lon, lat, b, w, h) => {
  const [u, v] = lonLatToUV(lon, lat, b); return [u * w, v * h];
};
// Heights in metres (Float32Array, row-major from the top left). hm = bounds.json layers.heightmap
export async function loadHeights(url, hm) {
  const u16 = new Uint16Array(await (await fetch(url)).arrayBuffer()); // little-endian = every browser CPU
  const k = (hm.max_m - hm.min_m) / 65535, out = new Float32Array(u16.length);
  for (let i = 0; i < u16.length; i++) out[i] = hm.min_m + u16[i] * k;
  return out; // length hm.width * hm.height
}
// Lincoln in the regional imagery (8192x5459):
// lonLatToPx(-112.67278, 46.95556, regional.bounds_mercator_m, 8192, 5459) -> about [4202, 2766]
```

Using the data in three.js:
- Terrain mesh: build `PlaneGeometry(Wg, Hg, w - 1, h - 1)`, where Wg and Hg are the box's
  `size_mercator_m` multiplied by `cos(lat)` (ground metres) or any common scale. Then set
  vertex `k` to z = `heights[k]`. Vertex order (row by row from the top) matches the heightmap
  rows, and the default UVs with `flipY = true` map the imagery correctly. Treating pixel centres as
  vertices that run edge to edge puts them at most half a DEM pixel out, which is negligible. Heights
  are true scale in metres; 1.5-3x exaggeration reads well on screen.
- Nesting boxes in one scene: position each plane at its Mercator centre relative to a common
  origin (for example Lincoln), using the same scale for every box. The rectangles then line up
  exactly, as shown in `index.json -> contains`.
- **16-bit PNG caveat:** browsers (`<img>`, canvas, `TextureLoader`) decode PNG16 to 8 bits.
  Use `heightmap_u16le.bin`, as in the helper above, or decode the PNG with a JS PNG decoder.
  The PNG16 files are for Blender, GIMP and Python.
- Texture sizes are at most 8192 px a side. That is the `MAX_TEXTURE_SIZE` the render setup reports
  (checked: headless Chromium, ANGLE/SwiftShader, 8192).
  An 8192x5459 RGBA texture uses ~180 MB of GPU memory. For a single shot, downscale it or load only
  the box you need.

## Licences and credits

All source data is public domain or open, and safe for a monetised YouTube video.

| data | used in | licence | credit |
|---|---|---|---|
| AWS Terrain Tiles (Mapzen/Tilezen "joerd", terrarium encoding), `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png` | all heightmaps, hillshades, relief in `us_dark*` | Sources in these boxes: USGS 3DEP/NED, SRTM, GMTED2010, ETOPO1, all public domain. The `us` box also takes in Canada and Mexico, whose source data is Canadian CDEM (Open Government Licence - Canada) and INEGI (free use with attribution). See https://github.com/tilezen/joerd/blob/master/docs/attribution.md | "Terrain: Mapzen Terrain Tiles (AWS Open Data); USGS 3DEP, SRTM, GMTED2010, ETOPO1". If the US overview is shown, add "Contains information licensed under the Open Government Licence - Canada; INEGI". |
| USGS The National Map, USGSImageryOnly, `https://basemap.nationalmap.gov/arcgis/rest/services/USGSImageryOnly/MapServer` | `imagery*.jpg` | public domain (US government; USDA NAIP orthoimagery) | "Imagery: USGS The National Map / USDA NAIP" |
| USGS The National Map, USGSTopo and USGSShadedReliefOnly | `usgs_topo.jpg`, `usgs_shaded_relief.jpg` | public domain | "USGS The National Map" |
| U.S. Census Bureau, cartographic boundary files 2023 (`cb_2023_us_state_5m`, `cb_2023_us_nation_5m`), https://www2.census.gov/geo/tiger/GENZ2023/shp/ | `vector/*`, US render | public domain | "U.S. Census Bureau" (optional) |
| Natural Earth 10m land and lakes, https://www.naturalearthdata.com | context land and lakes in the US render | public domain | "Made with Natural Earth" (optional) |
| Wikipedia article coordinates (Lincoln, Helena, Missoula, Great Falls, Chicago, Berkeley) | `points.json` | facts, not copyrightable | n/a |

The renders, grades, masks and hillshades are derived works made for this project.

A suggested single on-screen or description credit:
*"Map data: USGS The National Map, USDA NAIP, Mapzen Terrain Tiles (AWS), U.S. Census Bureau, Natural Earth."*

## Caveats
- The imagery is recent (service refreshed 2024; summer NAIP) and shows today's roads, houses and the Lincoln airstrip,
  not 1996. That is fine at map scale, but avoid presenting a close-up as a 1990s view. The `closeup`
  imagery has mild tone differences between NAIP acquisition strips (on its east side).
- The `closeup` box is the general area south of Lincoln along Stemple Pass Rd, **not** the exact
  cabin site.
- The `wide` box was requested as imagery z10. It was built at z11 (7672 px), which stays under the
  8192 px cap. Downscale it by 2x if z10 is wanted.
- The US render uses Web Mercator rather than Albers, so it nests exactly with the terrain boxes.
  The northern states look slightly stretched, as on any web map.

## Rebuild
Run from anywhere, in isolated mode. The tile cache goes in the session scratch dir; edit
`SCRATCH` in `tools/map_common.py` to change it.
```
python3 -I tools/map_rasters.py      # DEMs + imagery/topo/relief mosaics + bounds.json (boxes in map_common.BOXES)
python3 -I tools/map_grade.py        # imagery_grade_night.jpg (grade params in PARAMS)
python3 -I tools/map_vector.py       # vector/*.geojson, points.json
python3 -I tools/map_us_render.py    # us/* (needs map_vector sources)
python3 -I tools/map_index.py        # index.json
python3 -I tools/map_preview.py      # previews/*
```
