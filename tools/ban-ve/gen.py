#!/usr/bin/env python3
"""Bộ bản vẽ 2D (A3 ngang) cho KT-01 → HTML; tools/ban-ve/print.mjs in ra PDF.

python3 tools/ban-ve/gen.py out.html [cover.jpg]
"""
import math, sys, base64, os, html
from model import *

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATE = '22/10/2026'
PROJECT = 'NHÀ Ở 2 TẦNG 17 × 7 M'
CODE = 'KT-01'

# ---------------------------------------------------------------- svg helpers
INK = '#1a1f24'
POCHE = '#2b3137'
GLASS = '#cfe3ee'
ACCENT = '#c7782a'

def f(v): return f'{v:.2f}'.rstrip('0').rstrip('.')
def esc(s): return html.escape(s, quote=True)

class Page:
    def __init__(self): self.out = []
    def add(self, s): self.out.append(s)
    def svg(self): return '\n'.join(self.out)

class View:
    """Maps model (u, v) in metres to paper mm. flip=True: v grows upward (elevations)."""
    def __init__(self, page, ox, oy, scale, flip=False):
        self.p, self.ox, self.oy, self.k, self.flip = page, ox, oy, 1000 / scale, flip
    def x(self, u): return self.ox + u * self.k
    def y(self, v): return self.oy - v * self.k if self.flip else self.oy + v * self.k
    def pt(self, u, v): return f'{f(self.x(u))},{f(self.y(v))}'
    def rect(self, u1, u2, v1, v2, cls='', style=''):
        x1, x2 = sorted((self.x(u1), self.x(u2))); y1, y2 = sorted((self.y(v1), self.y(v2)))
        self.p.add(f'<rect class="{cls}" x="{f(x1)}" y="{f(y1)}" width="{f(x2 - x1)}" height="{f(y2 - y1)}" style="{style}"/>')
    def poly(self, pts, cls='', style='', closed=True):
        tag = 'polygon' if closed else 'polyline'
        self.p.add(f'<{tag} class="{cls}" points="{" ".join(self.pt(u, v) for u, v in pts)}" style="{style}"/>')
    def line(self, u1, v1, u2, v2, cls='', style=''):
        self.p.add(f'<line class="{cls}" x1="{f(self.x(u1))}" y1="{f(self.y(v1))}" x2="{f(self.x(u2))}" y2="{f(self.y(v2))}" style="{style}"/>')
    def circle(self, u, v, r, cls='', style=''):
        self.p.add(f'<circle class="{cls}" cx="{f(self.x(u))}" cy="{f(self.y(v))}" r="{f(r * self.k)}" style="{style}"/>')
    def path(self, d, cls='', style=''):
        self.p.add(f'<path class="{cls}" d="{d}" style="{style}"/>')
    def text(self, u, v, s, cls='t', size=2.2, anchor='middle', rot=0, dy=0, weight=None):
        x, y = self.x(u), self.y(v) + dy
        tr = f' transform="rotate({rot} {f(x)} {f(y)})"' if rot else ''
        w = f' font-weight="{weight}"' if weight else ''
        self.p.add(f'<text class="{cls}" x="{f(x)}" y="{f(y)}" font-size="{size}" text-anchor="{anchor}"{w}{tr}>{esc(s)}</text>')

