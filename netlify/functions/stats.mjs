// Visit + live-viewer counter for the 3D model page, stored in Netlify Blobs.
//   POST /api/stats {id, visit}  -> heartbeat (and +1 visit when visit=true), returns counts
//   GET  /api/stats              -> counts only
// Counters use etag compare-and-swap so concurrent visits are not lost.
// "Live" = distinct viewer ids that sent a heartbeat in the current or previous 30 s bucket.
import { getStore } from '@netlify/blobs';

const BUCKET_MS = 30_000;
const ID_RE = /^[a-z0-9]{8,40}$/;

// calendar day in Vietnam (UTC+7)
const vnDay = (now) => new Date(now + 7 * 3600_000).toISOString().slice(0, 10);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// retries with jittered backoff when another request wrote first
export async function increment(store, key) {
  for (let attempt = 0; attempt < 30; attempt++) {
    const cur = await store.getWithMetadata(key, { type: 'json' });
    const res = cur
      ? await store.setJSON(key, { n: (cur.data?.n ?? 0) + 1 }, { onlyIfMatch: cur.etag })
      : await store.setJSON(key, { n: 1 }, { onlyIfNew: true });
    if (res.modified) return true;
    await sleep(Math.random() * 15 * Math.min(attempt + 1, 8));
  }
  return false;
}

async function readCount(store, key) {
  const v = await store.get(key, { type: 'json' });
  return v?.n ?? 0;
}

async function liveCount(store, now) {
  const b = Math.floor(now / BUCKET_MS);
  const ids = new Set();
  for (const bucket of [b, b - 1]) {
    const { blobs } = await store.list({ prefix: `live/${bucket}/` });
    for (const { key } of blobs) ids.add(key.slice(key.lastIndexOf('/') + 1));
  }
  return ids.size;
}

// drop heartbeat buckets older than a minute
async function sweep(store, now) {
  const b = Math.floor(now / BUCKET_MS);
  const { directories } = await store.list({ prefix: 'live/', directories: true });
  for (const dir of directories) {
    const bucket = Number(dir.split('/')[1]);
    if (!(bucket < b - 1)) continue;
    const { blobs } = await store.list({ prefix: `${dir}/` });
    await Promise.all(blobs.map(({ key }) => store.delete(key)));
  }
}

export async function handle(store, req, now = Date.now(), random = Math.random) {
  const day = vnDay(now);
  if (req.method === 'POST') {
    let body = {};
    try { body = await req.json(); } catch { /* empty body */ }
    const id = typeof body.id === 'string' ? body.id.toLowerCase() : '';
    if (!ID_RE.test(id)) return json({ error: 'invalid id' }, 400);
    // a visit that loses every retry is dropped rather than failing the viewer's request
    if (body.visit === true) await Promise.all([increment(store, 'total'), increment(store, `day/${day}`)]);
    await store.set(`live/${Math.floor(now / BUCKET_MS)}/${id}`, '1');
    if (random() < 0.1) await sweep(store, now);
  } else if (req.method !== 'GET') {
    return json({ error: 'method not allowed' }, 405);
  }
  const [total, today, live] = await Promise.all([readCount(store, 'total'), readCount(store, `day/${day}`), liveCount(store, now)]);
  return json({ total, today, live });
}

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json', 'cache-control': 'no-store' } });
}

export default async (req) => handle(getStore({ name: 'site-stats', consistency: 'strong' }), req);

export const config = { path: '/api/stats' };
