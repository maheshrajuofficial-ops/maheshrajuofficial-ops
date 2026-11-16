"""Hair system: layered curved locks with gradient fill, per-lock highlight bands and forehead shadows."""
import math, random
from art import *

LINE = "#120c18"


def leaf_d(rx, ry, tx, ty, w, bend=0.0, taper=0.56):
    dx, dy = tx - rx, ty - ry
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    mx, my = (rx + tx) / 2 + nx * bend, (ry + ty) / 2 + ny * bend
    p1 = (rx + nx * w / 2, ry + ny * w / 2)
    p2 = (rx - nx * w / 2, ry - ny * w / 2)
    c1 = (mx + nx * w * taper, my + ny * w * taper)
    c2 = (mx - nx * w * taper, my - ny * w * taper)
    return (f"M {p1[0]:.1f},{p1[1]:.1f} Q {c1[0]:.1f},{c1[1]:.1f} {tx:.1f},{ty:.1f} "
            f"Q {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} Z")


def leaf(rx, ry, tx, ty, w, bend=0.0, fill="#000", op=None, stroke=None, sw=None):
    return P(leaf_d(rx, ry, tx, ty, w, bend), fill, stroke=stroke, sw=sw, op=op)


def _pt(rx, ry, tx, ty, bend, t):
    """point on the quadratic-ish centreline at t"""
    dx, dy = tx - rx, ty - ry
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    mx, my = (rx + tx) / 2 + nx * bend * 2, (ry + ty) / 2 + ny * bend * 2
    x = (1 - t) ** 2 * rx + 2 * (1 - t) * t * mx + t * t * tx
    y = (1 - t) ** 2 * ry + 2 * (1 - t) * t * my + t * t * ty
    return x, y


def locks(spec, fill, hi, line=LINE, sw=1.3, hl=(0.18, 0.42), hl_op=0.8, under=True, strands=0.35):
    """spec rows: (rx, ry, tx, ty, w, bend)."""
    out = []
    if under:
        out.append("".join(P(leaf_d(rx, ry + 2, tx + 1.5, ty + 3, w + 2, b), "#000", op=.35) for rx, ry, tx, ty, w, b in spec))
    for i, (rx, ry, tx, ty, w, b) in enumerate(spec):
        d = leaf_d(rx, ry, tx, ty, w, b)
        out.append(P(d, fill))
        out.append(P(d[:d.rindex(" Z")], "none", stroke=line, sw=sw))
        if hi:
            a = _pt(rx, ry, tx, ty, b, hl[0])
            m = _pt(rx, ry, tx, ty, b, (hl[0] + hl[1]) / 2)
            z = _pt(rx, ry, tx, ty, b, hl[1])
            o = -w * .16
            out.append(P(f"M {a[0] + o:.1f},{a[1]:.1f} Q {m[0] + o * 1.2:.1f},{m[1]:.1f} {z[0] + o * .6:.1f},{z[1]:.1f}", stroke=hi, sw=max(1.6, w * .16), op=hl_op))
            a2 = _pt(rx, ry, tx, ty, b, hl[1] + .06)
            z2 = _pt(rx, ry, tx, ty, b, hl[1] + .2)
            out.append(P(f"M {a2[0] + o * .8:.1f},{a2[1]:.1f} L {z2[0] + o * .5:.1f},{z2[1]:.1f}", stroke=hi, sw=1.2, op=hl_op * .7))
        if strands and (i % 2 == 0):
            a = _pt(rx, ry, tx, ty, b, .5)
            z = _pt(rx, ry, tx, ty, b, .92)
            out.append(P(f"M {a[0] + w * .15:.1f},{a[1]:.1f} Q {(a[0] + z[0]) / 2 + b * .3:.1f},{(a[1] + z[1]) / 2:.1f} {z[0]:.1f},{z[1]:.1f}", stroke=LINE, sw=0.9, op=strands))
    return "".join(out)


def forehead_shadow(spec, shade, dx=3, dy=7):
    return "".join(P(leaf_d(rx + dx, ry + dy, tx + dx, ty + dy, w + 3, b), shade) for rx, ry, tx, ty, w, b in spec)


