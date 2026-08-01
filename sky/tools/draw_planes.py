#!/usr/bin/env python3
"""Draw the aircraft, as SVG, in a hand-drawn hand.

The fish were scanned from paper and cut out. There is no paper here: each
aircraft is described below as a handful of straight-edged outlines seen from
above, nose to the right, and this script walks those outlines with a shaky
hand -- resampling every edge and pushing each sample sideways by a little
smooth noise -- so the finished line wanders the way a drawn one does instead
of ruling itself straight.

The wobble is seeded off the aircraft's name, so re-running gives byte-for-byte
the same drawings. Change SHAKE for a steadier or a wilder hand.

    python3 sky/tools/draw_planes.py

Writes sky/assets/planes/*.svg and the manifest the page reads.
"""

import json
import math
import os
import random

OUT = os.path.join(os.path.dirname(__file__), '..', 'assets', 'planes')

SHAKE = 1.0        # overall hand-shake; 0 rules everything perfectly straight
STEP = 15.0        # how finely each edge is resampled, in drawing units
PAD = 26           # margin round the drawing, so the stroke isn't clipped


# ---------------------------------------------------------------- the hand

def resample(pts, closed, step):
    """Walk the outline, dropping a point every `step`, keeping the corners."""
    out = []
    n = len(pts)
    last = n if closed else n - 1
    for i in range(last):
        a, b = pts[i], pts[(i + 1) % n]
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        k = max(1, int(d / step))
        for j in range(k):
            t = j / k
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    if not closed:
        out.append(pts[-1])
    return out


def shake(pts, closed, rng, amp):
    """Push each sample along its own normal by a slow, smooth wobble.

    Three harmonics around the outline: one long slow bend, two shorter
    ripples. A closed outline uses whole numbers of cycles so the wobble
    meets itself where the line closes.
    """
    n = len(pts)
    waves = []
    for f in (1, 3, 7):
        waves.append((f * rng.uniform(0.8, 1.3) if not closed else f,
                      rng.uniform(0, math.tau),
                      amp * rng.uniform(0.45, 1.0) / (0.6 + 0.5 * f)))
    out = []
    for i, (x, y) in enumerate(pts):
        p = pts[i - 1]
        q = pts[(i + 1) % n] if closed else pts[min(i + 1, n - 1)]
        tx, ty = q[0] - p[0], q[1] - p[1]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L, tx / L          # normal to the line here
        s = i / n
        d = sum(a * math.sin(math.tau * f * s + ph) for f, ph, a in waves)
        out.append((x + nx * d, y + ny * d))
    return out


def path_d(pts, closed):
    """Catmull-Rom through the samples, written out as cubic beziers."""
    n = len(pts)
    if n < 2:
        return ''
    d = ['M %.1f %.1f' % pts[0]]
    last = n if closed else n - 1
    for i in range(last):
        p0 = pts[i - 1] if (closed or i > 0) else pts[0]
        p1 = pts[i % n]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d.append('C %.1f %.1f %.1f %.1f %.1f %.1f' % (c1 + c2 + p2))
    if closed:
        d.append('Z')
    return ' '.join(d)


def mirror(pts):
    """The same shape on the other side of the fuselage."""
    return [(x, -y) for x, y in pts]


def arc(cx, cy, rx, ry, a0, a1, n=16):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n),
             cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


# ------------------------------------------------------------ the aircraft
#
# Every aircraft is seen from above with its nose pointing right (+x), the
# fuselage lying along y = 0. `solid` shapes are filled with paper white and
# outlined, in the order given, so a wing drawn before the fuselage tucks
# underneath it. `lines` are outline only: windows, folds, propeller discs.
#
# `trail` says whether the aircraft is high and fast enough to leave one.

def wings(shape):
    """A shape and its mirror image, as a pair of solids."""
    return [shape, mirror(shape)]


PLANES = []


def plane(name, stroke, trail, solid, lines=(), shake_amp=1.0):
    PLANES.append(dict(name=name, stroke=stroke, trail=trail,
                       solid=solid, lines=list(lines), shake=shake_amp))


# --- airliner: long, swept, two engines slung under the wings
plane('airliner', 9, True, [
    *wings([(90, -26), (-40, -300), (-96, -306), (-110, -286), (-60, -26)]),
    *wings([(-236, -22), (-306, -130), (-344, -134), (-352, -118), (-300, -22)]),
    [(380, 0), (352, -14), (250, -24), (-180, -30), (-300, -22), (-368, -6),
     (-368, 6), (-300, 22), (-180, 30), (250, 24), (352, 14)],
    *wings([(78, -116), (76, -158), (-46, -166), (-62, -150), (-50, -120)]),
], [
    [(322, -17), (296, 0), (322, 17)],
    [(240, -11), (-170, -13)],
    [(-228, 0), (-352, 0)],
])

# --- prop: high wing, strutted, a propeller disc at the nose
plane('prop', 9, False, [
    *wings([(130, -24), (120, -220), (106, -338), (62, -344), (66, -220), (56, -24)]),
    *wings([(-150, -16), (-206, -120), (-246, -126), (-252, -108), (-224, -16)]),
    [(270, 0), (250, -18), (150, -28), (-120, -24), (-220, -12), (-256, -4),
     (-256, 4), (-220, 12), (-120, 24), (150, 28), (250, 18)],
], [
    arc(252, 0, 30, 124, 0, math.tau, 26),
    [(66, -26), (108, -150)],
    [(66, 26), (108, 150)],
    [(196, -20), (150, -20)],
    [(196, 20), (150, 20)],
])

