"""Vector drawing kit for UNWEPT (dark manhwa style). All shapes are hand-authored SVG paths."""
import math, random, itertools, html

_c = itertools.count()
def uid(p="u"):
    return f"{p}{next(_c)}"

# ------------------------------------------------------------------ basics
def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def rgbhex(r, g, b):
    return "#%02x%02x%02x" % tuple(max(0, min(255, int(v))) for v in (r, g, b))
def mix(a, b, t):
    A, B = hexrgb(a), hexrgb(b)
    return rgbhex(*(A[i] + (B[i] - A[i]) * t for i in range(3)))
def dark(c, t=0.35):
    return mix(c, "#000000", t)
def light(c, t=0.35):
    return mix(c, "#ffffff", t)

def G(content, tx=0, ty=0, s=1, rot=0, sx=None, op=None, flt=None, extra=""):
    t = f"translate({tx:.1f},{ty:.1f})"
    if rot:
        t += f" rotate({rot})"
    if sx is not None:
        t += f" scale({sx},{s})"
    elif s != 1:
        t += f" scale({s})"
    a = f' opacity="{op}"' if op is not None else ""
    f = f' filter="url(#{flt})"' if flt else ""
    return f'<g transform="{t}"{a}{f} {extra}>{content}</g>'

def P(d, fill="none", stroke=None, sw=None, op=None, flt=None, cap="round", extra=""):
    s = f'<path d="{d}" fill="{fill}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw or 1}" stroke-linecap="{cap}" stroke-linejoin="round"'
    if op is not None:
        s += f' opacity="{op}"'
    if flt:
        s += f' filter="url(#{flt})"'
    return s + f" {extra}/>"

def C(cx, cy, r, fill, op=None, flt=None, stroke=None, sw=None):
    s = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw}"'
    if op is not None:
        s += f' opacity="{op}"'
    if flt:
        s += f' filter="url(#{flt})"'
    return s + "/>"

def E(cx, cy, rx, ry, fill, op=None, flt=None, stroke=None, sw=None, rot=0):
    s = f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw}"'
    if op is not None:
        s += f' opacity="{op}"'
    if flt:
        s += f' filter="url(#{flt})"'
    if rot:
        s += f' transform="rotate({rot} {cx} {cy})"'
    return s + "/>"

def R(x, y, w, h, fill, rx=0, op=None, flt=None, stroke=None, sw=None, extra=""):
    s = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw}"'
    if op is not None:
        s += f' opacity="{op}"'
    if flt:
        s += f' filter="url(#{flt})"'
    return s + f" {extra}/>"

def T(x, y, txt, size=20, fill="#fff", font="VT323", anchor="start", weight="normal", op=None, flt=None,
      stroke=None, sw=None, rot=0, ls=0, italic=False):
    s = (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{font}, monospace" font-size="{size}" fill="{fill}" '
         f'text-anchor="{anchor}" font-weight="{weight}" letter-spacing="{ls}"')
    if italic:
        s += ' font-style="italic"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw}" paint-order="stroke" stroke-linejoin="round"'
    if op is not None:
        s += f' opacity="{op}"'
    if flt:
        s += f' filter="url(#{flt})"'
    if rot:
        s += f' transform="rotate({rot} {x} {y})"'
    return s + f">{html.escape(txt)}</text>"

def poly(pts):
    return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"

def lin(id_, stops, x1=0, y1=0, x2=0, y2=1):
    st = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    return f'<linearGradient id="{id_}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{st}</linearGradient>'

def rad(id_, stops, cx=0.5, cy=0.5, r=0.5, fx=None, fy=None):
    st = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    f = f' fx="{fx}" fy="{fy}"' if fx is not None else ""
    return f'<radialGradient id="{id_}" cx="{cx}" cy="{cy}" r="{r}"{f}>{st}</radialGradient>'

def clip(id_, d):
    return f'<clipPath id="{id_}"><path d="{d}"/></clipPath>'

SHARED_DEFS = """
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="glow2" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="8" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="glow3" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="18" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<filter id="blur2" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="2"/></filter>
<filter id="blur6" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
<filter id="blur14" x="-80%" y="-80%" width="260%" height="260%"><feGaussianBlur stdDeviation="14"/></filter>
<filter id="blur30" x="-100%" y="-100%" width="300%" height="300%"><feGaussianBlur stdDeviation="30"/></filter>
<filter id="grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" stitchTiles="stitch"/><feColorMatrix values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 0.09 0"/></filter>
<filter id="smoke" x="-30%" y="-30%" width="160%" height="160%"><feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="3" seed="4" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="18"/></filter>
<filter id="smoke2" x="-30%" y="-30%" width="160%" height="160%"><feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="2" seed="9" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="40"/><feGaussianBlur stdDeviation="1.5"/></filter>
</defs></svg>"""