def hgrad(c, hi, top=None, y1=-112, y2=70):
    gid = uid("hg")
    st = "".join(f'<stop offset="{o}" stop-color="{col}"/>' for o, col in
                 [(0, top or mix(c, hi, .4)), (0.3, c), (0.75, dark(c, .3)), (1, dark(c, .5))])
    d = f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="{y1}" x2="0" y2="{y2}">{st}</linearGradient>'
    return gid, f"<defs>{d}</defs>"


# style table: back path, cap path, front lock spec, extras
def wren_spec():
    return [(-44, -46, -62, 40, 22, -11), (46, -46, 62, 34, 22, 11),
            (-30, -72, -54, -2, 26, -12), (-18, -80, -32, -8, 24, -7), (-6, -84, -16, -12, 20, 4),
            (4, -84, 0, 16, 14, -4), (14, -82, 22, -8, 22, 7), (24, -78, 34, -2, 22, 8),
            (-38, -62, -48, 14, 12, -5), (-12, -76, -24, 2, 10, -3)]


STYLES = {
    "wren": dict(
        back="M -62,36 C -72,-48 -42,-110 2,-110 C 46,-110 72,-48 62,36 L 48,10 L 48,-20 L -48,-20 L -48,12 Z",
        cap="M -56,-18 C -60,-60 -50,-88 -32,-100 L -40,-108 L -22,-103 C -8,-109 4,-111 12,-109 L 30,-114 L 25,-105 C 34,-103 44,-96 50,-86 L 60,-88 L 55,-76 C 58,-60 58,-40 56,-18 C 42,-56 -34,-58 -56,-18 Z",
        spec=wren_spec()),
    "earth": dict(
        back="M -56,8 C -64,-52 -40,-106 2,-106 C 44,-106 64,-52 56,8 L 46,-8 L -46,-8 Z",
        cap="M -53,-22 C -57,-70 -44,-94 -24,-102 L -26,-108 L -10,-104 C 0,-107 10,-107 18,-105 L 34,-108 L 30,-101 C 48,-92 58,-70 54,-22 C 44,-58 -32,-60 -53,-22 Z",
        spec=[(-44, -52, -54, 10, 16, -6), (46, -52, 54, 8, 16, 6),
              (-30, -76, -46, -18, 22, -7), (-16, -84, -26, -22, 20, -3), (-2, -88, -6, -24, 18, 2),
              (12, -86, 18, -20, 19, 4), (26, -80, 40, -22, 20, 6)]),
    "plastered": dict(
        back="M -56,10 C -62,-50 -38,-100 2,-100 C 42,-100 62,-50 56,10 L 46,-6 L -46,-6 Z",
        cap="M -52,-12 C -54,-80 -22,-98 2,-98 C 34,-98 56,-78 52,-12 C 42,-50 -30,-52 -52,-12 Z",
        spec=[(-44, -56, -50, 18, 13, -3), (46, -56, 50, 16, 13, 3), (-34, -74, -42, -2, 14, -2),
              (-22, -82, -26, 2, 14, -1), (-9, -86, -10, -4, 13, 0), (4, -86, 5, 6, 12, 1),
              (17, -84, 20, -2, 14, 1), (30, -76, 38, 0, 14, 2)]),
    "june": dict(
        back="M -66,58 C -78,-40 -46,-108 0,-108 C 46,-108 78,-40 66,58 L 52,40 L 54,0 L -54,0 L -52,40 Z",
        cap="M -56,-10 C -60,-82 -24,-104 2,-104 C 36,-104 62,-82 56,-10 C 44,-48 -34,-52 -56,-10 Z",
        spec=[(-52, -44, -68, 56, 22, -10), (52, -44, 66, 52, 22, 10), (-56, -16, -64, 40, 16, -5), (56, -16, 64, 36, 16, 6),
              (-34, -76, -52, -12, 22, -7), (-20, -84, -30, -6, 21, -4), (-6, -88, -12, -16, 18, 3),
              (8, -88, 12, -10, 18, 3), (22, -84, 30, -8, 20, 5), (36, -76, 50, -14, 20, 7)]),
    "solenne": dict(
        back="M -58,92 C -68,20 -64,-62 -30,-100 C 0,-114 40,-110 56,-82 C 66,-40 64,20 58,92 L 44,60 L 46,0 L -46,0 L -44,60 Z",
        cap="M -52,-16 C -56,-82 -22,-104 2,-104 C 36,-104 58,-82 54,-16 C 40,-62 -30,-64 -52,-16 Z",
        spec=[(-46, -60, -58, 96, 16, -10), (46, -60, 56, 92, 16, 10), (-40, -70, -52, 44, 13, -7),
              (-34, -84, -48, -6, 20, -7), (-20, -92, -20, -12, 18, -2), (-8, -94, 6, -16, 17, 5),
              (6, -94, 28, -12, 18, 6), (20, -90, 44, -6, 18, 7), (36, -80, 50, 14, 15, 6)]),
    "dorian": dict(
        back="M -56,6 C -64,-58 -36,-108 2,-110 C 46,-110 66,-58 58,6 L 66,22 L 46,-4 L -46,-4 L -64,24 Z",
        cap="M -52,-28 C -54,-88 -20,-108 4,-108 C 40,-108 58,-86 54,-28 C 46,-52 36,-64 20,-62 C 4,-68 -20,-66 -34,-60 C -44,-54 -48,-42 -52,-28 Z",
        spec=[(-10, -64, -22, -16, 10, -5), (-2, -64, -4, -26, 7, 3), (40, -60, 52, -6, 12, 6), (-44, -48, -52, 0, 12, -4)]),
    "miriam": dict(
        back="M -58,46 C -66,-40 -40,-104 0,-104 C 40,-104 66,-40 58,46 L 46,20 L -46,20 Z",
        cap="M -52,-14 C -56,-82 -22,-100 2,-100 C 36,-100 58,-80 54,-14 C 38,-60 -26,-66 -52,-14 Z",
        spec=[(-46, -58, -58, 54, 11, -9), (46, -60, 54, 50, 10, 9), (-34, -82, -42, -10, 18, -6), (-18, -90, -8, -22, 16, 5),
              (0, -92, 22, -24, 16, 6), (18, -88, 40, -16, 16, 6), (-40, -70, -46, 22, 8, -4)]),
    "maren": dict(
        back="M -58,40 C -66,-40 -40,-104 0,-104 C 40,-104 66,-40 58,40 L 46,16 L -46,16 Z",
        cap="M -52,-14 C -56,-82 -22,-100 2,-100 C 36,-100 58,-80 54,-14 C 38,-60 -26,-66 -52,-14 Z",
        spec=[(-46, -58, -56, 38, 14, -7), (46, -60, 54, 36, 13, 8), (-30, -84, -38, -18, 18, -6), (-12, -92, 4, -30, 17, 5),
              (8, -92, 32, -22, 17, 7)]),
    "pigtails": dict(
        back="M -56,10 C -62,-50 -38,-100 2,-100 C 42,-100 62,-50 56,10 L 46,-6 L -46,-6 Z",
        cap="M -52,-6 C -54,-80 -22,-98 2,-98 C 34,-98 56,-78 52,-6 C 42,-36 -30,-38 -52,-6 Z",
        spec=[(-40, -68, -48, -8, 16, -4), (-26, -78, -28, -14, 16, -1), (-10, -82, -10, -16, 16, 0), (6, -82, 8, -16, 16, 0),
              (22, -78, 26, -14, 16, 1), (38, -68, 46, -8, 16, 4)]),
    "lilyteen": dict(
        back="M -60,120 C -70,0 -50,-104 0,-104 C 50,-104 70,0 60,120 L 46,80 L 46,0 L -46,0 L -46,80 Z",
        cap="M -52,-12 C -56,-82 -22,-100 2,-100 C 36,-100 58,-80 54,-12 C 38,-60 -26,-66 -52,-12 Z",
        spec=[(-46, -58, -58, 104, 15, -9), (46, -60, 56, 100, 15, 9), (-34, -82, -46, -8, 18, -6), (-18, -92, -16, -16, 17, 2),
              (0, -94, 12, -14, 17, 4), (18, -90, 36, -10, 17, 6)]),
    "severin": dict(
        back="M -58,190 C -66,60 -64,-52 -40,-98 C -18,-114 18,-114 40,-98 C 64,-52 66,60 58,190 L 40,130 L 44,0 L -44,0 L -40,130 Z",
        cap="M -48,-10 C -50,-84 -22,-104 0,-104 C 22,-104 50,-84 48,-10 C 42,-50 20,-72 2,-76 C -18,-72 -42,-50 -48,-10 Z",
        spec=[(-6, -76, -40, 30, 14, -10), (6, -76, 40, 30, 14, 10), (-30, -66, -50, 96, 12, -7), (30, -66, 50, 96, 12, 7)]),
}