def rot(pts, cx, cy, deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return [(cx + (x - cx) * c - (y - cy) * s, cy + (x - cx) * s + (y - cy) * c) for x, y in pts]

# ---------------------------------------------------------------- dimensions
def dim_chain(V, axis, pts, at, side, label_scale=1000, cls='dim', ext_from=None):
    """Dimension chain along `axis` ('x': horizontal, 'y': vertical) at model coordinate `at`.
    side −1/+1: which side the text sits. ext_from: model coordinate where extension lines start."""
    pts = sorted(set(round(p, 4) for p in pts))
    k = V.k
    for p in pts:
        if axis == 'x':
            x = V.x(p); y = V.y(at)
            if ext_from is not None:
                y0 = V.y(ext_from)
                V.p.add(f'<line class="ext" x1="{f(x)}" y1="{f(y0 + math.copysign(1.2, y - y0))}" x2="{f(x)}" y2="{f(y + math.copysign(1.2, y - y0))}"/>')
            V.p.add(f'<line class="tick" x1="{f(x - 0.9)}" y1="{f(y + 0.9)}" x2="{f(x + 0.9)}" y2="{f(y - 0.9)}"/>')
        else:
            x = V.x(at); y = V.y(p)
            if ext_from is not None:
                x0 = V.x(ext_from)
                V.p.add(f'<line class="ext" x1="{f(x0 + math.copysign(1.2, x - x0))}" y1="{f(y)}" x2="{f(x + math.copysign(1.2, x - x0))}" y2="{f(y)}"/>')
            V.p.add(f'<line class="tick" x1="{f(x - 0.9)}" y1="{f(y + 0.9)}" x2="{f(x + 0.9)}" y2="{f(y - 0.9)}"/>')
    if axis == 'x':
        V.line(pts[0] - 0.12, at, pts[-1] + 0.12, at, cls)
    else:
        V.line(at, pts[0] - 0.12, at, pts[-1] + 0.12, cls)
    for a, b in zip(pts, pts[1:]):
        val = round((b - a) * label_scale)
        if val <= 0: continue
        m = (a + b) / 2
        small = (b - a) * k < 7
        if axis == 'x':
            V.text(m, at, f'{val}', 'dimt', 1.9, dy=-1.0 if side < 0 else 2.6) if not small else \
                V.text(m, at, f'{val}', 'dimt', 1.5, dy=-1.0 if side < 0 else 2.4)
        else:
            x = V.x(at) + (-1.0 if side < 0 else 2.4); y = V.y(m)
            sz = 1.9 if not small else 1.5
            V.p.add(f'<text class="dimt" x="{f(x)}" y="{f(y)}" font-size="{sz}" text-anchor="middle" transform="rotate(-90 {f(x)} {f(y)})">{val}</text>')

def axis_bubbles(V, xs, ys, xlabels, ylabels, top, left, bottom=None, right=None, r=2.6):
    for p, lb in zip(xs, xlabels):
        for edge in [e for e in (top, bottom) if e is not None]:
            up = edge == top
            y = V.y(edge) + (-r if up else r)
            V.p.add(f'<line class="axis" x1="{f(V.x(p))}" y1="{f(y + (r if up else -r))}" x2="{f(V.x(p))}" y2="{f(y + (r if up else -r) + (6 if up else -6))}"/>')
            V.p.add(f'<circle class="bubble" cx="{f(V.x(p))}" cy="{f(y)}" r="{r}"/>')
            V.p.add(f'<text class="bt" x="{f(V.x(p))}" y="{f(y + 0.85)}" font-size="2.4" text-anchor="middle">{lb}</text>')
    for p, lb in zip(ys, ylabels):
        for edge in [e for e in (left, right) if e is not None]:
            lf = edge == left
            x = V.x(edge) + (-r if lf else r)
            V.p.add(f'<line class="axis" x1="{f(x + (r if lf else -r))}" y1="{f(V.y(p))}" x2="{f(x + (r if lf else -r) + (6 if lf else -6))}" y2="{f(V.y(p))}"/>')
            V.p.add(f'<circle class="bubble" cx="{f(x)}" cy="{f(V.y(p))}" r="{r}"/>')
            V.p.add(f'<text class="bt" x="{f(x)}" y="{f(V.y(p) + 0.85)}" font-size="2.4" text-anchor="middle">{lb}</text>')

def level(V, u, z, label, side=1, note=''):
    """Level marker (elevation/section): open triangle on the level line + value."""
    x, y = V.x(u), V.y(z)
    s = 1.6
    V.p.add(f'<path class="lvl" d="M{f(x)},{f(y)} l{-s},{-s * 1.4} h{2 * s} z"/>')
    V.p.add(f'<line class="thin" x1="{f(x)}" y1="{f(y - s * 1.4)}" x2="{f(x + side * 14)}" y2="{f(y - s * 1.4)}"/>')
    V.p.add(f'<line class="thin" x1="{f(x - 3 * side)}" y1="{f(y)}" x2="{f(x + side * 3)}" y2="{f(y)}"/>')
    tx = x + side * 7.5
    V.p.add(f'<text class="lvlt" x="{f(tx)}" y="{f(y - s * 1.4 - 0.7)}" font-size="2.0" text-anchor="middle">{esc(label)}</text>')
    if note: V.p.add(f'<text class="note" x="{f(tx)}" y="{f(y + 2.4)}" font-size="1.6" text-anchor="middle">{esc(note)}</text>')

def plan_level(V, u, v, label):
    x, y = V.x(u), V.y(v)
    V.p.add(f'<g class="plvl"><circle cx="{f(x)}" cy="{f(y)}" r="1.3"/><path d="M{f(x - 1.3)},{f(y)} h2.6 M{f(x)},{f(y - 1.3)} v2.6"/>'
            f'<path class="fill" d="M{f(x)},{f(y)} v-1.3 a1.3,1.3 0 0 1 1.3,1.3 z M{f(x)},{f(y)} v1.3 a1.3,1.3 0 0 1 -1.3,-1.3 z"/></g>')
    V.p.add(f'<text class="lvlt" x="{f(x + 2.0)}" y="{f(y + 0.7)}" font-size="1.9">{esc(label)}</text>')

def title_under(V, cx_u, v, title, scale_txt, page):
    x, y = V.x(cx_u), V.y(v)
    page.add(f'<text class="dtitle" x="{f(x)}" y="{f(y)}" text-anchor="middle" font-size="5.2">{esc(title)}</text>')
    page.add(f'<line class="tline" x1="{f(x - 34)}" y1="{f(y + 2.2)}" x2="{f(x + 34)}" y2="{f(y + 2.2)}"/>')
    page.add(f'<text class="dsub" x="{f(x)}" y="{f(y + 6.4)}" text-anchor="middle" font-size="2.6">{esc(scale_txt)}</text>')

def section_mark(V, u1, v1, u2, v2, name, dx, dy):
    """Section cut line on a plan, (dx, dy) = view direction (model units)."""
    V.p.add(f'<line class="cutline" x1="{f(V.x(u1))}" y1="{f(V.y(v1))}" x2="{f(V.x(u2))}" y2="{f(V.y(v2))}"/>')
    for (u, v) in ((u1, v1), (u2, v2)):
        x, y = V.x(u), V.y(v)
        V.p.add(f'<circle class="secb" cx="{f(x)}" cy="{f(y)}" r="2.6"/>')
        V.p.add(f'<text class="secbt" x="{f(x)}" y="{f(y + 0.9)}" font-size="2.6" text-anchor="middle">{name}</text>')
        ax, ay = x + dx * 4.2, y + dy * 4.2
        px_, py_ = -dy, dx
        V.p.add(f'<path class="secarrow" d="M{f(x + dx * 2.6 + px_ * 1.5)},{f(y + dy * 2.6 + py_ * 1.5)} L{f(ax)},{f(ay)} L{f(x + dx * 2.6 - px_ * 1.5)},{f(y + dy * 2.6 - py_ * 1.5)} z"/>')

# ---------------------------------------------------------------- plans
def wall_segments(w, cut_h=1.2):
    """Return (solid spans, openings) for a wall at plan cut height."""
    axis, at, a0, a1, t, ops, out, mat = w
    ops = sorted(ops, key=lambda o: o['a'])
    solid, u = [], a0
    for o in ops:
        solid.append((u, o['a']))
        if o['kind'] == 'win' and o['sill'] > cut_h:   # cửa sổ cao: tường vẫn bị cắt, vẽ nét khuất
            solid.append((o['a'], o['b']))
        u = o['b']
    solid.append((u, a1))
    return [(p, q) for p, q in solid if q - p > 1e-4], ops

def wall_rect(V, axis, at, p, q, t, cls):
    if axis == 'x': V.rect(p, q, at - t / 2, at + t / 2, cls)
    else: V.rect(at - t / 2, at + t / 2, p, q, cls)

def draw_walls_plan(V, walls):
    for w in walls:
        axis, at, a0, a1, t, ops, out, mat = w
        spans, ops = wall_segments(w)
        for p, q in spans:
            wall_rect(V, axis, at, p, q, t, 'poche' if mat == 'wall' else 'poche clad')
    for w in walls:
        axis, at, a0, a1, t, ops, out, mat = w
        for o in ops:
            draw_opening_plan(V, axis, at, t, o, out)

def L(V, axis, at, u1, off1, u2, off2, cls='thin'):
    if axis == 'x': V.line(u1, at + off1, u2, at + off2, cls)
    else: V.line(at + off1, u1, at + off2, u2, cls)

def draw_opening_plan(V, axis, at, t, o, out):
    a, b, k = o['a'], o['b'], o['kind']
    h = t / 2
    if k == 'win':
        if o['sill'] > 1.2:     # cửa sổ cao (vệ sinh, hồi): nét đứt trên tường
            L(V, axis, at, a, -h * 0.35, b, -h * 0.35, 'hiddenw'); L(V, axis, at, a, h * 0.35, b, h * 0.35, 'hiddenw')
            return
        L(V, axis, at, a, -h, b, -h, 'thin'); L(V, axis, at, a, h, b, h, 'thin')
        L(V, axis, at, a, -0.02, b, -0.02, 'glass'); L(V, axis, at, a, 0.02, b, 0.02, 'glass')
        if out:   # bậu cửa nhô ra ngoài
            L(V, axis, at, a - 0.05, out * (h + 0.05), b + 0.05, out * (h + 0.05), 'thin')
            L(V, axis, at, a - 0.05, out * h, a - 0.05, out * (h + 0.05), 'thin'); L(V, axis, at, b + 0.05, out * h, b + 0.05, out * (h + 0.05), 'thin')
        for u in (a, b): L(V, axis, at, u, -h, u, h, 'thin')
    elif k in ('door', 'door2'):
        leaves = [(a, b, o['hinge'])] if k == 'door' else [(a, (a + b) / 2, 'a'), ((a + b) / 2, b, 'b')]
        for u in (a, b): L(V, axis, at, u, -h, u, h, 'thin')
        for la, lb, hinge in leaves:
            w = lb - la
            hu = la if hinge == 'a' else lb
            other = lb if hinge == 'a' else la
            s = o['swing']
            # leaf (open 90°) + swing arc
            if axis == 'x':
                hp = (hu, at); tip = (hu, at + s * w); closed = (other, at)
            else:
                hp = (at, hu); tip = (at + s * w, hu); closed = (at, other)
            V.line(hp[0], hp[1], tip[0], tip[1], 'leaf')
            sweep = arc_sweep(V, hp, tip, closed)
            V.path(f'M{V.pt(*tip)} A{f(w * V.k)},{f(w * V.k)} 0 0 {sweep} {V.pt(*closed)}', 'arc')
            if o.get('glazed'): V.line(hp[0], hp[1], tip[0], tip[1], 'glassleaf')
    elif k == 'fold':
        for u in (a, b): L(V, axis, at, u, -h, u, h, 'thin')
        n = max(4, round((b - a) / 0.42)); pts = []
        for i in range(n + 1):
            u = a + (b - a) * i / n
            off = 0 if i % 2 == 0 else 0.16
            pts.append((u, at + off) if axis == 'x' else (at + off, u))
        V.poly(pts, 'leaf', closed=False)

def arc_sweep(V, c, p0, p1):
    x0, y0 = V.x(p0[0]) - V.x(c[0]), V.y(p0[1]) - V.y(c[1])
    x1, y1 = V.x(p1[0]) - V.x(c[0]), V.y(p1[1]) - V.y(c[1])
    return 1 if x0 * y1 - y0 * x1 > 0 else 0

def rrect(V, x1, x2, y1, y2, cls='furn', r=0.04):
    X1, X2 = sorted((V.x(x1), V.x(x2))); Y1, Y2 = sorted((V.y(y1), V.y(y2)))
    V.p.add(f'<rect class="{cls}" x="{f(X1)}" y="{f(Y1)}" width="{f(X2 - X1)}" height="{f(Y2 - Y1)}" rx="{f(r * V.k)}"/>')

def bed(V, x1, x2, y1, y2, head):
    rrect(V, x1, x2, y1, y2, 'furn', 0.03)
    s = 1 if head == 'x1' else -1
    hx = x1 if head == 'x1' else x2
    V.line(hx + s * 0.08, y1, hx + s * 0.08, y2, 'fthin')
    for a, b in ((y1 + 0.1, (y1 + y2) / 2 - 0.05), ((y1 + y2) / 2 + 0.05, y2 - 0.1)):
        p1, p2 = sorted((hx + s * 0.14, hx + s * 0.52)); rrect(V, p1, p2, a, b, 'fthin', 0.07)
    bx = hx + s * 0.75
    V.line(bx, y1, bx, y2, 'fthin')
    fx = bx + s * 0.25
    V.path(f'M{V.pt(bx, y1)} L{V.pt(fx, y1 + 0.35)} L{V.pt(fx, y2)}', 'fthin')

def wardrobe(V, x1, x2, y1, y2):
    V.rect(x1, x2, y1, y2, 'furn')
    V.line(x1, y1, x2, y2, 'fthin'); V.line(x1, y2, x2, y1, 'fthin')

def sofa(V, x1, x2, y1, y2, back):
    rrect(V, x1, x2, y1, y2, 'furn', 0.06)
    yb, s = (y1, 1) if back == 'y1' else (y2, -1)
    V.line(x1 + 0.2, yb + s * 0.2, x2 - 0.2, yb + s * 0.2, 'fthin')
    V.line(x1 + 0.2, y1, x1 + 0.2, y2, 'fthin'); V.line(x2 - 0.2, y1, x2 - 0.2, y2, 'fthin')
    n = max(2, round((x2 - x1 - 0.4) / 0.85)); cw = (x2 - x1 - 0.4) / n
    for i in range(1, n): V.line(x1 + 0.2 + i * cw, yb + s * 0.2, x1 + 0.2 + i * cw, y2 if back == 'y1' else y1, 'fthin')

def chair(V, cx, cy, deg, w=0.46, d=0.46):
    pts = rot([(cx - w / 2, cy - d / 2), (cx + w / 2, cy - d / 2), (cx + w / 2, cy + d / 2), (cx - w / 2, cy + d / 2)], cx, cy, deg)
    V.poly(pts, 'furn')
    bk = rot([(cx - w / 2, cy - d / 2 + 0.08), (cx + w / 2, cy - d / 2 + 0.08)], cx, cy, deg)
    V.line(*bk[0], *bk[1], 'fthin')

def plant(V, cx, cy, r=0.22):
    V.circle(cx, cy, r, 'fthin')
    for i in range(6):
        a = i * math.pi / 3 + 0.3
        V.line(cx, cy, cx + math.cos(a) * r * 0.85, cy + math.sin(a) * r * 0.85, 'fthin')

def stairs_plan(V, floor):
    tr = stair_treads()
    for i, (pts, z) in enumerate(tr):
        cls = 'stair'
        if floor == 1 and i >= 10: cls = 'stair hiddenst'
        V.poly(pts, cls)
    if floor == 1:
        # break line through tread 10, arrow up
        V.path(f'M{V.pt(5.4, 1.05)} L{V.pt(5.62, 0.62)} L{V.pt(5.5, 0.52)} L{V.pt(5.72, 0.05)}', 'brk')
        V.poly([(4.54, 1.95), (4.54, 1.0), (4.54, 0.55), (5.5, 0.55)], 'walk', closed=False)
        V.circle(4.54, 1.95, 0.05, 'walkdot')
        arrow(V, 5.5, 0.55, 1, 0)
        V.text(4.54, 2.25, 'LÊN', 'small', 1.7, weight=600)
    else:
        V.poly([(6.8, 0.55), (4.54, 0.55), (4.54, 1.9)], 'walk', closed=False)
        V.circle(6.8, 0.55, 0.05, 'walkdot')
        arrow(V, 4.54, 1.9, 0, 1)
        V.text(5.95, 0.42, 'XUỐNG', 'small', 1.7, weight=600)

def arrow(V, u, v, du, dv):
    x, y = V.x(u), V.y(v)
    px, py = -dv, du
    V.p.add(f'<path class="arrowh" d="M{f(x + du * 1.4)},{f(y + dv * 1.4)} L{f(x + px * 0.8)},{f(y + py * 0.8)} L{f(x - px * 0.8)},{f(y - py * 0.8)} z"/>')

def room_labels(V, rooms):
    for name, area, u, v in rooms:
        if name == 'LỐI ĐI':
            V.text(u, v, name, 'room', 2.1, rot=-90, weight=600); V.text(u + 0.2, v, area, 'area', 1.7, rot=-90); continue
        if name == 'SÂN SAU':
            V.text(u, v, name, 'room', 2.3, weight=600); V.text(u, v + 0.28, area, 'area', 1.8); continue
        V.text(u, v, name, 'room', 2.5, weight=600)
        if area: V.text(u, v + 0.3, area, 'area', 1.9)

def plan_dims(V, floor):
    """Exterior dimension chains: openings (inner), axes, overall."""
    if floor == 1:
        top_open = [0, 0.9, 2.1, 9.6, 11.2, 13.0, 15.0, 17]
        top_ax = [0, 3, 4, 7, 9, 13, 17]
        bot_open = [0, 0.8, 2.2, 4.8, 7.6, 10.2, 11.8, 14.2, 15.8, 17]
        bot_ax = [0, 3, 9, 13, 17]
        left = [0, 3, 7]
        right_open = [0, 4.5, 5.5, 7]
        right_ax = [0, 3, 7]
    else:
        top_open = [0, 4, 8.0, 10.0, 12.0, 12.8, 14.0, 14.6, 15, 17]
        top_ax = [0, 4, 7, 11, 13.5, 15, 17]
        bot_open = [0, 7, 8.2, 9.8, 12.2, 13.8, 15, 17]
        bot_ax = [0, 4, 7, 11, 15, 17]
        left = [0, 2, 3, 3.5, 7]
        right_open = [0, 2.6, 3.4, 4.6, 5.8, 7]
        right_ax = [0, 2, 3.5, 7]
    e = -0.1
    dim_chain(V, 'x', top_open, -0.75, -1, ext_from=-0.12)
    dim_chain(V, 'x', top_ax, -1.25, -1)
    dim_chain(V, 'x', [0, 17], -1.75, -1)
    dim_chain(V, 'x', bot_open, 7.75 + (0.55 if floor == 1 else 0), 1, ext_from=7.12)
    dim_chain(V, 'x', bot_ax, 8.25 + (0.55 if floor == 1 else 0), 1)
    dim_chain(V, 'x', [0, 17], 8.75 + (0.55 if floor == 1 else 0), 1)
    dim_chain(V, 'y', left, -0.8, -1, ext_from=-0.12)
    dim_chain(V, 'y', [0, 7], -1.3, -1)
    dim_chain(V, 'y', right_open, 17.8, -1, ext_from=17.12)
    dim_chain(V, 'y', right_ax, 18.3, -1)

def plan_page_common(V, floor):
    xs = [0, 3, 4, 7, 9, 11, 13, 15, 17]
    axis_bubbles(V, xs, [0, 3, 7], [str(i + 1) for i in range(len(xs))], ['A', 'B', 'C'], top=-2.15, left=-1.75)

def plan1(V):
    # nền + bậc tam cấp + bồn cây trước nhà
    V.rect(-0.15, 17.15, -0.15, 7.15, 'plinth')
    for (a, b) in ((2.6, 4.4), (7.9, 9.9)):
        V.rect(a, b, 7.2, 7.75, 'furn'); V.rect(a + 0.08, b - 0.08, 7.28, 7.67, 'fthin')
        for i in range(int((b - a) / 0.35)): plant(V, a + 0.22 + i * 0.35, 7.47, 0.14)
    V.rect(0.7, 2.3, 7.15, 7.55, 'furn'); V.rect(0.7, 2.3, 7.55, 7.95, 'furn')
    V.text(1.5, 7.83, 'TAM CẤP', 'small', 1.4)
    # sàn gỗ (hatch nhạt)
    for (x1, x2, y1, y2) in ((0.1, 2.9, 0.1, 2.9), (9.06, 12.94, 3.06, 6.9), (13.06, 16.9, 3.06, 6.9)):
        V.rect(x1, x2, y1, y2, 'wood')
    V.rect(4.4, 7.6, 4.35, 6.25, 'rug'); V.rect(9.3, 12.0, 4.0, 6.0, 'rug'); V.rect(14.0, 16.6, 4.0, 6.0, 'rug')
    # nội thất
    V.rect(0.5, 2.5, 0.12, 0.62, 'furn'); V.rect(0.9, 2.1, 0.12, 0.42, 'fthin'); V.text(1.5, 0.48, 'BÀN THỜ', 'small', 1.4)
    V.rect(0.1, 0.5, 3.4, 5.4, 'furn'); V.text(0.3, 4.4, 'TỦ GIÀY', 'small', 1.3, rot=-90)
    V.rect(1.0, 2.2, 3.2, 3.55, 'furn')
    sofa(V, 4.6, 7.4, 3.25, 4.1, 'y1')
    rrect(V, 5.45, 6.55, 4.65, 5.25, 'furn', 0.05)
    V.rect(5.0, 7.0, 6.42, 6.82, 'furn'); V.text(6.0, 6.7, 'KỆ TIVI', 'small', 1.3)
    chair(V, 8.25, 4.75, 115 + 90, 0.75, 0.8); chair(V, 3.85, 5.0, -75 + 90, 0.72, 0.72)
    for (u, v, r) in ((8.55, 6.5, 0.26), (3.55, 6.55, 0.22), (2.55, 6.45, 0.24)): plant(V, u, v, r)
    rrect(V, 7.45, 10.15, 1.0, 2.0, 'furn', 0.03)
    for px in (7.69, 8.19, 8.69, 9.19, 9.69): chair(V, px, 0.62, 0, 0.42, 0.42); chair(V, px, 2.38, 180, 0.42, 0.42)
    chair(V, 6.95, 1.5, -90, 0.42, 0.42); chair(V, 10.65, 1.5, 90, 0.42, 0.42)
    V.rect(12.25, 13.0, 0.1, 0.78, 'furn'); V.line(12.25, 0.1, 13.0, 0.78, 'fthin'); V.text(12.62, 0.95, 'TỦ LẠNH', 'small', 1.3)
    V.poly([(13.0, 0.1), (16.9, 0.1), (16.9, 1.87), (16.28, 1.87), (16.28, 0.72), (13.0, 0.72)], 'furn')
    V.rect(13.7, 14.7, 0.18, 0.6, 'fthin')
    for (u, v) in ((13.95, 0.29), (14.45, 0.29), (13.95, 0.49), (14.45, 0.49)): V.circle(u, v, 0.08, 'fthin')
    rrect(V, 15.2, 15.9, 0.18, 0.6, 'fthin', 0.06); V.circle(15.55, 0.3, 0.03, 'fthin')
    V.rect(15.1, 16.9, 0.1, 0.45, 'hiddenf')
    plant(V, 16.6, 1.4, 0.15)
    V.text(14.6, 1.0, 'BẾP', 'small', 1.4)
    bed(V, 9.1, 11.1, 4.2, 5.8, 'x1'); bed(V, 14.95, 16.9, 4.2, 5.8, 'x2')
    wardrobe(V, 12.3, 12.92, 4.85, 6.88); wardrobe(V, 13.08, 13.7, 4.85, 6.88)
    for (u, v) in ((9.35, 3.82), (9.35, 6.18), (16.65, 3.82), (16.65, 6.18)): V.rect(u - 0.2, u + 0.2, v - 0.2, v + 0.2, 'furn'); V.circle(u, v, 0.1, 'fthin')
    stairs_plan(V, 1)
    draw_walls_plan(V, WALLS1)
    room_labels(V, ROOMS1)
    plan_level(V, 6.55, 2.6, '±0.000')
    plan_dims(V, 1)
    plan_page_common(V, 1)
    section_mark(V, 5.6, -2.95, 5.6, 9.75, 'A', 1, 0)
    section_mark(V, -2.6, 1.45, 19.0, 1.45, 'B', 0, -1)

def plan2(V):
    # sàn: gỗ sân thượng, đá sân sau
    V.rect(-0.1, 4.0, -0.1, 7.1, 'deck'); V.rect(4.0, 7.0, 3.0, 7.1, 'deck')
    V.rect(15.0, 17.1, -0.1, 7.1, 'stone')
    V.rect(11.0, 15.0, 0, 2.0, 'tile')
    V.rect(7.06, 10.94, 3.56, 6.9, 'wood'); V.rect(11.06, 14.9, 3.56, 6.9, 'wood')
    # ô thông tầng thang
    V.rect(4.1, 7.0, 0.1, 2.0, 'void')
    stairs_plan(V, 2)
    # lan can
    for axis, at, u1, u2, wh in RAILS2:
        t = 0.15 if wh else 0.06
        if axis == 'x': V.rect(u1, u2, at - t / 2, at + t / 2, 'parapet' if wh else 'railp')
        else: V.rect(at - t / 2, at + t / 2, u1, u2, 'parapet' if wh else 'railp')
        if wh:
            if axis == 'x': V.line(u1, at, u2, at, 'glass')
            else: V.line(at, u1, at, u2, 'glass')
    V.rect(7.6, 10.4, 1.0, 2.45, 'rug'); V.rect(7.6, 10.0, 4.0, 6.6, 'rug'); V.rect(12.0, 14.4, 4.0, 6.6, 'rug')
    # SHC
    sofa(V, 7.9, 10.2, 2.55, 3.35, 'y2')
    V.rect(8.2, 9.8, 0.25, 0.65, 'furn'); V.rect(8.45, 9.55, 0.13, 0.17, 'fthin'); V.text(9.0, 0.53, 'KỆ TIVI', 'small', 1.3)
    rrect(V, 8.5, 9.6, 1.5, 2.0, 'furn', 0.05)
    plant(V, 7.45, 0.55, 0.24)
    # tắm + WC
    V.rect(11.06, 12.28, 0.1, 1.12, 'furn'); V.line(11.06, 0.1, 12.28, 1.12, 'fthin'); V.line(11.06, 1.12, 12.28, 0.1, 'fthin')
    V.circle(11.67, 0.61, 0.05, 'fthin')
    V.line(11.06, 1.12, 12.28, 1.12, 'glass')
    V.rect(12.47, 13.4, 0.1, 0.57, 'furn'); V.p.add(ellipse(V, 12.93, 0.33, 0.28, 0.16))
    V.rect(14.05, 14.45, 0.1, 0.3, 'furn'); V.p.add(ellipse(V, 14.25, 0.58, 0.18, 0.24))
    # PN3, PN4
    bed(V, 7.1, 9.1, 4.46, 6.05, 'x1'); bed(V, 12.9, 14.9, 4.46, 6.05, 'x2')
    wardrobe(V, 10.3, 10.94, 4.85, 6.88); wardrobe(V, 11.06, 11.7, 4.85, 6.88)
    for (u, v) in ((7.35, 4.06), (14.65, 4.06)): V.rect(u - 0.2, u + 0.2, v - 0.2, v + 0.2, 'furn'); V.circle(u, v, 0.1, 'fthin')
    # sân thượng: bàn cafe + chậu cây
    for (u, v) in ((1.2, 1.1), (1.2, 3.4), (1.2, 5.7), (3.0, 5.7), (5.2, 5.7)):
        V.circle(u, v, 0.32, 'furn'); chair(V, u - 0.62, v, -90, 0.44, 0.44); chair(V, u + 0.62, v, 90, 0.44, 0.44)
    for (u, v, a) in ((2.6, 0.32, 0), (4.75, 3.3, 0), (16.55, 1.0, 90), (16.55, 6.0, 90)):
        pts = rot([(u - 0.5, v - 0.18), (u + 0.5, v - 0.18), (u + 0.5, v + 0.18), (u - 0.5, v + 0.18)], u, v, a)
        V.poly(pts, 'furn')
        for d in (-0.3, 0, 0.3):
            c = rot([(u + d, v)], u, v, a)[0]; plant(V, c[0], c[1], 0.13)
    for (u, v, s) in ((0.4, 0.4, 1.4), (0.45, 6.6, 1.5), (3.6, 6.6, 1.3), (15.5, 6.6, 1.3)): plant(V, u, v, 0.16 * s)
    # pergola (nét đứt phía trên) + cột
    V.rect(0.08, 6.92, 3.15, 7.0, 'over')
    for (u, v) in ((0.15, 3.3), (0.15, 6.85), (3.5, 6.85), (6.85, 6.85), (6.85, 3.3)): V.rect(u - 0.07, u + 0.07, v - 0.07, v + 0.07, 'post')
    V.text(3.5, 4.35, 'GIÀN PERGOLA GỖ PHÍA TRÊN', 'note', 1.5)
    # mép mái thái phía trên
    V.rect(*EAVE, 'over')
    draw_walls_plan(V, WALLS2)
    room_labels(V, ROOMS2)
    plan_level(V, 1.75, 2.95, '+3.300')
    plan_level(V, 12.2, 2.95, '+3.300')
    plan_dims(V, 2)
    plan_page_common(V, 2)
    section_mark(V, 5.6, -2.95, 5.6, 9.3, 'A', 1, 0)
    section_mark(V, -2.6, 1.45, 19.0, 1.45, 'B', 0, -1)

def ellipse(V, u, v, rx, ry):
    return f'<ellipse class="furn" cx="{f(V.x(u))}" cy="{f(V.y(v))}" rx="{f(rx * V.k)}" ry="{f(ry * V.k)}"/>'

def roofplan(V):
    V.rect(-0.15, 17.15, -0.15, 7.15, 'plinthfaint')
    # sân thượng + sân sau seen from above
    V.rect(-0.1, 4.0, -0.1, 7.1, 'deck'); V.rect(4.0, 7.0, 3.0, 7.1, 'deck'); V.rect(15.0, 17.1, -0.1, 7.1, 'stone')
    for axis, at, u1, u2, wh in RAILS2[2:]:
        if axis == 'x': V.rect(u1, u2, at - 0.075, at + 0.075, 'parapet')
        else: V.rect(at - 0.075, at + 0.075, u1, u2, 'parapet')
    # pergola
    V.rect(0.08, 6.92, 3.23, 3.37, 'woodb'); V.rect(0.08, 6.92, 6.78, 6.92, 'woodb')
    px = 0.2
    while px < 6.9:
        V.rect(px, px + 0.06, 3.15, 7.0, 'woodb'); px += 0.32
    V.text(3.5, 5.1, 'GIÀN PERGOLA GỖ', 'notebg', 1.9, weight=600)
    V.text(3.5, 5.45, 'SÂN THƯỢNG +3.300', 'notebg', 1.6)
    V.text(16.0, 3.5, 'SÂN SAU +3.300', 'note', 1.6, rot=-90)
    # khối mái bằng ô thang + giếng trời
    V.rect(*STAIR_BOX, 'flat')
    V.rect(*SKYLIGHT, 'skylight')
    V.line(SKYLIGHT[0], SKYLIGHT[2], SKYLIGHT[1], SKYLIGHT[3], 'fthin'); V.line(SKYLIGHT[0], SKYLIGHT[3], SKYLIGHT[1], SKYLIGHT[2], 'fthin')
    V.text(5.5, 2.55, 'MÁI BẰNG BTCT', 'small', 1.7, weight=600)
    V.text(5.5, 2.85, 'đỉnh +7.090', 'small', 1.5)
    V.text(5.5, 0.42, 'GIẾNG TRỜI KÍNH', 'small', 1.4)
    # mái thái: hatch ngói song song với mép
    x0, x1, y0, y1 = EAVE; r1, r2, yc = RIDGE
    faces = {'front': [(x0, y1), (x1, y1), (r2, yc), (r1, yc)], 'back': [(x1, y0), (x0, y0), (r1, yc), (r2, yc)],
             'left': [(x0, y0), (x0, y1), (r1, yc)], 'right': [(x1, y1), (x1, y0), (r2, yc)]}
    for name, pts in faces.items():
        V.poly(pts, 'roof')
    # tile courses
    step = 0.33
    k = 1
    while y0 + k * step < yc - 0.02:
        d = k * step
        V.line(x0 + d, y0 + d, x1 - d, y0 + d, 'tilel'); V.line(x0 + d, y1 - d, x1 - d, y1 - d, 'tilel')
        V.line(x0 + d, y0 + d, x0 + d, y1 - d, 'tilel'); V.line(x1 - d, y0 + d, x1 - d, y1 - d, 'tilel')
        k += 1
    for pts in faces.values(): V.poly(pts, 'roofedge')
    V.line(r1, yc, r2, yc, 'ridge')
    for a in ((x0, y0), (x0, y1)): V.line(a[0], a[1], r1, yc, 'ridge')
    for a in ((x1, y0), (x1, y1)): V.line(a[0], a[1], r2, yc, 'ridge')
    # slope arrows + labels
    for (u, v, du, dv) in ((11.0, 1.4, 0, -1), (11.0, 5.6, 0, 1), (8.0, 3.5, -1, 0), (14.0, 3.5, 1, 0)):
        V.line(u - du * 0.6, v - dv * 0.6, u + du * 0.6, v + dv * 0.6, 'slope'); arrow(V, u + du * 0.6, v + dv * 0.6, du, dv)
    V.text(11.0, 1.1, 'i = 52% (≈ 27°)', 'notebg', 1.6)
    V.text(11.0, 6.15, 'MÁI NGÓI XÁM', 'notebg', 1.9, weight=600)
    V.text(11.0, 6.45, 'đỉnh nóc +8.800', 'notebg', 1.6)
    V.text(11.0, 3.35, 'NÓC', 'notebg', 1.5)
    # dims
    dim_chain(V, 'x', [0, 4, 7, 15, 17], -1.15, -1, ext_from=-0.15)
    dim_chain(V, 'x', [x0, r1, r2, x1], -1.65, -1)
    dim_chain(V, 'x', [0, 17], 8.25, 1, ext_from=7.15)
    dim_chain(V, 'x', [x0, 7, 15, x1], 7.85, 1)
    dim_chain(V, 'y', [y0, 0, 7, y1], 17.75, -1, ext_from=x1 + 0.05)
    dim_chain(V, 'y', [y0, yc, y1], 18.25, -1)
    dim_chain(V, 'y', [0, 3.2, 7], -0.85, -1, ext_from=-0.15)

def siteplan(V):
    V.rect(-1.2, 18.2, 7.15, 10.85, 'pave'); V.rect(-1.2, 18.2, 11.05, 12.8, 'curb')
    V.rect(-1.3, 18.3, -4.2, 11.05, 'lotline')
    V.rect(-0.15, 17.15, -0.15, 7.15, 'bldg')
    V.rect(*STAIR_BOX, 'bldgfaint')
    x0, x1, y0, y1 = EAVE
    V.rect(x0, x1, y0, y1, 'bldgroof')
    V.rect(-0.1, 4.0, -0.1, 7.1, 'terr'); V.rect(4.0, 7.0, 3.2, 7.1, 'terr'); V.rect(15.55, 17.1, -0.1, 7.1, 'terr')
    for (u, v, r) in ((-3.2, 9.2, 1.4), (4.5, -5.4, 1.4), (12.5, -5.8, 1.6), (20.4, 8.6, 1.3)):
        V.circle(u, v, r, 'treec')
    V.text(8.5, 9.1, 'SÂN TRƯỚC', 'small', 1.6)
    V.text(8.5, 12.1, 'VỈA HÈ', 'small', 1.5)
    V.text(8.5, -2.2, 'SÂN VƯỜN SAU', 'small', 1.6)
    V.text(8.5, 3.6, 'NHÀ 2 TẦNG', 'small', 1.7, weight=600)
    V.text(8.5, 14.6, 'ĐƯỜNG', 'small', 1.7, weight=600)
    for (a, b) in ((0.3, 3.2), (8.6, 12.4)):
        V.rect(a, b, 10.85, 11.05, 'gate')
    V.text(1.75, 10.6, 'CỔNG ĐI BỘ', 'small', 1.2); V.text(10.5, 10.6, 'CỔNG XE', 'small', 1.2)
    # north arrow (giả định: mặt tiền hướng Nam)
    nx, ny = V.x(16.3), V.y(-2.7)
    V.p.add(f'<g class="north"><circle cx="{f(nx)}" cy="{f(ny)}" r="3.4"/><path d="M{f(nx)},{f(ny - 3.0)} L{f(nx + 1.5)},{f(ny + 2.2)} L{f(nx)},{f(ny + 1.2)} z"/>'
            f'<text x="{f(nx)}" y="{f(ny - 4.2)}" font-size="2.2" text-anchor="middle">B</text></g>')

# ---------------------------------------------------------------- elevations & sections (box painter)
class Solid:
    def __init__(self, poly, z1, z2, cls): self.poly, self.z1, self.z2, self.cls = poly, z1, z2, cls

def box(x1, x2, y1, y2, z1, z2, cls): return Solid([(x1, y1), (x2, y1), (x2, y2), (x1, y2)], z1, z2, cls)

def seg_box(axis, at, u1, u2, z1, z2, t, cls, off=0):
    if u2 - u1 < 1e-4 or z2 - z1 < 1e-4: return None
    if axis == 'x': return box(u1, u2, at + off - t / 2, at + off + t / 2, z1, z2, cls)
    return box(at + off - t / 2, at + off + t / 2, u1, u2, z1, z2, cls)

def build_solids():
    S = []
    def add(s):
        if s: S.append(s)
    add(box(-0.15, 17.15, -0.15, 7.15, GROUND, F1, 'plinth'))
    add(box(0.7, 2.3, 7.15, 7.55, GROUND, GROUND + 0.3, 'plinth')); add(box(0.7, 2.3, 7.15, 7.95, GROUND, GROUND + 0.15, 'plinth'))
    for (a, b) in ((2.6, 4.4), (7.9, 9.9)): add(box(a, b, 7.2, 7.75, GROUND, GROUND + 0.45, 'planter'))
    for walls, base, h in ((WALLS1, F1, FH), (WALLS2, F2, WALL2)):
        for axis, at, a0, a1, t, ops, out, mat in walls:
            ops = sorted(ops, key=lambda o: o['a']); u = a0
            for o in ops:
                add(seg_box(axis, at, u, o['a'], base, base + h, t, mat))
                sill = o['sill'] if o['kind'] == 'win' else 0
                head = o['head']
                if sill: add(seg_box(axis, at, o['a'], o['b'], base, base + sill, t, mat))
                add(seg_box(axis, at, o['a'], o['b'], base + head, base + h, t, mat))
                if o['kind'] == 'win':
                    add(seg_box(axis, at, o['a'], o['b'], base + sill, base + head, 0.06, 'win'))
                    if out: add(seg_box(axis, at, o['a'] - 0.05, o['b'] + 0.05, base + sill - 0.05, base + sill, 0.1, 'sill', off=out * (t / 2 + 0.03)))
                elif o['kind'] in ('door', 'door2'):
                    add(seg_box(axis, at, o['a'], o['b'], base, base + head, 0.05, 'door2' if o['kind'] == 'door2' else ('doorg' if o.get('glazed') else 'door')))
                elif o['kind'] == 'fold':
                    add(seg_box(axis, at, o['a'], o['b'], base, base + head, 0.05, 'fold'))
                u = o['b']
            add(seg_box(axis, at, u, a1, base, base + h, t, mat))
            add(seg_box(axis, at, a0, a1, base, base + h, t, 'outline'))
    # sàn tầng 2 + viền
    for (x1, x2, y1, y2) in SLABS2: add(box(x1, x2, y1, y2, F2 - 0.15, F2, 'slab'))
    for b in ((-0.16, 17.16, 7.08, 7.16), (-0.16, 17.16, -0.16, -0.08), (-0.16, -0.08, -0.16, 7.16), (17.08, 17.16, -0.16, 7.16)):
        add(box(*b, F2 - 0.25, F2 + 0.02, 'band'))
    # lan can
    for axis, at, u1, u2, wh in RAILS2:
        if wh: add(seg_box(axis, at, u1, u2, F2, F2 + wh, 0.15, 'parapet')); add(seg_box(axis, at, u1, u2, F2 + wh, F2 + wh + 0.03, 0.19, 'sill'))
        add(seg_box(axis, at, u1, u2, F2 + wh + 0.04, F2 + 1.02, 0.015, 'rglass'))
        add(seg_box(axis, at, u1, u2, F2 + 1.02, F2 + 1.07, 0.06, 'rail'))
        n = max(1, round((u2 - u1) / 1.4))
        for i in range(n + 1):
            uu = u1 + (u2 - u1) * i / n
            add(seg_box(axis, at, max(u1, uu - 0.025), min(u2, uu + 0.025), F2 + wh, F2 + 1.02, 0.05, 'rail'))
    # pergola
    pz = F2 + 2.75
    for (u, v) in ((0.15, 3.3), (0.15, 6.85), (3.5, 6.85), (6.85, 6.85), (6.85, 3.3)): add(box(u - 0.07, u + 0.07, v - 0.07, v + 0.07, F2, pz, 'timber'))
    add(box(0.08, 6.92, 3.23, 3.37, pz - 0.2, pz, 'timber')); add(box(0.08, 6.92, 6.78, 6.92, pz - 0.2, pz, 'timber'))
    px = 0.2
    while px < 6.9: add(box(px, px + 0.06, 3.15, 7.0, pz, pz + 0.14, 'timber')); px += 0.32
    # mái
    add(box(3.9, 7.1, -0.1, 3.1, TOP2, ROOFB, 'slab')); add(box(7.0, 15.1, -0.1, 7.1, TOP2, ROOFB, 'slab'))
    add(box(*STAIR_BOX, ROOFB, ROOFB + 0.4, 'block')); add(box(*STAIR_BOX, ROOFB + 0.4, ROOFB + 0.44, 'band'))
    add(box(*SKYLIGHT, ROOFB + 0.4, ROOFB + 0.48, 'win'))
    x0, x1, y0, y1 = EAVE
    add(box(x0, x1, y0, y1, ROOFB - 0.1, ROOFB + 0.14, 'fascia'))
    # cầu thang
    for pts, z in stair_treads(): add(Solid(pts, F1, F1 + z, 'tread'))
    return S

ELEV_FILL = {'plinth': '#d9d4cb', 'wall': '#ffffff', 'parapet': '#ffffff', 'block': '#ffffff', 'clad': '#e9dccb', 'win': GLASS, 'sill': '#f1efea', 'door': '#e7d6bf', 'door2': '#e7d6bf',
             'doorg': '#e7d6bf', 'fold': '#efe4d4', 'slab': '#ffffff', 'band': '#5d646b', 'rglass': 'none', 'rail': '#3b4248', 'timber': '#b98d62',
             'fascia': '#4d555c', 'tread': '#ffffff', 'planter': '#e4ded4'}

def view_params(view):
    """(u(x,y), near-face depth key(x-range,y-range) → larger = nearer, mirror)"""
    if view == 'front': return lambda x, y: x, lambda xs, ys: max(ys)
    if view == 'back': return lambda x, y: 17 - x, lambda xs, ys: -min(ys)
    if view == 'left': return lambda x, y: y, lambda xs, ys: -min(xs)
    if view == 'right': return lambda x, y: 7 - y, lambda xs, ys: max(xs)

def cut_range(poly, plane_axis, c):
    """Intersection of a polygon footprint with x=c (plane_axis 'x') or y=c → (lo, hi) along the other axis, or None."""
    vals = []
    n = len(poly)
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        a1, a2 = (x1, x2) if plane_axis == 'x' else (y1, y2)
        b1, b2 = (y1, y2) if plane_axis == 'x' else (x1, x2)
        if (a1 - c) * (a2 - c) < 0 or (abs(a1 - a2) > 1e-9 and min(a1, a2) <= c <= max(a1, a2)):
            if abs(a2 - a1) < 1e-9: continue
            t = (c - a1) / (a2 - a1); vals.append(b1 + t * (b2 - b1))
    if len(vals) < 2: return None
    return min(vals), max(vals)

def draw_solid_face(V, cls, u1, u2, z1, z2):
    if cls == 'outline':
        V.rect(u1, u2, z1, z2, 'eloutline'); return
    fill = ELEV_FILL.get(cls, '#ffffff')
    style = f'fill:{fill}'
    V.rect(u1, u2, z1, z2, 'el ' + cls, style)
    w, h = abs(u2 - u1), z2 - z1
    if cls == 'win' and h > 0.2 and w > 0.2:
        f_ = 0.055
        V.rect(u1 + f_, u2 - f_, z1 + f_, z2 - f_, 'elthin', 'fill:none')
        if w > 1.1:
            m = (u1 + u2) / 2; V.line(m, z1 + f_, m, z2 - f_, 'elthin')
        for i in range(2):   # glare strokes
            a = u1 + w * (0.25 + 0.2 * i)
            V.line(a, z1 + h * 0.45, a + min(w, h) * 0.18, z1 + h * 0.62, 'glare')
    elif cls in ('door', 'doorg', 'door2'):
        if cls == 'door2':
            m = (u1 + u2) / 2; V.line(m, z1, m, z2, 'elthin')
            for a, b in ((u1, m), (m, u2)):
                V.rect(a + 0.12, b - 0.12, z1 + 0.35, z2 - 0.25, 'elthin', f'fill:{GLASS}')
        elif cls == 'doorg':
            V.rect(u1 + 0.15, u2 - 0.15, z1 + 0.5, z2 - 0.3, 'elthin', f'fill:{GLASS}')
        else:
            V.rect(u1 + 0.12, u2 - 0.12, z1 + 0.25, z2 - 0.25, 'elthin', 'fill:none')
    elif cls == 'fold':
        n = max(4, round(w / 0.42))
        for i in range(1, n): V.line(u1 + w * i / n, z1, u1 + w * i / n, z2, 'elthin')
    elif cls == 'rglass':
        V.rect(u1, u2, z1, z2, 'rglassf', f'fill:{GLASS};fill-opacity:0.35')
    elif cls == 'clad' and h > 0.3:
        n = int(w / 0.12)
        for i in range(1, n): V.line(u1 + w * i / n, z1, u1 + w * i / n, z2, 'cladl')

def render_view(V, view, solids, plane=None, extra=None):
    """plane: (axis 'x'|'y', c, keep_side) — keep solids on the far side; straddling ones are drawn as cuts."""
    U, depth = view_params(view)
    items, cuts = [], []
    for s in solids:
        xs = [p[0] for p in s.poly]; ys = [p[1] for p in s.poly]
        if plane:
            pa, c, side = plane
            vals = xs if pa == 'x' else ys
            lo, hi = min(vals), max(vals)
            if (side > 0 and hi <= c) or (side < 0 and lo >= c): continue      # in front of the cut
            if lo < c < hi:
                if s.cls == 'outline': continue
                r = cut_range(s.poly, pa, c)
                if r:
                    us = [U(r[0], c) if pa == 'y' else U(c, r[0]), U(r[1], c) if pa == 'y' else U(c, r[1])]
                    cuts.append((min(us), max(us), s.z1, s.z2, s.cls))
                continue
        us = [U(x, y) for x, y in s.poly]
        items.append((depth(xs, ys), min(us), max(us), s.z1, s.z2, s.cls))
    # roof faces (3D polygons)
    faces = roof_faces()
    roof_items = []
    for fc in faces:
        pts = fc
        if plane:
            pts = clip_poly3(pts, plane)
            if len(pts) < 3: continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        d = depth([cx], [cy])
        roof_items.append((d, [(U(p[0], p[1]), p[2]) for p in pts]))
    allitems = [(it[0], 'b', it) for it in items] + [(r[0] + 0.0, 'r', r) for r in roof_items]
    allitems.sort(key=lambda t: t[0])
    for _, kind, it in allitems:
        if kind == 'b':
            _, u1, u2, z1, z2, cls = it
            draw_solid_face(V, cls, u1, u2, z1, z2)
        else:
            V.poly(it[1], 'elroof')
            roof_hatch(V, it[1])
    # cuts on top
    for u1, u2, z1, z2, cls in cuts:
        if cls in ('win', 'rglass'): V.rect(u1, u2, z1, z2, 'cutglass')
        elif cls in ('door', 'doorg', 'door2', 'fold'): V.rect(u1, u2, z1, z2, 'cutdoor')
        elif cls in ('timber', 'rail'): V.rect(u1, u2, z1, z2, 'cutthin')
        else: V.rect(u1, u2, z1, z2, 'cut')
    if plane:
        for fc in faces:
            seg = plane_cut_poly3(fc, plane)
            if seg:
                (a, b) = seg
                V.line(U(a[0], a[1]), a[2], U(b[0], b[1]), b[2], 'roofcut')
    return cuts

def roof_hatch(V, pts):
    # horizontal tile courses clipped to the face polygon
    zs = [p[1] for p in pts]
    z0, z1 = min(zs), max(zs)
    z = z0 + 0.18
    while z < z1 - 0.05:
        xs = []
        n = len(pts)
        for i in range(n):
            (u1, v1), (u2, v2) = pts[i], pts[(i + 1) % n]
            if (v1 - z) * (v2 - z) < 0:
                xs.append(u1 + (z - v1) / (v2 - v1) * (u2 - u1))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]): V.line(a, z, b, z, 'tileh')
        z += 0.18

