"""Creatures: the Hush, Wracks (Murmur, Wail, Dirge, Lament), Crumb."""
import math, random
from art import *
from figures import tube

LINE = "#06040a"
VIO = "#a673ff"
OBS = "#0c0a12"


def tendrils(x0, y0, x1, y1, n, length, col, seed=1, w=(10, 22), sway=40, op=1):
    rnd = random.Random(seed)
    out = []
    for i in range(n):
        t = i / max(1, n - 1)
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        L = length * rnd.uniform(.6, 1.2)
        ww = rnd.uniform(*w)
        sx = rnd.uniform(-sway, sway)
        d = (f"M {x - ww / 2:.1f},{y:.1f} C {x - ww / 2 + sx * .3:.1f},{y + L * .4:.1f} {x + sx:.1f},{y + L * .6:.1f} {x + sx * 1.3:.1f},{y + L:.1f} "
             f"C {x + sx + ww * .2:.1f},{y + L * .6:.1f} {x + ww / 2 + sx * .3:.1f},{y + L * .4:.1f} {x + ww / 2:.1f},{y:.1f} Z")
        out.append(P(d, col, op=op))
    return "".join(out)


def hush_mask(x, y, s=1, glow=True, crack=False):
    g = P("M 0,-46 C 26,-46 34,-14 30,14 C 26,40 12,58 0,62 C -12,58 -26,40 -30,14 C -34,-14 -26,-46 0,-46 Z", "#f1eee8", stroke=LINE, sw=2.4)
    g += P("M 6,-44 C 26,-40 32,-10 28,16 C 24,40 12,56 2,60 C 14,40 18,10 6,-44 Z", "#c9c4d0", op=.8)
    g += P("M -18,-34 C -10,-42 4,-44 12,-40", stroke="#ffffff", sw=3, op=.9)
    for sx in (-12, 12):
        if glow:
            g += P(f"M {sx},-12 L {sx},22", stroke=VIO, sw=9, op=.6, flt="blur6")
        g += P(f"M {sx - 3},-14 Q {sx},-18 {sx + 3},-14 L {sx + 2},22 Q {sx},26 {sx - 2},22 Z", "#1a0b30", stroke=LINE, sw=1.2)
        g += P(f"M {sx},-10 L {sx},18", stroke="#e6d4ff", sw=2.2, flt="glow")
    if crack:
        g += P("M 0,-46 L -3,-20 L 3,-4 L -2,18 L 2,40 L 0,62", stroke="#120a1e", sw=2.6) + P("M 0,-46 L -3,-20 L 3,-4 L -2,18 L 2,40 L 0,62", stroke=VIO, sw=1, flt="glow")
    return G(g, x, y, s)


