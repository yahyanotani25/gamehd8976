// Opens the engine in headless Chromium and returns a frame renderer.
import { createRequire } from 'module';
import { serve } from './server.mjs';
const require = createRequire('/opt/node-tools/');
const { chromium } = require('playwright');

export async function openEngine({ scenes } = {}) {
  const srv = await serve();
  const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--disable-gpu-sandbox'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error' && !/GL Driver Message/.test(m.text())) errors.push(m.text()); });
  const q = scenes ? `?scenes=${encodeURIComponent(scenes)}` : '';
  await page.goto(`http://127.0.0.1:${srv.port}/${q}`);
  await page.waitForFunction('window.ready === true || window.bootError', null, { timeout: 120000 });
  const bootError = await page.evaluate('window.bootError');
  if (bootError) throw new Error('engine failed to boot:\n' + bootError);
  const cdp = await page.context().newCDPSession(page);
  const duration = await page.evaluate('window.DURATION');
  return {
    page, duration, errors,
    // Render time t and return a PNG buffer.
    async frame(t) {
      await page.evaluate((tt) => window.renderFrame(tt), t);
      const { data } = await cdp.send('Page.captureScreenshot', { format: 'png', optimizeForSpeed: true });
      if (errors.length) throw new Error(`errors at t=${t}:\n` + errors.join('\n'));
      return Buffer.from(data, 'base64');
    },
    async close() { await browser.close(); srv.close(); },
  };
}