def clip_poly3(pts, plane):
    pa, c, side = plane
    idx = 0 if pa == 'x' else 1
    inside = lambda p: (p[idx] - c) * side >= 0
    out = []
    n = len(pts)
    for i in range(n):
        p, q = pts[i], pts[(i + 1) % n]
        ip, iq = inside(p), inside(q)
        if ip: out.append(p)
        if ip != iq:
            t = (c - p[idx]) / (q[idx] - p[idx]); out.append(tuple(p[j] + t * (q[j] - p[j]) for j in range(3)))
    return out

def plane_cut_poly3(pts, plane):
    pa, c, side = plane
    idx = 0 if pa == 'x' else 1
    hits = []
    n = len(pts)
    for i in range(n):
        p, q = pts[i], pts[(i + 1) % n]
        if (p[idx] - c) * (q[idx] - c) < 0:
            t = (c - p[idx]) / (q[idx] - p[idx]); hits.append(tuple(p[j] + t * (q[j] - p[j]) for j in range(3)))
    return (hits[0], hits[1]) if len(hits) >= 2 else None

def ground(V, u1, u2):
    V.line(u1, GROUND, u2, GROUND, 'groundl')
    k = u1
    while k < u2:
        V.line(k, GROUND, k - 0.25, GROUND - 0.25, 'groundh'); k += 0.25

