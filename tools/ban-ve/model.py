# KT-01 — dữ liệu hình học dùng chung cho bản vẽ 2D, chép từ site/house3d.html.
# Toạ độ mặt bằng: px 0..17 trái → phải, py 0..7 sau (trên bản vẽ) → trước (mặt đường).
# Cao độ z tính từ sàn hoàn thiện tầng 1 (±0.000); sân vườn −0.450.

GROUND = -0.45
F1, FH = 0.0, 3.3
F2 = F1 + FH            # +3.300
WALL2 = 3.2
TOP2 = F2 + WALL2       # +6.500 (đáy sàn mái)
ROOFB = TOP2 + 0.15     # +6.650 (mặt sàn mái)
RISE = FH / 17

def win(a, b, sill=0.9, head=2.4): return dict(kind='win', a=a, b=b, sill=sill, head=head)
def door(a, b, hinge, swing, head=2.2, glazed=False): return dict(kind='door', a=a, b=b, hinge=hinge, swing=swing, head=head, glazed=glazed)
def door2(a, b, swing, head=2.2): return dict(kind='door2', a=a, b=b, swing=swing, head=head)
def fold(a, b, head=2.2): return dict(kind='fold', a=a, b=b, head=head)

# (axis, at, from, to, thickness, openings, outside side: −1/+1 exterior, 0 interior, material)
WALLS1 = [
    ('x', 0, -0.1, 17.1, 0.2, [win(0.9, 2.1), win(9.6, 11.2), win(13.0, 15.0, sill=1.15)], -1, 'wall'),
    ('x', 7, -0.1, 17.1, 0.2, [door2(0.8, 2.2, -1, head=2.5), win(4.8, 7.6, sill=0.45, head=2.6), win(10.2, 11.8), win(14.2, 15.8)], 1, 'wall'),
    ('y', 0, 0.1, 6.9, 0.2, [], -1, 'wall'),
    ('y', 17, 0.1, 6.9, 0.2, [win(4.5, 5.5, sill=1.3)], 1, 'wall'),
    ('y', 3, 0.1, 2.9, 0.2, [door(0.6, 1.42, 'b', -1)], 0, 'wall'),
    ('x', 3, 0.1, 4.1, 0.2, [], 0, 'wall'),
    ('y', 3, 3.1, 6.9, 0.2, [fold(3.84, 6.17, head=2.4)], 0, 'wall'),
    ('y', 4, 0.1, 2.9, 0.2, [fold(2.12, 2.9)], 0, 'wall'),
    ('x', 3, 8.94, 16.9, 0.12, [door(12.0, 12.9, 'b', 1), door(13.07, 13.98, 'a', 1)], 0, 'wall'),
    ('y', 9, 3.06, 6.9, 0.12, [], 0, 'wall'),
    ('y', 13, 3.06, 6.9, 0.12, [], 0, 'wall'),
]
WALLS2 = [
    ('x', 0, 3.9, 15.1, 0.2, [win(8.0, 10.0), win(12.0, 12.8, 1.5, 2.3), win(14.0, 14.6, 1.5, 2.3)], -1, 'wall'),
    ('y', 4, 0.1, 3.1, 0.2, [], -1, 'clad'),
    ('x', 3, 4.1, 7.1, 0.2, [door(5.39, 6.27, 'a', 1, glazed=True)], 1, 'clad'),
    ('y', 7, 3.1, 7.1, 0.2, [win(4.6, 5.8, sill=1.3)], -1, 'wall'),
    ('x', 7, 6.9, 15.1, 0.2, [win(8.2, 9.8), win(12.2, 13.8)], 1, 'wall'),
    ('y', 15, 0.1, 6.9, 0.2, [door(2.6, 3.4, 'b', 1, glazed=True), win(4.6, 5.8, sill=1.3)], 1, 'wall'),
    ('y', 11, 0.1, 2.06, 0.12, [], 0, 'wall'),
    ('x', 2.0, 10.94, 14.9, 0.12, [door(12.6, 13.4, 'b', -1), door(13.58, 14.28, 'a', -1)], 0, 'wall'),
    ('y', 13.5, 0.1, 1.94, 0.12, [], 0, 'wall'),
    ('x', 3.5, 7.1, 14.9, 0.12, [door(10.0, 10.85, 'b', 1), door(11.08, 11.98, 'a', 1)], 0, 'wall'),
    ('y', 11, 3.56, 6.9, 0.12, [], 0, 'wall'),
]
# lan can: (axis, at, u1, u2, chiều cao tường thấp)
RAILS2 = [
    ('x', 2.0, 4.1, 7.0, 0), ('y', 7.0, 1.0, 2.0, 0),
    ('x', -0.02, -0.1, 3.9, 0.35), ('y', -0.02, -0.1, 7.1, 0.35), ('x', 7.02, -0.1, 7.0, 0.35),
    ('y', 17.02, -0.1, 7.1, 0.35), ('x', -0.02, 15.1, 17.1, 0.35), ('x', 7.02, 15.0, 17.1, 0.35),
]
SLABS2 = [(-0.1, 4.1, -0.1, 7.1), (7.0, 17.1, -0.1, 7.1), (4.1, 7.0, 2.0, 7.1), (4.1, 7.0, -0.1, 0.1)]
STAIR_VOID = (4.1, 7.0, 0.1, 2.0)

