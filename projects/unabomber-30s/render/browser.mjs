// Opens the engine in headless Chromium (SwiftShader WebGL2) and returns a
// frame renderer. Every frame is a pure function of t, so any number of these
// can run in parallel on different time ranges.
import { createRequire } from 'module';
import { serve } from './server.mjs';
const require = createRequire('/opt/node-tools/');
const { chromium } = require('playwright');

export const W = 1920, H = 1080;

export async function openEngine({ scenes, query = {} } = {}) {
  const srv = await serve();
  const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-sandbox', '--js-flags=--max-old-space-size=6144'] });
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => {
    const tx = m.text();
    if (m.type() === 'error' && !/GL Driver Message|GPU stall due to ReadPixels/.test(tx)) errors.push(tx);
    else if (process.env.ENGINE_LOG && m.type() !== 'error') console.log('[page]', tx);
  });
  const q = new URLSearchParams({ ...(scenes ? { scenes } : {}), ...query }).toString();
  await page.goto(`http://127.0.0.1:${srv.port}/${q ? '?' + q : ''}`);
  await page.waitForFunction('window.ready === true || window.bootError', null, { timeout: 300000, polling: 200 });
  const bootError = await page.evaluate('window.bootError');
  if (bootError) { await browser.close(); srv.close(); throw new Error('engine failed to boot:\n' + bootError); }
  const cdp = await page.context().newCDPSession(page);
  const duration = await page.evaluate('window.DURATION');
  return {
    page, duration, errors,
    // Render time t and return an image buffer (PNG by default; 'jpeg' for quick looks).
    async frame(t, { format = 'png', quality = 92 } = {}) {
      const err = await page.evaluate(async (tt) => { try { await window.renderFrame(tt); return null; } catch (e) { return String(e && e.stack || e); } }, t);
      if (err) errors.push(err);
      if (errors.length) throw new Error(`errors at t=${t}:\n` + errors.join('\n'));
      const { data } = await cdp.send('Page.captureScreenshot', { format, ...(format === 'jpeg' ? { quality } : {}), optimizeForSpeed: true });
      return Buffer.from(data, 'base64');
    },
    async stats() { return page.evaluate('window.engineStats && window.engineStats()'); },
    async close() { await browser.close(); srv.close(); },
  };
}