def levels_side(V, u, side, lv):
    for z, lb, note, du in lv: level(V, u + du, z, lb, side, note)

LEVELS = [(GROUND, '−0.450', 'MẶT SÂN', -1.5), (F1, '±0.000', 'SÀN TẦNG 1', 0), (F2, '+3.300', 'SÀN TẦNG 2', 0),
          (TOP2, '+6.500', 'ĐÁY SÀN MÁI', 0), (ROOF_Z0 + ROOF_RH, '+8.800', 'ĐỈNH NÓC', 0)]

def elevation(V, view, title, solids):
    render_view(V, view, solids)
    span = 17 if view in ('front', 'back') else 7
    ground(V, -1.2, span + 1.2)
    levels_side(V, -1.0, -1, LEVELS)
    if view in ('front', 'back'):
        dim_chain(V, 'x', [0, 17], GROUND - 0.9, 1)
        pts = [0, 3, 4, 7, 9, 11, 13, 15, 17] if view == 'front' else [0, 2, 4, 6, 8, 10, 13, 14, 17]
        if view == 'front':
            dim_chain(V, 'x', [0, 4, 7, 15, 17], GROUND - 0.5, 1)
        else:
            dim_chain(V, 'x', [0, 2, 10, 13, 17], GROUND - 0.5, 1)
    else:
        dim_chain(V, 'x', [0, 7], GROUND - 0.9, 1)
        dim_chain(V, 'x', [0, 3, 7] if view == 'left' else [0, 4, 7], GROUND - 0.5, 1)
    hv = 17 if view in ('front', 'back') else 7
    dim_chain(V, 'y', [GROUND, F1, F2, TOP2, ROOFB + 0.05, ROOF_Z0 + ROOF_RH], hv + 1.0, 1)