def hush(seam=VIO, with_mist=True):
    """Full-body Hush, frame ~ x[-220,220] y[0,1000]."""
    out = []
    if with_mist:
        out.append(mist(-260, 840, 520, 160, n=6, color="#3a2a6a", op=.6, seed=3, rmin=80, rmax=160))
    # mantle of shadow tendrils behind
    out.append(P("M -120,190 C -190,300 -210,520 -230,760 L 230,760 C 210,520 190,300 120,190 C 60,150 -60,150 -120,190 Z", "#07050c", stroke=LINE, sw=2))
    out.append(tendrils(-228, 740, 228, 740, 16, 200, "#07050c", seed=4, w=(18, 34), sway=36))
    out.append(tendrils(-200, 760, 200, 760, 9, 150, "#120c22", seed=9, w=(10, 18), sway=30, op=.9))
    out.append(P("M -120,190 C -190,300 -210,520 -230,760", stroke=seam, sw=2, op=.6, flt="glow"))
    # hood behind head
    out.append(P("M -70,170 C -96,80 -60,20 0,14 C 60,20 96,80 70,170 Z", "#07050c", stroke=LINE, sw=2))
    # legs
    for s in (-1, 1):
        out.append(tube([(s * 46, 500, 66), (s * 66, 640, 54), (s * 70, 730, 40), (s * 54, 840, 34), (s * 46, 930, 26)], OBS, "#000000", stroke=LINE, sw=2))
        out.append(P(f"M {s * 52},560 Q {s * 68},640 {s * 70},720 M {s * 64},760 Q {s * 56},840 {s * 48},910", stroke=seam, sw=2.2, flt="glow", op=.9))
        for k in range(3):
            out.append(P(f"M {s * 46 + (k - 1) * 12},{922} L {s * 46 + (k - 1) * 18 + s * 6},{972} L {s * 46 + (k - 1) * 12 + 6},{930} Z", "#1a1624", stroke=LINE, sw=1.4))
        out.append(E(s * 70, 726, 18, 12, "#1a1626", stroke=LINE, sw=1.6))
    # torso
    torso = "M -18,150 L -112,192 Q -128,200 -124,232 L -66,420 L -58,520 L 58,520 L 66,420 L 124,232 Q 128,200 112,192 L 18,150 Z"
    out.append(P(torso, OBS, stroke=LINE, sw=2.4))
    out.append(P("M 20,160 L 110,196 Q 124,206 120,232 L 62,420 L 54,520 L 20,520 C 34,400 30,260 20,160 Z", "#000", op=.6))
    # plates and seams
    for y in (250, 300, 350):
        out.append(P(f"M -70,{y} Q -30,{y + 18} 0,{y + 6} Q 30,{y + 18} 70,{y}", stroke=seam, sw=2.4, flt="glow"))
    out.append(P("M 0,180 L 0,500", stroke=seam, sw=2, flt="glow", op=.8))
    out.append(P("M -110,200 Q -60,230 -20,226 M 110,200 Q 60,230 20,226", stroke=seam, sw=2, flt="glow"))
    out.append(P("M -60,420 L 0,450 L 60,420", stroke=seam, sw=2, flt="glow", op=.8))
    out.append(P("M -80,240 Q -60,236 -50,260", stroke="#4a4466", sw=3, op=.8))
    out.append(C(0, 290, 16, seam, op=.5, flt="blur6") + C(0, 290, 6, "#e6d4ff", flt="glow"))
    # shoulder plates
    for s in (-1, 1):
        out.append(P(f"M {s * 80},186 C {s * 120},150 {s * 160},160 {s * 168},200 C {s * 160},230 {s * 130},236 {s * 100},230 Z", "#141020", stroke=LINE, sw=2))
        out.append(P(f"M {s * 150},168 L {s * 176},126 L {s * 160},180 Z", "#141020", stroke=LINE, sw=1.6))
        out.append(P(f"M {s * 92},200 C {s * 120},176 {s * 150},178 {s * 160},200", stroke=seam, sw=1.8, flt="glow", op=.9))
    # arms (long) + claws
    for s in (-1, 1):
        out.append(tube([(s * 128, 214, 40), (s * 146, 330, 36), (s * 154, 440, 30), (s * 150, 560, 32), (s * 140, 650, 24)], OBS, "#000", stroke=LINE, sw=2))
        out.append(P(f"M {s * 134},240 Q {s * 150},340 {s * 152},430 M {s * 154},470 Q {s * 152},560 {s * 142},640", stroke=seam, sw=2, flt="glow"))
        for k in range(4):
            a = math.radians(96 + s * (k - 1.5) * 9)
            x0, y0 = s * 140 + (k - 1.5) * 8, 652
            x1, y1 = x0 + math.cos(a) * 110 * s * .1 + s * (k - 1.5) * 10, y0 + 120 - abs(k - 1.5) * 10
            out.append(P(f"M {x0 - 5:.0f},{y0} Q {x0 - 2:.0f},{(y0 + y1) / 2:.0f} {x1:.0f},{y1:.0f} Q {x0 + 8:.0f},{(y0 + y1) / 2:.0f} {x0 + 5:.0f},{y0} Z", "#1a1624", stroke=LINE, sw=1.4))
            out.append(P(f"M {x0:.0f},{y0 + 6} L {x1:.0f},{y1 - 4:.0f}", stroke="#5a4a8a", sw=1, op=.7))
    # neck + mask
    out.append(P("M -20,100 L -24,170 L 24,170 L 20,100 Z", OBS, stroke=LINE, sw=2))
    out.append(hush_mask(0, 86, 1.0))
    return "".join(out)