def grain(w, h, op=1):
    return R(0, 0, w, h, "#fff", flt="grain", op=op)

# ------------------------------------------------------------------ effects
def speed_lines(cx, cy, w, h, n=90, r0=180, color="#fff", op=0.5, seed=1, width=(1, 3)):
    rnd = random.Random(seed)
    out = []
    R_ = max(w, h) * 1.2
    for i in range(n):
        a = rnd.uniform(0, math.tau)
        r1 = r0 + rnd.uniform(0, 80)
        wd = rnd.uniform(*width)
        x1, y1 = cx + math.cos(a) * r1, cy + math.sin(a) * r1
        x2, y2 = cx + math.cos(a - 0.004 * wd) * R_, cy + math.sin(a - 0.004 * wd) * R_
        x3, y3 = cx + math.cos(a + 0.004 * wd) * R_, cy + math.sin(a + 0.004 * wd) * R_
        out.append(f'<path d="M {x1:.0f},{y1:.0f} L {x2:.0f},{y2:.0f} L {x3:.0f},{y3:.0f} Z" fill="{color}"/>')
    return f'<g opacity="{op}">{"".join(out)}</g>'

def vlines(w, h, n=40, color="#fff", op=0.3, seed=2, ang=0):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        x = rnd.uniform(0, w)
        l = rnd.uniform(h * 0.2, h * 0.9)
        y = rnd.uniform(-0.1 * h, h - l * 0.5)
        sw = rnd.uniform(0.6, 2.4)
        out.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x + ang * l:.0f}" y2="{y + l:.0f}" stroke="{color}" stroke-width="{sw:.1f}"/>')
    return f'<g opacity="{op}">{"".join(out)}</g>'

def rain(w, h, n=160, color="#cfe0ff", op=0.35, seed=3, ang=-0.18):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        x = rnd.uniform(-60, w + 60)
        y = rnd.uniform(-40, h)
        l = rnd.uniform(18, 60)
        out.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x + ang * l:.0f}" y2="{y + l:.0f}" stroke="{color}" stroke-width="{rnd.uniform(.6, 1.6):.1f}"/>')
    return f'<g opacity="{op}">{"".join(out)}</g>'

def particles(x0, y0, w, h, n=40, color="#c9a5ff", rmax=2.6, seed=5, op=0.9, flt="glow"):
    rnd = random.Random(seed)
    out = "".join(C(rnd.uniform(x0, x0 + w), rnd.uniform(y0, y0 + h), rnd.uniform(0.6, rmax), color,
                    op=round(rnd.uniform(0.3, 1), 2)) for _ in range(n))
    return f'<g opacity="{op}" filter="url(#{flt})">{out}</g>'

def mist(x0, y0, w, h, n=8, color="#6b45c9", op=0.35, seed=6, rmin=60, rmax=180):
    rnd = random.Random(seed)
    out = "".join(E(rnd.uniform(x0, x0 + w), rnd.uniform(y0, y0 + h), rnd.uniform(rmin, rmax),
                    rnd.uniform(rmin * 0.35, rmax * 0.45), color, op=round(rnd.uniform(0.3, 0.9), 2)) for _ in range(n))
    return f'<g opacity="{op}" filter="url(#blur30)">{out}</g>'

def cracks(x, y, n=6, length=90, color="#b98cff", seed=7, sw=2.2, spread=math.tau, base=0):
    rnd = random.Random(seed)
    segs = []
    def branch(px, py, ang, l, depth, w):
        if depth == 0 or l < 6:
            return
        pts = [(px, py)]
        cx_, cy_ = px, py
        steps = rnd.randint(3, 5)
        for _ in range(steps):
            ang += rnd.uniform(-0.5, 0.5)
            cx_ += math.cos(ang) * l / steps
            cy_ += math.sin(ang) * l / steps
            pts.append((cx_, cy_))
        segs.append((pts, w))
        if rnd.random() < 0.8:
            branch(cx_, cy_, ang + rnd.uniform(-1, 1), l * 0.6, depth - 1, w * 0.7)
        if rnd.random() < 0.5:
            branch(pts[len(pts) // 2][0], pts[len(pts) // 2][1], ang + rnd.choice([-1, 1]) * rnd.uniform(.6, 1.2), l * 0.45, depth - 1, w * 0.6)
    for i in range(n):
        branch(x, y, base + spread * i / n + rnd.uniform(-.2, .2), length * rnd.uniform(.6, 1.2), 3, sw)
    core = "".join(f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in p)}" fill="none" stroke="{color}" stroke-width="{w:.1f}" stroke-linecap="round" stroke-linejoin="round"/>' for p, w in segs)
    white = "".join(f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in p)}" fill="none" stroke="#fff" stroke-width="{w * 0.35:.1f}" stroke-linecap="round"/>' for p, w in segs)
    return f'<g filter="url(#glow)">{core}{white}</g>'