def section(V, view, plane, title, solids, span):
    render_view(V, view, solids, plane)
    ground(V, -1.2, span + 1.2)
    levels_side(V, -1.0, -1, LEVELS[:4] + [(ROOFB + 0.44, '+7.090', 'ĐỈNH MÁI BẰNG', -1.9)])
    dim_chain(V, 'y', [GROUND, F1, F2 - 0.15, F2, TOP2, ROOFB], span + 1.0, 1)

# ---------------------------------------------------------------- sheet layout
CSS = """
@page { size: 420mm 297mm; margin: 0 }
* { box-sizing: border-box }
html, body { margin: 0; padding: 0; background: #f3f3f1 }
.sheet { width: 420mm; height: 297mm; page-break-after: always; break-after: page; background: #fff; overflow: hidden; position: relative }
.sheet:last-child { page-break-after: auto; break-after: auto }
svg { display: block; width: 420mm; height: 297mm; font-family: 'Be Vietnam Pro', 'DejaVu Sans', sans-serif }
.frame { fill: none; stroke: #1a1f24; stroke-width: .5 }
.frame2 { fill: none; stroke: #1a1f24; stroke-width: .18 }
.poche { fill: #2b3137; stroke: #1a1f24; stroke-width: .12 }
.poche.clad { fill: #6d5843 }
.thin { stroke: #1a1f24; stroke-width: .18; fill: none }
.glass { stroke: #3b7fa6; stroke-width: .25; fill: none }
.leaf { stroke: #1a1f24; stroke-width: .3; fill: none }
.glassleaf { stroke: #3b7fa6; stroke-width: .12; fill: none; stroke-dasharray: .6 .5 }
.arc { stroke: #1a1f24; stroke-width: .12; fill: none; stroke-dasharray: 1 .6 }
.hiddenw { stroke: #fff; stroke-width: .16; fill: none; stroke-dasharray: 1.1 .7 }
.hidden { stroke: #1a1f24; stroke-width: .16; fill: none; stroke-dasharray: 1.1 .7 }
.furn { fill: #fff; stroke: #5a636b; stroke-width: .16 }
.fthin { fill: none; stroke: #7d868d; stroke-width: .11 }
.hiddenf { fill: none; stroke: #7d868d; stroke-width: .11; stroke-dasharray: .9 .6 }
.wood { fill: #f5ece0; stroke: none }
.deck { fill: #eedfcb; stroke: none }
.stone { fill: #e8e6e1; stroke: none }
.tile { fill: #e7eef1; stroke: none }
.rug { fill: none; stroke: #b9a58c; stroke-width: .14; stroke-dasharray: .5 .5 }
.plinth { fill: #ece9e3; stroke: #1a1f24; stroke-width: .18 }
.plinthfaint { fill: #f4f2ee; stroke: #8e969c; stroke-width: .14 }
.void { fill: #f7f7f5; stroke: none }
.stair { fill: #fff; stroke: #4a535a; stroke-width: .16 }
.stair.hiddenst { stroke-dasharray: .9 .6; stroke: #8b949a }
.brk { fill: none; stroke: #1a1f24; stroke-width: .2 }
.walk { fill: none; stroke: #1a1f24; stroke-width: .16 }
.walkdot { fill: #1a1f24 }
.arrowh { fill: #1a1f24 }
.parapet { fill: #b9bfc4; stroke: #1a1f24; stroke-width: .16 }
.railp { fill: #1a1f24 }
.post { fill: #6d4d30; stroke: #1a1f24; stroke-width: .1 }
.over { fill: none; stroke: #1a1f24; stroke-width: .16; stroke-dasharray: 2 .8 .4 .8 }
.room { fill: #1a1f24; letter-spacing: .08px }
.area { fill: #6a737a }
.small { fill: #4b545b }
.note { fill: #59636a; font-style: italic }
.notebg { fill: #1a1f24; paint-order: stroke; stroke: #fff; stroke-width: .9 }
.dim, .ext { stroke: #1a1f24; stroke-width: .12 }
.ext { stroke: #8e969c }
.tick { stroke: #1a1f24; stroke-width: .35 }
.dimt { fill: #1a1f24 }
.axis { stroke: #9aa2a8; stroke-width: .12; stroke-dasharray: 3 .8 .5 .8 }
.bubble { fill: #fff; stroke: #1a1f24; stroke-width: .2 }
.bt { fill: #1a1f24; font-weight: 600 }
.plvl circle, .plvl path { fill: none; stroke: #1a1f24; stroke-width: .14 }
.plvl path.fill { fill: #1a1f24; stroke: none }
.lvl { fill: #fff; stroke: #1a1f24; stroke-width: .2 }
.lvlt { fill: #1a1f24; font-weight: 600 }
.cutline { stroke: #c7782a; stroke-width: .35; stroke-dasharray: 5 1 1 1 }
.secb { fill: #fff; stroke: #c7782a; stroke-width: .35 }
.secbt { fill: #c7782a; font-weight: 700 }
.secarrow { fill: #c7782a }
.dtitle { fill: #1a1f24; font-weight: 600; letter-spacing: .4px }
.dsub { fill: #6a737a; letter-spacing: .3px }
.tline { stroke: #1a1f24; stroke-width: .35 }
.el { stroke: #1a1f24; stroke-width: .16 }
.el.band, .el.fascia { stroke-width: .12 }
.el.wall, .el.clad { stroke: none }
.eloutline { fill: none; stroke: #1a1f24; stroke-width: .2 }
.el.rglass { stroke: none }
.rglassf { stroke: #3b7fa6; stroke-width: .1 }
.elthin { stroke: #4b545b; stroke-width: .1 }
.glare { stroke: #ffffff; stroke-width: .25; opacity: .9 }
.cladl { stroke: #b49d82; stroke-width: .08 }
.elroof { fill: #7d858c; stroke: #1a1f24; stroke-width: .2 }
.tileh { stroke: #5b6369; stroke-width: .1 }
.cut { fill: #2b3137; stroke: #1a1f24; stroke-width: .2 }
.cutglass { fill: #9cc3d8; stroke: #1a1f24; stroke-width: .2 }
.cutdoor { fill: #c9b293; stroke: #1a1f24; stroke-width: .2 }
.cutthin { fill: #6d4d30; stroke: #1a1f24; stroke-width: .15 }
.roofcut { stroke: #1a1f24; stroke-width: .9; stroke-linecap: round }
.groundl { stroke: #1a1f24; stroke-width: .6 }
.groundh { stroke: #1a1f24; stroke-width: .12 }
.flat { fill: #dfe1e2; stroke: #1a1f24; stroke-width: .3 }
.skylight { fill: #cfe3ee; stroke: #1a1f24; stroke-width: .2 }
.roof { fill: #c5c9cc; stroke: none }
.roofedge { fill: none; stroke: #1a1f24; stroke-width: .3 }
.tilel { stroke: #9aa1a6; stroke-width: .1 }
.ridge { stroke: #1a1f24; stroke-width: .45 }
.slope { stroke: #1a1f24; stroke-width: .18 }
.woodb { fill: #c7a07a; stroke: #6d4d30; stroke-width: .08 }
.pave { fill: #ece8e1; stroke: #8e969c; stroke-width: .1 }
.curb { fill: #dcdad6; stroke: #8e969c; stroke-width: .1 }
.lotline { fill: #f1f5ec; stroke: #1a1f24; stroke-width: .25; stroke-dasharray: 3 1 }
.bldg { fill: #fff; stroke: #1a1f24; stroke-width: .35 }
.bldgfaint { fill: #dfe1e2; stroke: #1a1f24; stroke-width: .15 }
.bldgroof { fill: #c5c9cc; stroke: #1a1f24; stroke-width: .25 }
.terr { fill: #eedfcb; stroke: #1a1f24; stroke-width: .12 }
.treec { fill: #dfe9d3; stroke: #7f9b6c; stroke-width: .18 }
.gate { fill: #fff; stroke: #1a1f24; stroke-width: .2 }
.north circle { fill: #fff; stroke: #1a1f24; stroke-width: .2 }
.north path { fill: #1a1f24 }
.north text { fill: #1a1f24; font-weight: 700 }
.tb-k { fill: #6a737a; letter-spacing: .3px }
.tb-v { fill: #1a1f24 }
.tb-big { fill: #1a1f24; font-weight: 700; letter-spacing: .3px }
.tb-line { stroke: #1a1f24; stroke-width: .18 }
.tb-acc { fill: #c7782a }
.legend-t { fill: #1a1f24 }
"""