def murmur_skull(rim=VIO, jaw_open=6, mouths=True):
    """eyeless elongated head facing -x; neck root near (-60,-110)."""
    out = []
    out.append(P("M -46,-128 C -70,-136 -110,-126 -150,-104 C -170,-94 -184,-86 -186,-78 C -186,-72 -178,-70 -168,-71 L -120,-74 C -96,-78 -72,-90 -50,-100 Z", "#1a1222", stroke=LINE, sw=1.8))
    out.append(P(f"M -170,-70 L -118,{-66 + jaw_open} C -100,{-66 + jaw_open} -84,-74 -72,-84 L -116,-76 Z", "#140e1c", stroke=LINE, sw=1.6))
    teeth = "M -168,-72 " + " ".join(f"L {-164 + i * 6},{-66 + (i % 2) * 4 + jaw_open * .3:.1f}" for i in range(9))
    out.append(P(teeth, "none", stroke="#d8d0e0", sw=1.4))
    out.append(P("M -182,-82 l 6,-2 M -176,-86 l 6,-1", stroke="#4a3a5a", sw=1.6))
    out.append(P("M -150,-108 C -120,-124 -80,-130 -50,-124", stroke=rim, sw=2, op=.85, flt="glow"))
    out.append(P("M -140,-100 C -130,-96 -120,-96 -110,-100 M -128,-112 c 6,4 14,4 20,0", stroke="#2a2036", sw=1.6))
    return "".join(out)


def murmur(s=1, facing=-1, chest=True, rim=VIO):
    """hyena-like smoke beast in profile; origin at feet centre."""
    out = []
    rnd = random.Random(7)
    for i in range(9):
        x = -40 + i * 16 + rnd.uniform(-4, 4)
        y = -126 + i * 5
        L = rnd.uniform(40, 90)
        sx = rnd.uniform(-20, 30)
        out.append(P(f"M {x - 6},{y + 6} C {x - 4},{y - L * .4} {x + sx},{y - L * .6} {x + sx * 1.4},{y - L} C {x + sx + 4},{y - L * .5} {x + 6},{y - L * .3} {x + 6},{y + 6} Z", "#120c1a", op=.8))
    for pts in ([(-48, -66, 18), (-38, -34, 11), (-50, -4, 7)], [(-26, -64, 18), (-18, -32, 11), (-28, -3, 7)],
                [(60, -62, 22), (82, -36, 13), (64, -4, 7)], [(80, -60, 20), (98, -34, 12), (86, -3, 7)]):
        out.append(tube(pts, "#120c1a", "#06040a", stroke=LINE, sw=1.4))
    body = "M -70,-76 C -84,-114 -62,-138 -30,-138 C 10,-138 60,-114 92,-92 C 108,-80 106,-58 88,-54 C 60,-46 20,-54 -10,-56 C -40,-58 -64,-60 -70,-76 Z"
    out.append(G(P(body, "#100a18"), 0, 0, flt="smoke"))
    out.append(P(body, "#17101f", stroke=LINE, sw=1.6))
    out.append(P("M -60,-120 C -30,-140 30,-126 92,-92", stroke=rim, sw=2.4, op=.85, flt="glow"))
    for x in range(-40, 80, 18):
        out.append(P(f"M {x},-130 l 4,-10 l 4,10", stroke="#2a2036", sw=1.6))
    if chest:
        out.append(C(-44, -86, 24, rim, op=.45, flt="blur6") + C(-44, -86, 7, "#d9c4ff", flt="glow"))
    for i, x in enumerate(range(-20, 84, 22)):
        y = -84 + (i % 2) * 8
        out.append(P(f"M {x - 9},{y} Q {x},{y - 7} {x + 9},{y} Q {x},{y + 6} {x - 9},{y} Z", "#05030a", stroke="#3a2a4a", sw=1))
        out.append(P(f"M {x - 7},{y} l 2,2 l 2,-2 l 2,2 l 2,-2 l 2,2 l 2,-2", stroke="#e0d8ea", sw=.9))
        out.append(E(x, y + 1, 4, 1.4, rim, op=.6, flt="glow"))
    out.append(murmur_skull(rim))
    out.append(particles(-160, -190, 300, 120, n=18, color="#2a1a40", rmax=4, seed=3, op=.8, flt="blur2"))
    return G("".join(out), 0, 0, s, sx=-facing * s)