def sfx(x, y, txt, size=80, fill="#ffd84d", rot=-6, stroke="#000", sw=8, glow=None, font="Bangers", ls=2):
    g_ = f' filter="url(#{glow})"' if glow else ""
    return (f'<g{g_}>' + T(x, y, txt, size=size, fill=fill, font=font, anchor="middle", stroke=stroke, sw=sw, rot=rot, ls=ls) + "</g>")

def knot(cx, cy, r=18, color="#b78cff", seed=11, glow=True):
    rnd = random.Random(seed)
    lines = []
    for i in range(14):
        a1, a2 = rnd.uniform(0, math.tau), rnd.uniform(0, math.tau)
        x1, y1 = cx + math.cos(a1) * r, cy + math.sin(a1) * r
        x2, y2 = cx + math.cos(a2) * r, cy + math.sin(a2) * r
        qx, qy = cx + rnd.uniform(-r, r) * .6, cy + rnd.uniform(-r, r) * .6
        lines.append(f'<path d="M {x1:.1f},{y1:.1f} Q {qx:.1f},{qy:.1f} {x2:.1f},{y2:.1f}" fill="none" stroke="{color}" stroke-width="{rnd.uniform(1, 2.4):.1f}"/>')
    halo = C(cx, cy, r * 2.2, color, op=0.35, flt="blur14") if glow else ""
    return (halo + C(cx, cy, r * 0.95, dark(color, .55), op=0.85) + f'<g filter="url(#glow)">{"".join(lines)}</g>'
            + C(cx, cy, r * 0.3, "#fff", op=0.9, flt="glow"))

def note_glyph(x, y, s=1, color="#ffd56b"):
    return G(P("M 0,0 L 0,-34 L 22,-40 L 22,-8", stroke=color, sw=3.4) + E(-5, 0, 7, 5, color, rot=-20) +
             E(17, -6, 7, 5, color, rot=-20), x, y, s, flt="glow")

# ------------------------------------------------------------------ system window
def sys_window(x, y, w, lines, kind="under", size=24, pad=18, lh=1.28, title=None):
    h = pad * 2 + len(lines) * size * lh + (size * 1.4 if title else 0)
    gid = uid("sw")
    if kind == "under":
        bg = lin(gid, [(0, "#0d0820", .94), (1, "#22103c", .94)])
        stroke, txt, glow = "#9a6bff", "#ddd0ff", "#8a5cff"
    elif kind == "gold":
        bg = lin(gid, [(0, "#2b1a04", .95), (1, "#46300a", .95)])
        stroke, txt, glow = "#f2b844", "#ffe7aa", "#ffb02e"
    else:
        bg = lin(gid, [(0, "#06172e", .9), (1, "#0d2a52", .9)])
        stroke, txt, glow = "#6fb8ff", "#d8ecff", "#4aa3ff"
    out = [f"<defs>{bg}</defs>",
           R(x - 6, y - 6, w + 12, h + 12, glow, rx=16, op=0.35, flt="blur14"),
           R(x, y, w, h, f"url(#{gid})", rx=10, stroke=stroke, sw=2),
           R(x + 4, y + 4, w - 8, h - 8, "none", rx=8, stroke=stroke, sw=0.6, op=0.5),
           P(f"M {x + 10},{y} L {x + 60},{y}", stroke="#fff", sw=2, op=0.8)]
    ty = y + pad + size * 0.9
    if title:
        out.append(T(x + w / 2, ty, title, size=size * 1.05, fill="#fff", anchor="middle", flt="glow"))
        out.append(P(f"M {x + 20},{ty + 10} L {x + w - 20},{ty + 10}", stroke=stroke, sw=1, op=0.6))
        ty += size * 1.4
    for ln in lines:
        out.append(T(x + pad, ty, ln, size=size, fill=txt, flt="glow"))
        ty += size * lh
    return "".join(out), h

# ------------------------------------------------------------------ pixel art
def pixels(grid, x0, y0, ps, pal):
    out = []
    for j, row in enumerate(grid):
        for i, ch in enumerate(row):
            if ch in pal and pal[ch]:
                out.append(f'<rect x="{x0 + i * ps}" y="{y0 + j * ps}" width="{ps + .3}" height="{ps + .3}" fill="{pal[ch]}"/>')
    return "".join(out)