def logo_data(dark=True):
    p = os.path.join(ROOT, 'site/assets/brand/logo-light.png')
    return 'data:image/png;base64,' + base64.b64encode(open(p, 'rb').read()).decode()

LOGO = None

SHEETS = [('KT-00', 'BÌA · DANH MỤC BẢN VẼ', '—'), ('KT-01', 'MẶT BẰNG TẦNG 1', '1:75'), ('KT-02', 'MẶT BẰNG TẦNG 2', '1:75'),
          ('KT-03', 'MẶT BẰNG MÁI · TỔNG THỂ', '1:75 · 1:250'), ('KT-04', 'MẶT ĐỨNG CHÍNH · MẶT ĐỨNG SAU', '1:100'),
          ('KT-05', 'MẶT ĐỨNG BÊN TRÁI · BÊN PHẢI', '1:75'), ('KT-06', 'MẶT CẮT A-A · B-B', '1:100')]

NOTES = [
    'Kích thước ghi theo trục tường, đơn vị mm; cao độ đơn vị m.',
    'Cao độ ±0.000 lấy tại mặt sàn hoàn thiện tầng 1; sân −0.450.',
    'Tường bao 200, tường ngăn 100–200.',
    'Cầu thang chữ L: 4 bậc + 4 bậc xoay + 8 bậc, 17 cổ bậc ≈ 194, mặt bậc 250.',
    'Bản vẽ phương án, dựng lại từ phác thảo tay và mô hình 3D; vị trí cửa, nội thất và kết cấu cần chủ nhà xác nhận trước khi triển khai kỹ thuật.',
]