def wail(s=1):
    """heron-necked horse with a white screaming mask; origin feet centre, faces left."""
    out = []
    out.append(P("M -70,-210 C -40,-250 60,-250 90,-210 C 110,-180 96,-150 60,-146 L -50,-146 C -80,-150 -90,-184 -70,-210 Z", "#120c1a", stroke=LINE, sw=1.8))
    for x, k in ((-50, 0), (-24, 1), (44, 0), (70, 1)):
        out.append(tube([(x, -160, 18), (x - 6 + k * 8, -90, 12), (x - 2, -40, 10), (x + 4, 0, 6)], "#120c1a", None, stroke=LINE, sw=1.6))
    out.append(tube([(-60, -214, 30), (-100, -290, 20), (-110, -360, 16), (-132, -420, 14)], "#120c1a", None, stroke=LINE, sw=1.8))
    # screaming mask
    m = P("M 0,-30 C 26,-30 30,0 26,24 C 20,46 8,60 0,62 C -8,60 -20,46 -26,24 C -30,0 -26,-30 0,-30 Z", "#ece8e2", stroke=LINE, sw=2)
    m += E(-10, -4, 6, 9, "#0a060e") + E(10, -4, 6, 9, "#0a060e") + E(0, 34, 11, 20, "#0a060e") + E(0, 34, 6, 12, "#3a1a4a", op=.8)
    m += P("M -18,-24 C -8,-30 6,-30 14,-26", stroke="#fff", sw=2.4, op=.9)
    out.append(G(m, -140, -446, 1, rot=-18))
    out.append(tendrils(-60, -150, 90, -150, 9, 60, "#120c1a", seed=12, w=(6, 12), sway=14))
    out.append(C(10, -200, 14, VIO, op=.4, flt="blur6") + C(10, -200, 5, "#d9c4ff", flt="glow"))
    return G("".join(out), 0, 0, s)


def dirge(s=1):
    """hulking sludge giant with a cage-ribcage; origin feet centre."""
    out = []
    out.append(G(P("M -150,0 C -190,-160 -170,-360 -80,-440 C -20,-490 60,-480 110,-430 C 180,-350 190,-160 150,0 Z", "#0e0a14"), 0, 0, flt="smoke2"))
    out.append(P("M -140,0 C -176,-160 -160,-350 -80,-430 C -20,-476 60,-468 104,-422 C 170,-340 180,-160 140,0 Z", "#130e1a", stroke=LINE, sw=2))
    # ribcage glow
    out.append(E(0, -260, 70, 90, VIO, op=.4, flt="blur14"))
    for i in range(6):
        y = -330 + i * 26
        out.append(P(f"M -10,{y} C -60,{y - 4} -86,{y + 18} -80,{y + 40} M 10,{y} C 60,{y - 4} 86,{y + 18} 80,{y + 40}", stroke="#d8cfe0", sw=5))
    out.append(P("M 0,-350 L 0,-170", stroke="#d8cfe0", sw=7))
    out.append(C(0, -260, 14, "#efe2ff", flt="glow2"))
    # many dangling hands
    rnd = random.Random(5)
    for i in range(9):
        x = rnd.uniform(-150, 150)
        y = rnd.uniform(-380, -160)
        L = rnd.uniform(60, 130)
        out.append(tube([(x, y, 12), (x + rnd.uniform(-20, 20), y + L * .6, 9), (x + rnd.uniform(-20, 20), y + L, 7)], "#1a1422", None, stroke=LINE, sw=1.4))
    # face: smooth with one vertical mouth
    out.append(E(0, -440, 44, 52, "#1a1422", stroke=LINE, sw=2))
    out.append(P("M -4,-470 Q 0,-476 4,-470 L 6,-410 Q 0,-402 -6,-410 Z", "#05030a", stroke="#5a4a6a", sw=1.2))
    out.append(P("M -3,-466 l 3,4 l 3,-4 M -4,-446 l 4,4 l 4,-4 M -4,-426 l 4,4 l 4,-4", stroke="#ddd", sw=1))
    return G("".join(out), 0, 0, s)