# mái bằng BTCT trên khối phòng ngủ: sênô đua 0.35 m + tường chắn mái 0.7 m; khối ô thang cao bằng tường chắn, giếng trời kính
PH = 0.7                                  # tường chắn mái trên mặt sàn mái
ROOF_TOP = ROOFB + PH + 0.05              # +7.400 đỉnh tường chắn / khối thang
CORNICE_O = 0.35
EAVE = (6.9 - CORNICE_O, 15.1 + CORNICE_O, -0.1 - CORNICE_O, 7.1 + CORNICE_O)   # mép sênô
ROOF_MAIN = (6.9, 15.1, -0.1, 7.1)
PARAPETS = [(7.0, 15.1, -0.1, 0.05), (6.9, 15.1, 6.95, 7.1), (14.95, 15.1, 0.05, 6.95), (6.9, 7.05, 3.2, 6.95)]
CORNICES = [(6.9, 15.45, -0.45, -0.1), (6.9, 15.45, 7.1, 7.45), (15.1, 15.45, -0.1, 7.1), (6.55, 6.9, 3.25, 7.45)]
DRAINS = [(14.65, 0.45), (14.65, 6.55)]
STAIR_BOX = (3.8, 7.0, -0.2, 3.2)
SKYLIGHT = (4.6, 6.4, 0.6, 2.2)

def roof_faces():
    return []

# stair treads as vertical prisms: (footprint polygon, top z)
def stair_treads():
    out = []
    ax1, ax2 = 4.1, 4.98
    for i in range(4):
        y2 = 2.0 - 0.25 * i; y1 = y2 - 0.25
        out.append(([(ax1, y1), (ax2, y1), (ax2, y2), (ax1, y2)], RISE * (i + 1)))
    import math
    P = (ax2, 1.0)
    def hit(a):
        dx, dy = math.cos(a), math.sin(a); t = math.inf
        if dx < -1e-6: t = min(t, (ax1 - P[0]) / dx)
        if dy < -1e-6: t = min(t, (0.1 - P[1]) / dy)
        return (P[0] + dx * t, P[1] + dy * t)
    corner = (ax1, 0.1); cang = math.atan2(corner[1] - P[1], corner[0] - P[0]) + 2 * math.pi
    for i in range(4):
        a0 = math.pi + i * math.pi / 8; a1 = math.pi + (i + 1) * math.pi / 8
        pts = [P, hit(a0)]
        if a0 < cang < a1: pts.append(corner)
        pts.append(hit(a1))
        out.append((pts, RISE * (5 + i)))
    for i in range(8):
        x1 = ax2 + 0.2525 * i
        out.append(([(x1, 0.1), (x1 + 0.2525, 0.1), (x1 + 0.2525, 1.0), (x1, 1.0)], RISE * (9 + i)))
    return out

ROOMS1 = [('PHÒNG THỜ', '9.0 m²', 1.5, 1.75), ('SẢNH TRƯỚC', '12.0 m²', 1.55, 5.55), ('LỐI ĐI', '3.0 m²', 3.5, 1.2),
          ('PHÒNG KHÁCH', '24.0 m²', 6.0, 5.75), ('BẾP + ĂN', '30.0 m²', 11.6, 2.25),
          ('PHÒNG NGỦ 1', '16.0 m²', 11.05, 3.65), ('PHÒNG NGỦ 2', '16.0 m²', 14.95, 3.65)]
ROOMS2 = [('SÂN THƯỢNG', '40.0 m²', 2.4, 2.25), ('SẢNH THANG', '9.0 m²', 5.55, 2.55), ('SINH HOẠT CHUNG', '14.0 m²', 9.0, 1.0),
          ('TẮM', '5.0 m²', 11.75, 1.5), ('WC', '3.0 m²', 14.68, 1.3), ('HÀNH LANG', '', 13.0, 2.78),
          ('PHÒNG NGỦ 3', '14.0 m²', 9.05, 3.98), ('PHÒNG NGỦ 4', '14.0 m²', 12.95, 3.98), ('SÂN SAU', '14.0 m²', 16.0, 4.6)]