def wrap(s, n):
    words, lines, cur = s.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 > n: lines.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    if cur: lines.append(cur)
    return lines

def title_block(P, sheet_no, sheet_name, scale, notes=True, legend=None):
    x0, x1, y0, y1 = 334, 410, 10, 287
    P.add(f'<rect class="frame" x="20" y="10" width="390" height="277"/>')
    P.add(f'<line class="tb-line" x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" style="stroke-width:.4"/>')
    cx = x0 + 4
    # logo (ink tint) + studio
    P.add(f'<image href="{LOGO}" x="{cx}" y="16" width="25" height="19.3" style="filter:brightness(0) saturate(100%)" preserveAspectRatio="xMinYMin meet"/>')
    P.add(f'<text class="tb-big" x="{cx + 28}" y="22.6" font-size="3.6">Bảo ALONE</text>')
    P.add(f'<text class="tb-k" x="{cx + 28}" y="26.6" font-size="1.9">CREATIVE STUDIO · GAME STUDIO</text>')
    P.add(f'<text class="tb-k" x="{cx + 28}" y="31.4" font-size="1.9">THIẾT KẾ · LIÊN HỆ</text>')
    P.add(f'<text class="tb-acc" x="{cx + 28}" y="35.2" font-size="3.0" font-weight="700">0932 705 063</text>')
    P.add(f'<line class="tb-line" x1="{x0}" y1="41" x2="{x1}" y2="41"/>')
    y = 48
    if notes:
        P.add(f'<text class="tb-big" x="{cx}" y="{y}" font-size="2.6">GHI CHÚ</text>'); y += 5
        for i, n in enumerate(NOTES, 1):
            for j, ln in enumerate(wrap(n, 52)):
                P.add(f'<text class="tb-v" x="{cx + (0 if j == 0 else 3)}" y="{y}" font-size="1.85">{(str(i) + ". ") if j == 0 else ""}{esc(ln)}</text>'); y += 3.1
            y += 0.8
    if legend:
        y += 3
        P.add(f'<text class="tb-big" x="{cx}" y="{y}" font-size="2.6">{esc(legend[0])}</text>'); y += 5
        for sw, label in legend[1]:
            P.add(sw(cx, y - 2.4))
            P.add(f'<text class="legend-t" x="{cx + 12}" y="{y}" font-size="1.85">{esc(label)}</text>'); y += 4.4
    # bottom block
    yb = 214
    P.add(f'<line class="tb-line" x1="{x0}" y1="{yb}" x2="{x1}" y2="{yb}"/>')
    rows = [('CÔNG TRÌNH', PROJECT), ('MÃ PHƯƠNG ÁN', CODE + ' · nhà ở 2 tầng · 184 m² sàn'), ('GIAI ĐOẠN', 'THIẾT KẾ PHƯƠNG ÁN'),
            ('NGÀY', DATE), ('TỈ LỆ', scale + ' (khổ A3)')]
    y = yb + 6
    for k, v in rows:
        P.add(f'<text class="tb-k" x="{cx}" y="{y}" font-size="1.7">{k}</text>')
        P.add(f'<text class="tb-v" x="{cx}" y="{y + 3.4}" font-size="2.3" font-weight="600">{esc(v)}</text>'); y += 8.4
    P.add(f'<line class="tb-line" x1="{x0}" y1="{y - 2}" x2="{x1}" y2="{y - 2}"/>')
    P.add(f'<text class="tb-k" x="{cx}" y="{y + 3.5}" font-size="1.7">TÊN BẢN VẼ</text>')
    nm = wrap(sheet_name, 26)
    yy = y + 8
    for ln in nm:
        P.add(f'<text class="tb-big" x="{cx}" y="{yy}" font-size="3.1">{esc(ln)}</text>'); yy += 4.2
    P.add(f'<text class="tb-big" x="{x1 - 4}" y="{y1 - 5}" font-size="7" text-anchor="end">{sheet_no}</text>')
    P.add(f'<text class="tb-k" x="{cx}" y="{y1 - 5}" font-size="1.7">SỐ BẢN VẼ</text>')

def sheet(svg_inner):
    return f'<section class="sheet"><svg viewBox="0 0 420 297" xmlns="http://www.w3.org/2000/svg">{svg_inner}</svg></section>'

def swatch(cls, kind='rect'):
    def fn(x, y):
        if kind == 'rect': return f'<rect class="{cls}" x="{x}" y="{y}" width="9" height="3"/>'
        if kind == 'line': return f'<line class="{cls}" x1="{x}" y1="{y + 1.5}" x2="{x + 9}" y2="{y + 1.5}"/>'
    return fn