def hair_style(name, c, hi, ex=None):
    """returns (back_svg, front_svg, spec_for_forehead_shadow)"""
    if name == "otto":
        return otto_hair(c, hi)
    if name == "iona":
        return iona_hair(c, hi)
    st = STYLES[name]
    gid, gdef = hgrad(c, hi)
    fill = f"url(#{gid})"
    line = LINE if name not in ("solenne", "severin") else "#4e5874"
    back = gdef + P(st["back"], dark(c, .25), stroke=line, sw=1.6)
    extra_back, extra_front = "", ""
    if name == "solenne":
        g2, d2 = hgrad(c, hi)
        extra_back += d2 + P("M 30,-98 C 80,-106 106,-40 94,40 C 88,110 110,170 98,252 C 82,192 68,122 72,52 C 76,-8 62,-58 30,-82 Z", f"url(#{g2})", stroke=line, sw=1.6)
        extra_back += P("M 70,-60 C 90,0 78,80 94,200", stroke="#9aa6c2", sw=1.4) + P("M 62,-40 C 82,40 72,110 86,160", stroke="#ffffff", sw=1.6, op=.9)
        extra_front += P("M 40,-94 L 66,-116 L 68,-88 Z", "#0d0d10", stroke=LINE, sw=1.2) + P("M 40,-94 L 72,-82 L 58,-70 Z", "#0d0d10", stroke=LINE, sw=1.2)
        extra_front += P("M 50,-90 L 60,-46 L 52,-50 Z M 50,-90 L 74,-50 L 68,-52 Z", "#18181c") + P("M 46,-100 L 60,-108", stroke="#666", sw=1.2)
    if name == "pigtails":
        for s in (-1, 1):
            extra_back += G(P("M 0,0 C 32,-12 54,10 52,48 C 50,72 32,88 20,98 C 22,72 10,52 -4,30 Z", fill, stroke=LINE, sw=1.6)
                            + P("M 12,8 C 32,20 38,50 26,80", stroke=hi, sw=3, op=.8) + P("M 20,30 C 34,44 30,64 20,80", stroke=LINE, sw=.9, op=.4), 46 * s, -50, sx=s, s=1)
            extra_front += G(C(0, 0, 8, "#e23b4a", stroke=LINE, sw=1.4) + C(-2, -3, 2.4, "#ffb0b8"), 50 * s, -46)
    if name == "miriam":
        extra_back += C(30, -108, 27, fill, stroke=LINE, sw=1.6) + P("M 12,-116 Q 30,-130 48,-112", stroke=hi, sw=3, op=.8)
        extra_back += P("M 8,-142 L 62,-84", stroke="#e7b84a", sw=6) + P("M 62,-84 L 69,-76", stroke="#2a2a2a", sw=6) + P("M 6,-144 L 12,-138", stroke="#f09aa0", sw=6.5)
    if name == "june":
        extra_front += P("M -58,-60 Q 0,-84 58,-60 L 58,-50 Q 0,-74 -58,-50 Z", "#3a2a1c", stroke=LINE, sw=1.4)
        for gx in (-22, 22):
            extra_front += C(gx, -74, 16, "#8a6a3a", stroke=LINE, sw=1.6) + C(gx, -74, 11.5, "#1f3c4c", stroke="#d8b070", sw=2.2)
            extra_front += P(f"M {gx - 6},{-80} Q {gx},{-86} {gx + 6},{-82}", stroke="#cfefff", sw=2.6, op=.9) + C(gx + 5, -69, 1.8, "#cfefff")
    if name == "severin":
        extra_front += P("M 0,-102 L 0,-76", stroke="#9aa0b0", sw=1.2)
    if name == "dorian":
        for x in (-34, -18, -2, 14, 30):
            extra_front += P(f"M {x},-60 C {x - 4},-82 {x + 10},-100 {x + 24},-106", stroke=dark(c, .4), sw=1.4)
        extra_front += P("M -30,-64 C -40,-82 -20,-102 6,-104", stroke=hi, sw=3.4, op=.9) + P("M 2,-66 C 0,-88 18,-102 34,-102", stroke=hi, sw=2.6, op=.8)
    cap = P(st["cap"], fill, stroke=line, sw=1.4)
    if name == "wren":
        sid = uid("st")
        streak_def = f"<defs>{lin(sid, [(0, '#ffffff', 1), (1, '#b9c1d4', 1)])}</defs>"
        spec = st["spec"]
        front = cap + locks(spec, fill, hi, line=line)
        front += streak_def + P(leaf_d(30, -80, 44, -2, 18, 7), f"url(#{sid})", stroke=line, sw=1.3)
        front += P(leaf_d(36, -74, 50, 8, 8, 7), "#eef1f8", stroke=line, sw=1.0)
        front += P("M 33,-72 Q 41,-40 42,-10", stroke="#8e98b0", sw=1.1)
        front += P(leaf_d(31, -76, 36, -50, 6, 2), "#ffffff", op=.9)
    else:
        spec = st["spec"]
        front = cap + locks(spec, fill, hi, line=line)
    return back + extra_back, front + extra_front, spec


