import { handle, increment } from '../netlify/functions/stats.mjs';
import assert from 'node:assert/strict';
// in-memory Blobs store with etag CAS + async jitter to force interleaving
class FakeStore {
  m = new Map(); n = 0;
  tick() { return new Promise((r) => setTimeout(r, Math.random() * 3)); }
  async getWithMetadata(k) { await this.tick(); const v = this.m.get(k); return v ? { data: JSON.parse(v.d), etag: v.e, metadata: {} } : null; }
  async get(k) { await this.tick(); const v = this.m.get(k); return v ? JSON.parse(v.d) : null; }
  async setJSON(k, data, o = {}) { await this.tick(); const v = this.m.get(k);
    if (o.onlyIfNew && v) return { modified: false };
    if (o.onlyIfMatch && (!v || v.e !== o.onlyIfMatch)) return { modified: false };
    const e = 'e' + ++this.n; this.m.set(k, { d: JSON.stringify(data), e }); return { modified: true, etag: e }; }
  async set(k, d) { await this.tick(); this.m.set(k, { d: JSON.stringify(d), e: 'e' + ++this.n }); return { modified: true }; }
  async delete(k) { await this.tick(); this.m.delete(k); }
  async list({ prefix = '', directories = false } = {}) { await this.tick();
    const keys = [...this.m.keys()].filter((k) => k.startsWith(prefix));
    if (!directories) return { blobs: keys.map((key) => ({ key, etag: '' })), directories: [] };
    const dirs = new Set(), blobs = [];
    for (const k of keys) { const rest = k.slice(prefix.length); const i = rest.indexOf('/'); if (i >= 0) dirs.add(prefix + rest.slice(0, i)); else blobs.push({ key: k, etag: '' }); }
    return { blobs, directories: [...dirs] }; }
}
const req = (body, method = 'POST') => new Request('http://x/api/stats', { method, body: method === 'POST' ? JSON.stringify(body) : undefined });
const s = new FakeStore();
// 1) concurrent increments are not lost
await Promise.all(Array.from({ length: 50 }, () => increment(s, 'total')));
assert.equal((await s.get('total')).n, 50, 'CAS increments');
// 2) visits + live counting
const s2 = new FakeStore(); const t0 = Date.UTC(2026, 9, 21, 20, 0, 0); // 03:00 VN on 22/10
let r = await (await handle(s2, req({ id: 'aaaaaaaa1', visit: true }), t0, () => 1)).json();
assert.deepEqual(r, { total: 1, today: 1, live: 1 });
r = await (await handle(s2, req({ id: 'bbbbbbbb2', visit: true }), t0 + 1000, () => 1)).json();
assert.deepEqual(r, { total: 2, today: 2, live: 2 });
// heartbeat without visit doesn't count a visit; same viewer counted once
r = await (await handle(s2, req({ id: 'aaaaaaaa1', visit: false }), t0 + 20000, () => 1)).json();
assert.deepEqual(r, { total: 2, today: 2, live: 2 });
assert.ok(s2.m.has('day/2026-10-22'), 'VN day key');
// 3) after 70 s with only one heartbeat, the other viewer drops off; sweep removes old buckets
r = await (await handle(s2, req({ id: 'bbbbbbbb2' }), t0 + 70000, () => 0)).json();
assert.equal(r.live, 1);
assert.ok(![...s2.m.keys()].some((k) => k.startsWith(`live/${Math.floor(t0 / 30000)}/`)), 'old bucket swept');
// 4) GET is read-only; bad input rejected
r = await (await handle(s2, req(null, 'GET'), t0 + 70000)).json();
assert.equal(r.total, 2);
assert.equal((await handle(s2, req({ id: 'x' }), t0)).status, 400);
assert.equal((await handle(s2, new Request('http://x', { method: 'POST', body: 'not json' }), t0)).status, 400);
assert.equal((await handle(s2, new Request('http://x', { method: 'DELETE' }), t0)).status, 405);
console.log('all stats tests passed');