def cover_sheet(cover_img):
    P = Page()
    P.add(f'<rect class="frame" x="20" y="10" width="390" height="277"/>')
    if cover_img:
        P.add(f'<clipPath id="cv"><rect x="20" y="10" width="390" height="190"/></clipPath>')
        P.add(f'<image href="{cover_img}" x="20" y="10" width="390" height="190" preserveAspectRatio="xMidYMid slice" clip-path="url(#cv)"/>')
        P.add('<defs><linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#111a21" stop-opacity="0"/><stop offset="1" stop-color="#111a21" stop-opacity=".78"/></linearGradient></defs>')
        P.add('<rect x="20" y="150" width="390" height="50" fill="url(#fade)"/>')
    P.add(f'<image href="{LOGO}" x="30" y="166" width="34" height="26.3" preserveAspectRatio="xMinYMin meet"/>')
    P.add('<text x="70" y="178" font-size="9" fill="#ece6da" font-weight="700" letter-spacing=".6">NHÀ Ở 2 TẦNG 17 × 7 M</text>')
    P.add('<text x="70" y="186.5" font-size="3.6" fill="#ece6da" letter-spacing=".8">HỒ SƠ THIẾT KẾ PHƯƠNG ÁN KIẾN TRÚC · KT-01</text>')
    P.add('<text x="400" y="186.5" font-size="3.4" fill="#f3b35c" font-weight="700" text-anchor="end">0932 705 063</text>')
    P.add('<text x="400" y="180.5" font-size="2.3" fill="#ece6da" text-anchor="end" letter-spacing=".5">Bảo ALONE · CREATIVE STUDIO · GAME STUDIO</text>')
    # thông số
    stats = [('KÍCH THƯỚC NHÀ', '17 × 7 m'), ('SỐ TẦNG', '2 tầng + mái thái'), ('DIỆN TÍCH SÀN', '184 m²'),
             ('PHÒNG NGỦ', '4 phòng'), ('CHIỀU CAO TẦNG', '3.300 mm'), ('ĐỈNH NÓC', '+8.800')]
    x = 30
    for k, v in stats:
        P.add(f'<text class="tb-k" x="{x}" y="212" font-size="2.0">{k}</text>')
        P.add(f'<text class="tb-big" x="{x}" y="218.5" font-size="4.2">{esc(v)}</text>')
        x += 63
    P.add('<line class="tb-line" x1="30" y1="226" x2="400" y2="226"/>')
    P.add('<text class="tb-big" x="30" y="234" font-size="3">DANH MỤC BẢN VẼ</text>')
    y = 242
    for i, (no, name, sc) in enumerate(SHEETS):
        col = 0 if i < 4 else 1
        yy = y + (i if i < 4 else i - 4) * 9
        xx = 30 + col * 190
        P.add(f'<text class="tb-acc" x="{xx}" y="{yy}" font-size="2.8" font-weight="700">{no}</text>')
        P.add(f'<text class="tb-v" x="{xx + 17}" y="{yy}" font-size="2.8">{esc(name)}</text>')
        P.add(f'<text class="tb-k" x="{xx + 160}" y="{yy}" font-size="2.3" text-anchor="end">{sc}</text>')
    P.add(f'<text class="tb-k" x="30" y="282" font-size="1.9">Mô hình 3D tương tác: auudii-house.netlify.app  ·  Ngày phát hành {DATE}  ·  Bản vẽ phương án, kích thước cần xác nhận lại trước khi thi công.</text>')
    return sheet(P.svg())

def main():
    global LOGO
    out = sys.argv[1]
    cover = None
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        ext = 'jpeg' if sys.argv[2].endswith('.jpg') else 'png'
        cover = f'data:image/{ext};base64,' + base64.b64encode(open(sys.argv[2], 'rb').read()).decode()
    LOGO = logo_data()
    solids = build_solids()
    sheets = [cover_sheet(cover)]

    legend_plan = ('KÝ HIỆU', [
        (swatch('poche'), 'Tường xây (cắt)'), (swatch('poche clad'), 'Tường ốp gỗ (cắt)'), (swatch('glass', 'line'), 'Kính cửa sổ / lan can'),
        (swatch('hidden', 'line'), 'Cửa sổ cao (trên mặt cắt)'), (swatch('over', 'line'), 'Mép mái / kết cấu phía trên'),
        (swatch('wood'), 'Sàn gỗ'), (swatch('deck'), 'Sàn gỗ ngoài trời'), (swatch('stone'), 'Sàn đá / gạch'), (swatch('cutline', 'line'), 'Vị trí mặt cắt'),
    ])
    K = 75
    for no, name, fn, extra in (('KT-01', 'MẶT BẰNG TẦNG 1', plan1, ''), ('KT-02', 'MẶT BẰNG TẦNG 2', plan2, '')):
        P = Page()
        V = View(P, 63, 100, K)
        fn(V)
        title_under(V, 8.5, 12.0, name, 'TỈ LỆ 1:75', P)
        title_block(P, no, name, '1:75', legend=legend_plan)
        sheets.append(sheet(P.svg()))

    # roof + site
    P = Page()
    V = View(P, 63, 48, K)
    roofplan(V)
    title_under(V, 8.5, 10.2, 'MẶT BẰNG MÁI', 'TỈ LỆ 1:75', P)
    V2 = View(P, 62, 222, 250)
    siteplan(V2)
    P.add('<text class="dtitle" x="160" y="238" font-size="5.2">MẶT BẰNG TỔNG THỂ</text>')
    P.add('<line class="tline" x1="160" y1="240.2" x2="228" y2="240.2"/>')
    P.add('<text class="dsub" x="160" y="244.6" font-size="2.6">TỈ LỆ 1:250 · hướng Bắc giả định</text>')
    for i, ln in enumerate(['Khu đất 19.6 × 15 m, nhà lùi 3.7 m so với ranh trước.', 'Cổng đi bộ 2.9 m, cổng xe 3.8 m; tường rào đá + bờ giậu.', 'Sân sau 4 m, hàng rào thép thấp phía sau.']):
        P.add(f'<text class="tb-v" x="160" y="{252 + i * 4.2}" font-size="2.1">{esc(ln)}</text>')
    title_block(P, 'KT-03', 'MẶT BẰNG MÁI · TỔNG THỂ', '1:75 · 1:250')
    sheets.append(sheet(P.svg()))

    # elevations front/back
    P = Page()
    V = View(P, 85, 113, 100, flip=True); elevation(V, 'front', '', solids)
    title_under(V, 8.5, GROUND - 1.85, 'MẶT ĐỨNG CHÍNH (TRỤC 1 → 9)', 'TỈ LỆ 1:100', P)
    V = View(P, 85, 245, 100, flip=True); elevation(V, 'back', '', solids)
    title_under(V, 8.5, GROUND - 1.85, 'MẶT ĐỨNG SAU (TRỤC 9 → 1)', 'TỈ LỆ 1:100', P)
    title_block(P, 'KT-04', 'MẶT ĐỨNG CHÍNH · MẶT ĐỨNG SAU', '1:100', legend=('VẬT LIỆU', [
        (swatch('el parapet'), 'Sơn nước trắng'), (swatch('el clad'), 'Ốp gỗ óc chó (ô thang)'), (swatch('elroof'), 'Ngói xám'),
        (swatch('el win'), 'Kính khung nhôm đen'), (swatch('el band'), 'Viền sàn sơn ghi'), (swatch('el timber'), 'Gỗ pergola'),
        (swatch('el plinth'), 'Đá ốp chân tường')]))
    sheets.append(sheet(P.svg()))

    # side elevations
    P = Page()
    V = View(P, 60, 190, 75, flip=True); elevation(V, 'left', '', solids)
    title_under(V, 3.5, GROUND - 1.85, 'MẶT ĐỨNG BÊN TRÁI (TRỤC A → C)', 'TỈ LỆ 1:75', P)
    V = View(P, 222, 190, 75, flip=True); elevation(V, 'right', '', solids)
    title_under(V, 3.5, GROUND - 1.85, 'MẶT ĐỨNG BÊN PHẢI (TRỤC C → A)', 'TỈ LỆ 1:75', P)
    title_block(P, 'KT-05', 'MẶT ĐỨNG BÊN TRÁI · BÊN PHẢI', '1:75', legend=('VẬT LIỆU', [
        (swatch('el parapet'), 'Sơn nước trắng'), (swatch('el clad'), 'Ốp gỗ óc chó (ô thang)'), (swatch('elroof'), 'Ngói xám'),
        (swatch('el win'), 'Kính khung nhôm đen'), (swatch('el band'), 'Viền sàn sơn ghi'), (swatch('el timber'), 'Gỗ pergola')]))
    sheets.append(sheet(P.svg()))

    # sections
    P = Page()
    V = View(P, 70, 118, 100, flip=True); section(V, 'front', ('y', 1.45, -1), '', solids, 17)
    dim_chain(V, 'x', [0, 3, 4, 7, 11, 13.5, 15, 17], GROUND - 0.5, 1); dim_chain(V, 'x', [0, 17], GROUND - 0.9, 1)
    title_under(V, 8.5, GROUND - 1.85, 'MẶT CẮT B-B', 'TỈ LỆ 1:100', P)
    V = View(P, 120, 255, 100, flip=True); section(V, 'left', ('x', 5.6, 1), '', solids, 7)
    dim_chain(V, 'x', [0, 3, 7], GROUND - 0.5, 1)
    dim_chain(V, 'x', [0, 7], GROUND - 0.9, 1)
    title_under(V, 3.5, GROUND - 1.85, 'MẶT CẮT A-A', 'TỈ LỆ 1:100', P)
    title_block(P, 'KT-06', 'MẶT CẮT A-A · B-B', '1:100', legend=('KÝ HIỆU', [
        (swatch('cut'), 'Kết cấu / tường bị cắt'), (swatch('cutglass'), 'Kính bị cắt'), (swatch('roofcut', 'line'), 'Mái ngói bị cắt'),
        (swatch('el parapet'), 'Phần nhìn thấy phía sau')]))
    sheets.append(sheet(P.svg()))

    doc = f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>{CODE} – Bản vẽ phương án</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700&display=swap" rel="stylesheet">
<style>{CSS}{''.join(f'.el.{k}{{fill:{v}}}' for k, v in ELEV_FILL.items())}</style></head><body>{''.join(sheets)}</body></html>"""
    open(out, 'w').write(doc)

if __name__ == '__main__':
    main()