def lament(s=1):
    """towering veiled weeping figure of black water; origin feet centre."""
    out = []
    out.append(mist(-260, -200, 520, 220, n=6, color="#2a1e4a", op=.6, seed=7, rmin=90, rmax=170))
    out.append(P("M -40,-760 C -110,-700 -150,-420 -230,0 L 230,0 C 150,-420 110,-700 40,-760 Z", "#0b0812", stroke=LINE, sw=2))
    out.append(tendrils(-228, -10, 228, -10, 18, 60, "#0b0812", seed=21, w=(12, 26), sway=20))
    # veil
    out.append(P("M -60,-820 C -90,-800 -110,-700 -130,-560 C -60,-520 60,-520 130,-560 C 110,-700 90,-800 60,-820 C 30,-850 -30,-850 -60,-820 Z", "#24203a", stroke=LINE, sw=2, op=.95))
    out.append(P("M -50,-800 C -70,-720 -80,-640 -96,-570 M 40,-806 C 56,-720 70,-640 90,-570 M 0,-830 L 0,-540", stroke="#5a5480", sw=1.6, op=.7))
    out.append(E(0, -760, 30, 40, "#05030a", op=.85))
    for x in (-12, 12):
        out.append(P(f"M {x},-760 C {x - 2},-700 {x + 4},-640 {x},-560", stroke="#bfe6ff", sw=2.4, op=.85, flt="glow"))
    # willow arms
    for s_ in (-1, 1):
        out.append(P(f"M {s_ * 70},-620 C {s_ * 170},-560 {s_ * 220},-400 {s_ * 240},-200", stroke="#0b0812", sw=22))
        for k in range(5):
            out.append(P(f"M {s_ * (200 + k * 8)},{-330 + k * 22} C {s_ * (210 + k * 10)},{-250 + k * 22} {s_ * (204 + k * 6)},{-170 + k * 20} {s_ * (214 + k * 10)},{-100 + k * 18}", stroke="#0b0812", sw=5))
    # faded red thread at the throat
    out.append(P("M -26,-700 Q 0,-690 26,-700", stroke="#a02a2a", sw=4, op=.8))
    out.append(E(0, -440, 60, 120, VIO, op=.35, flt="blur14") + C(0, -440, 10, "#efe2ff", flt="glow2"))
    return G("".join(out), 0, 0, s)


def crumb(s=1, scared=False):
    out = []
    out.append(G(C(0, -26, 26, "#16101e"), 0, 0, flt="smoke"))
    out.append(C(0, -26, 22, "#1c1426", stroke=LINE, sw=1.4))
    out.append(C(-10, -40, 9, "#2a2038", op=.8))
    for x in (-14, -5, 5, 14):
        out.append(R(x - 3, -10, 6, 10, "#16101e", rx=3))
    ey = -28
    if scared:
        out.append(C(-8, ey, 4.4, "#ffffff") + C(8, ey, 4.4, "#ffffff"))
        out.append(P("M -18,-12 l 3,-3 l 3,3 M 14,-12 l 3,-3 l 3,3", stroke="#9ad", sw=1))
    else:
        out.append(C(-8, ey, 3.6, "#ffffff") + C(8, ey, 3.6, "#ffffff"))
    return G("".join(out), 0, 0, s)


def human_silhouette(h=500, col="#2a2440"):
    s = h / 1000
    d = ("M 0,0 C 30,0 40,30 38,60 C 36,90 24,110 14,120 L 60,140 C 80,150 86,170 86,200 L 92,420 L 72,420 L 64,240 L 56,480 L 52,960 L 12,960 L 6,560 L -6,560 L -12,960 L -52,960 L -56,480 L -64,240 L -72,420 L -92,420 L -86,200 "
         "C -86,170 -80,150 -60,140 L -14,120 C -24,110 -36,90 -38,60 C -40,30 -30,0 0,0 Z")
    return G(P(d, col), 0, -h, s)