# --- biplane: two wings, the top one carried a little ahead of the bottom
plane('biplane', 10, False, [
    *wings([(60, -28), (56, -170), (46, -278), (0, -284), (4, -170), (-14, -28)]),
    *wings([(150, -28), (144, -190), (134, -318), (84, -324), (86, -190), (68, -28)]),
    *wings([(-140, -18), (-198, -116), (-238, -120), (-244, -102), (-214, -18)]),
    [(250, 0), (232, -22), (130, -32), (-110, -26), (-210, -14), (-246, -6),
     (-246, 6), (-210, 14), (-110, 26), (130, 32), (232, 22)],
], [
    arc(234, 0, 26, 106, 0, math.tau, 24),
    [(126, -196), (34, -204)],
    [(126, 196), (34, 204)],
    [(96, -14), (96, 14)],
], shake_amp=1.25)

# --- jet: delta wing, canards, twin fins
plane('jet', 9, True, [
    *wings([(70, -34), (-210, -250), (-300, -252), (-310, -44)]),
    *wings([(232, -24), (168, -112), (136, -114), (146, -24)]),
    *wings([(-244, -50), (-318, -66), (-346, -56), (-330, -42), (-266, -40)]),
    [(368, 0), (334, -14), (232, -24), (-120, -40), (-260, -44), (-336, -26),
     (-344, 0), (-336, 26), (-260, 44), (-120, 40), (232, 24), (334, 14)],
    [(318, -13), (262, -20), (222, -12), (222, 12), (262, 20), (318, 13)],
], [
    [(-120, -30), (-300, -34)],
    [(-120, 30), (-300, 34)],
])

# --- paper dart: creased, not curved, so it gets barely any wobble
plane('dart', 8, False, [
    [(400, 0), (-280, -250), (-170, -60), (-300, -22),
     (-300, 22), (-170, 60), (-280, 250)],
], [
    [(388, 0), (-292, 0)],
    [(390, -5), (-172, -58)],
    [(390, 5), (-172, 58)],
], shake_amp=0.35)

# --- glider: all wing, no engine
plane('glider', 8, False, [
    *wings([(90, -18), (88, -260), (78, -462), (38, -468), (40, -260), (32, -18)]),
    *wings([(-200, -10), (-236, -96), (-266, -100), (-270, -86), (-248, -10)]),
    [(240, 0), (224, -14), (150, -20), (-140, -16), (-250, -8), (-272, -3),
     (-272, 3), (-250, 8), (-140, 16), (150, 20), (224, 14)],
], [
    [(206, -14), (168, 0), (206, 14)],
])

# --- seaplane: a prop plane on floats
plane('seaplane', 9, False, [
    *wings([(140, -24), (130, -200), (116, -328), (70, -334), (72, -200), (62, -24)]),
    *wings([(-150, -16), (-208, -122), (-248, -128), (-254, -110), (-224, -16)]),
    [(276, 0), (256, -19), (152, -30), (-120, -26), (-222, -13), (-260, -4),
     (-260, 4), (-222, 13), (-120, 26), (152, 30), (256, 19)],
    *wings([(206, -168), (178, -192), (60, -200), (-112, -194), (-154, -176),
            (-146, -154), (-100, -146), (60, -142), (180, -148)]),
], [
    arc(258, 0, 28, 118, 0, math.tau, 26),
    [(120, -30), (150, -146)],
    [(120, 30), (150, 146)],
    [(-40, -28), (-30, -150)],
    [(-40, 28), (-30, 150)],
])

# --- flying wing: one swept boomerang, a bulge where the pilot sits
plane('flyingwing', 9, True, [
    [(300, 0), (-150, -330), (-232, -318), (-160, -180), (-70, -18),
     (-70, 18), (-160, 180), (-232, 318), (-150, 330)],
    [(240, 0), (170, -46), (60, -50), (58, 50), (170, 46)],
], [
    [(-40, -128), (-96, -136)],
    [(-40, 128), (-96, 136)],
])


# ------------------------------------------------------------------ output

def render(p):
    rng = random.Random(p['name'])
    amp = SHAKE * p['shake'] * 3.2

    shapes = []
    for pts in p['solid']:
        s = shake(resample(pts, True, STEP), True, rng, amp)
        shapes.append(('solid', s))
    for pts in p['lines']:
        s = shake(resample(list(pts), False, STEP), False, rng, amp * 0.8)
        shapes.append(('line', s))

    xs = [x for _, s in shapes for x, _ in s]
    ys = [y for _, s in shapes for _, y in s]
    m = PAD + p['stroke']
    x0, y0 = min(xs) - m, min(ys) - m
    w = round(max(xs) + m - x0)
    h = round(max(ys) + m - y0)

    body = []
    for kind, s in shapes:
        moved = [(x - x0, y - y0) for x, y in s]
        d = path_d(moved, kind == 'solid')
        fill = '#fff' if kind == 'solid' else 'none'
        body.append('  <path fill="%s" d="%s"/>' % (fill, d))

    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
           'viewBox="0 0 %d %d">\n'
           '<g stroke="#111" stroke-width="%g" stroke-linejoin="round" '
           'stroke-linecap="round">\n%s\n</g>\n</svg>\n'
           % (w, h, w, h, p['stroke'], '\n'.join(body)))
    return svg, w, h


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = []
    for p in PLANES:
        svg, w, h = render(p)
        name = p['name'] + '.svg'
        with open(os.path.join(OUT, name), 'w') as f:
            f.write(svg)
        manifest.append(dict(file=name, w=w, h=h, trail=p['trail']))
        print('%-12s %4d x %4d' % (name, w, h))
    with open(os.path.join(OUT, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=1)


if __name__ == '__main__':
    main()