def otto_hair(c, hi):
    gid, gdef = hgrad(c, hi)
    fill = f"url(#{gid})"
    def curl(x, y, r):
        return (C(x, y, r, fill, stroke=LINE, sw=1.4) + P(f"M {x - r * .55},{y + r * .05} Q {x - r * .1},{y - r * .75} {x + r * .5},{y - r * .1}", stroke=hi, sw=2.2, op=.85)
                + P(f"M {x - r * .2},{y + r * .55} Q {x + r * .45},{y + r * .35} {x + r * .25},{y - r * .15}", stroke=dark(c, .55), sw=1.3))
    back = gdef + "".join(curl(x, y, r) for x, y, r in
                          [(-54, -30, 18), (-58, -6, 15), (54, -30, 18), (58, -6, 15), (-40, -72, 21), (40, -72, 21),
                           (-16, -92, 22), (16, -92, 22), (0, -98, 18), (-52, 14, 12), (52, 14, 12)])
    front = "".join(curl(x, y, r) for x, y, r in
                    [(-44, -48, 15), (-30, -66, 16), (-12, -76, 15), (6, -78, 16), (24, -72, 15), (40, -54, 15),
                     (-22, -52, 12), (0, -56, 12), (20, -52, 12), (-48, -24, 11), (48, -24, 11)])
    spec = [(-30, -60, -30, -40, 30, 0), (0, -62, 0, -42, 30, 0), (28, -60, 28, -40, 30, 0)]
    return back, front, spec


def iona_hair(c, hi):
    back = P("M -50,-10 C -54,-76 -26,-98 0,-98 C 26,-98 54,-76 50,-10 L 44,-30 L -44,-30 Z", dark(c, .2), stroke=LINE, sw=1.6)
    gid, gdef = hgrad(c, hi)
    front = gdef + P("M -49,-24 C -52,-80 -24,-98 0,-98 C 26,-98 52,-80 49,-24 C 44,-46 30,-56 0,-58 C -30,-56 -44,-46 -49,-24 Z", f"url(#{gid})", stroke=LINE, sw=1.4)
    rnd = random.Random(8)
    for _ in range(46):
        x = rnd.uniform(-42, 42)
        y = rnd.uniform(-90, -60) + abs(x) * 0.45
        front += P(f"M {x:.1f},{y:.1f} l {rnd.uniform(-2, 2):.1f},{rnd.uniform(4, 7):.1f}", stroke=dark(c, .4), sw=1.2)
    front += P("M -30,-86 Q 0,-96 26,-88", stroke=hi, sw=3.4, op=.7)
    return back, front, []
