// node tools/ban-ve/print.mjs in.html out.pdf [png-prefix]  — in bản vẽ ra PDF A3 (Chromium)
import { chromium } from '/opt/node22/lib/node_modules/playwright/index.mjs';
import path from 'path';
const [inp, out, pngs] = process.argv.slice(2);
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1588, height: 1123 } });
await page.goto('file://' + path.resolve(inp), { waitUntil: 'networkidle' });
await page.evaluate(() => document.fonts.ready);
await page.pdf({ path: out, width: '420mm', height: '297mm', printBackground: true, preferCSSPageSize: true });
if (pngs) {
  const n = await page.$$eval('.sheet', (s) => s.length);
  for (let i = 0; i < n; i++) await (await page.$$('.sheet'))[i].screenshot({ path: `${pngs}-${i}.png` });
}
await browser.close();
