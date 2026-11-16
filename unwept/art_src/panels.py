"""Chapter 1 'The Anniversary Run': 60 illustrated panels. Each returns dict(h, svg, L=letters)."""
import math, random
from art import *
from chars import head, CAST, back_head
from figures import figure, tube
from beasts import hush, hush_mask, murmur, murmur_skull, crumb, human_silhouette
from scenes import *

W = 800
MON = dict(rim="#6fb8ff", shade="#16244e", amb="#4a6aa8", amb_t=.22, key="#cfe6ff")
RAIN = dict(rim="#9fb2d6", shade="#2a3050", amb="#8a9ab8", amb_t=.14, key="#e8eeff")
VIOL = dict(rim="#b48cff", shade="#2a1450", amb="#7a5aa8", amb_t=.22, key="#efe4ff")
UNDER = dict(rim="#ffcf6a", shade="#2a1450", amb="#8a5cff", amb_t=.28, key="#f4e4ff", rim_side=-1)


def hd(key, x, y, s, expr=None, lit=None, rot=0, flip=False, body=True, over=None):
    return G(head(key, expr, lit, body=body, cfg_over=over), x, y, s, rot=rot, sx=(-s if flip else None))


def fig(key, fkey, x, ground, s, expr=None, rim="#9a7bff", lit=None):
    g, sc = figure(key, fkey, expr=expr, rim=rim, lit=lit)
    k = s * sc
    return G(g, x, ground - 965 * k, k)


def cap(x, y, w, text, style=""):
    return dict(t="cap", x=x, y=y, w=w, text=text, style=style)


def bub(x, y, w, text, tail="b", tx=30, style=""):
    return dict(t="bub", x=x, y=y, w=w, text=text, tail=tail, tx=tx, style=style)


def chat(x, y, w, rows, style=""):
    return dict(t="chat", x=x, y=y, w=w, rows=rows, style=style)


def pnl(h, svg, L=None, cls=""):
    return dict(h=h, svg=svg, L=L or [], cls=cls)


def drip_window(x, y, w, lines, size=30, title=None, kind="under"):
    """Undertally black-glass window with violet ink drips."""
    g, h = sys_window(x, y, w, lines, kind=kind, size=size, title=title)
    rnd = random.Random(len("".join(lines)))
    if kind == "under":
        for _ in range(int(w / 26)):
            dx = rnd.uniform(x + 20, x + w - 20)
            L = rnd.uniform(10, 46)
            g += P(f"M {dx - 3:.0f},{y + h} Q {dx:.0f},{y + h + L:.0f} {dx + 3:.0f},{y + h} Z", "#8a5cff", op=.85) + C(dx, y + h + L + 4, 3.2, "#b48cff", op=.9, flt="glow")
    return g, h


def notes(cx, cy, n=6, spread=260, seed=3, col="#ffd56b"):
    rnd = random.Random(seed)
    return "".join(note_glyph(cx + rnd.uniform(-spread, spread), cy + rnd.uniform(-spread * .5, spread * .5), rnd.uniform(.6, 1.2), col) for _ in range(n))


def rain_bg(h, seed=1, lamp=True):
    g = vgrad(W, h, [(0, "#0a0e18"), (.6, "#121a2a"), (1, "#070a10")])
    if lamp:
        g += rglow(W * .86, h * .18, 160, "#ffcf7a", .35) + C(W * .86, h * .18, 6, "#ffe9b8", flt="glow2")
    return g


def chart_rows(*rows):
    cols = ["#9d8cff", "#6fd0ff", "#ffb35a", "#7ee08a", "#ff7aa8", "#f2c35a", "#c8c8d8"]
    names = ["pixelpilgrim", "noresetnate", "frame_eater", "lilsprout", "anyp3rcent", "glitchgran", "ttv_moth", "clipqueen", "mod_owl", "deadzone"]
    return [(names[i % len(names)], r, cols[i % len(cols)]) for i, r in enumerate(rows)]


def apartment(h, glow=1.0, figure_back=True):
    g = vgrad(W, h, [(0, "#06070c"), (1, "#0c0f18")])
    g += R(0, h * .66, W, h * .34, "#0e0f16") + R(0, h * .66, W, 6, "#1c2030")
    g += R(560, h * .1, 150, 170, "#d8d4c8", stroke=LINE, sw=2, op=.85)
    g += R(560, h * .1, 150, 30, "#b23a3a", op=.9) + T(635, h * .1 + 22, "MARCH", 18, "#fff", anchor="middle", font="Arial", weight="bold")
    for i in range(5):
        for j in range(7):
            g += R(568 + j * 20, h * .1 + 38 + i * 26, 16, 20, "none", stroke="#9a968a", sw=.8)
    g += E(651, h * .1 + 114, 16, 14, "none", stroke="#d02a2a", sw=3.4) + T(640, h * .1 + 160, "MOM — 13", 16, "#d02a2a", font="Patrick Hand")
    g += C(90, h * .36, 56, "none", stroke="#2a2c36", sw=10) + P(f"M 90,{h * .36 + 56} L 90,{h * .66}", stroke="#2a2c36", sw=5)
    g += P(f"M 90,{h * .66} Q 130,{h * .7} 120,{h * .78}", stroke="#2a2c36", sw=2)
    mons = [(150, h * .26, 160, 120, "#4a8ad8"), (330, h * .2, 240, 170, "#5a9cff"), (590, h * .36, 130, 100, "#4a7ac8")]
    for x, y, w, hh, col in mons:
        inner = pixel_screen("title", int(w), int(hh), ps=4) if w > 200 else R(x, y, w, hh, "#0e1a36") + "".join(R(x + 8, y + 10 + k * 12, w * .6 * (0.4 + (k % 3) * .2), 6, "#3a6aaa", op=.8) for k in range(int(hh / 14)))
        if w > 200:
            inner = G(inner, x, y)
        g += monitor(x, y, w, hh, inner, glow=col)
        g += P(f"M {x + w / 2 - 10},{y + hh + 10} L {x + w / 2 - 20},{h * .66} L {x + w / 2 + 20},{h * .66} L {x + w / 2 + 10},{y + hh + 10} Z", "#0a0a0e")
    for i, (x, col) in enumerate(((140, "#3ad06a"), (178, "#e2544a"), (690, "#3ad06a"), (730, "#4aa3ff"))):
        g += can(x, h * .66 + 2, 1.0, col, tipped=(i == 3))
    g += R(0, h * .64, W, h * .36, "#4a8ad8", op=.06 * glow)
    return g

# ------------------------------------------------------------------ the panels

def build():
    P_ = []
    # P1 -----------------------------------------------------------------------------------------
    h = 900
    g = R(0, 0, W, h, "#030408") + rain(W, h, n=260, color="#b8c8e6", op=.32, seed=1) + rain(W, h, n=60, color="#ffffff", op=.5, seed=2)
    for i, x in enumerate((60, 190, 330, 470, 610, 740)):
        g += gravestone(x, h + 10 - (i % 2) * 20, .9 + (i % 3) * .15, col="#0c0f16")
    g += P(f"M 0,{h - 70} Q 400,{h - 110} 800,{h - 70}", stroke="#2a3446", sw=1.2, op=.6)
    g += T(730, 300, "shhhhhhhhhh", 30, "#8a9ab8", font="Patrick Hand", rot=90, op=.8, ls=3)
    g += vignette(W, h, .9)
    P_.append(pnl(h, g, [cap(6, 6, 42, "Thirteen years ago.", "time")]))
    # P2 -----------------------------------------------------------------------------------------
    h = 560
    g = rain_bg(h, 2, lamp=False) + rain(W, h, n=120, color="#c8d8f0", op=.25, seed=3)
    g += tube([(560, 320, 96), (700, 300, 116), (860, 290, 130)], "#15161d", "#05060a", cap=False)
    g += P("M 548,262 L 566,372", stroke="#e8e8ee", sw=10) + P("M 548,262 L 566,372", stroke=LINE, sw=1)
    g += hand2(548, 318, ang=-96, s=2.3, skin=mix("#efd9c8", "#6a7a9a", .2), curl=(.25, .2, .22, .3), thumb=.4, spread=.35)
    g += tube([(-60, 360, 120), (120, 350, 100), (245, 345, 80)], "#f2c230", "#a77a12", cap=False)
    g += P("M 236,300 Q 256,346 238,392", stroke="#c9961c", sw=8)
    g += hand2(262, 344, ang=96, s=1.45, skin=mix("#f6dfcf", "#6a7a9a", .15), curl=(.8, .75, .75, .8), thumb=.1, side=-1, spread=.4)
    rnd = random.Random(5)
    for _ in range(14):
        x, y = rnd.uniform(250, 560), rnd.uniform(250, 380)
        g += P(f"M {x:.0f},{y:.0f} q 4,6 0,9 q -4,-3 0,-9 Z", "#dff0ff", op=.85) + C(x - 1, y + 5, 1, "#fff")
    g += T(140, 140, "pat...", 34, "#a8bad8", font="Patrick Hand", rot=-8) + T(600, 520, "pat...", 30, "#a8bad8", font="Patrick Hand", rot=6)
    g += vignette(W, h, .8)
    P_.append(pnl(h, g))
    # P3 -----------------------------------------------------------------------------------------
    h = 1000
    g = rain_bg(h, 3) + R(0, h * .82, W, h * .18, "#0b0d14")
    for i, x in enumerate((40, 150, 260, 520, 630, 740)):
        g += umbrella_mourner(x, h * .8, 1.2, bend=.6 + (i % 3) * .14, col="#0b0d14", seed=i)
    g += umbrella_mourner(700, h * .9, 1.55, bend=.8, col="#0d1018", seed=9)
    g += umbrella_mourner(110, h * 1.02, 2.0, bend=.95, col="#3c414c", umb="#1a1d26", seed=11, rim="#9fb2d6")
    g += gravestone(560, h * .93, 1.55, col="#2a3040", text=["MIRIAM REED", "SHE MADE", "WORLDS"])
    g += fig("jonah11", "jonah11", 360, h * .93, .36, expr=dict(wet=True, hl=False), rim="#9fb2d6")
    g += fig("lily4", "lily4", 430, h * .93, .42, expr=dict(wet=True, look=(-3, -3)), rim="#9fb2d6")
    g += C(398, h * .93 - 965 * .266 + 500 * .266 + 8, 7, "#e9d4c4", stroke=LINE, sw=1.2)
    g += rain(W, h, n=240, color="#c8d8f0", op=.3, seed=4) + vignette(W, h, .7)
    P_.append(pnl(h, g, [cap(5, 5, 40, "Everyone cried.")]))
    # P4 -----------------------------------------------------------------------------------------
    h = 640
    g = rain_bg(h, 4) + rglow(560, 300, 260, "#f2c230", .12)
    g += hd("lily4", 460, 330, 2.05, dict(look=(0, -4), brow="worried", mouth="o", wet=True, welling=True), RAIN, rot=-8)
    g += rain(W, h, n=120, color="#c8d8f0", op=.28, seed=6) + vignette(W, h, .75)
    P_.append(pnl(h, g, [bub(4, 8, 38, "Jojo... are you crying?", "r", 70), bub(84, 30, 14, "No.", "r", 50, "off")]))
    # P5 -----------------------------------------------------------------------------------------
    h = 640
    g = rain_bg(h, 5, lamp=False) + rglow(200, 200, 260, "#9fb2d6", .12)
    g += hd("jonah11", 420, 300, 2.3, dict(wet=True, hl=False), RAIN)
    g += rain(W, h, n=120, color="#c8d8f0", op=.28, seed=7) + vignette(W, h, .8)
    P_.append(pnl(h, g, [bub(3, 6, 22, "Why not?", "l", 30, "small off"), bub(64, 70, 33, "'Cause you're holding on.", "t", 30)]))
    # P6 -----------------------------------------------------------------------------------------
    h = 900
    g = rain_bg(h, 6) + R(0, h * .7, W, h * .3, "#090b11")
    rnd = random.Random(8)
    for i in range(14):
        x = 30 + i * 56 + rnd.uniform(-10, 10)
        if 5 < i < 8:
            continue
        g += umbrella_mourner(x, h * .7 + rnd.uniform(-6, 10), .62, bend=.9 + rnd.uniform(0, .25), col="#0c0f16", seed=i + 20)
    g += G(human_silhouette(150, "#05060a"), 392, h * .72) + G(human_silhouette(96, "#05060a"), 418, h * .72)
    g += P(f"M 392,{h * .72 - 150} L 392,{h * .72 - 168}", stroke="#9fb2d6", sw=1, op=.0)
    g += rglow(400, h * .64, 70, "#9fb2d6", .25)
    g += rain(W, h, n=280, color="#c8d8f0", op=.28, seed=9) + vignette(W, h, .8)
    P_.append(pnl(h, g, [cap(5, 6, 44, "Somebody had to be still."), cap(52, 80, 26, "So I was."), cap(58, 89, 38, "I just never stopped.")]))
    P_.append(dict(gutter=420))
    # P7 -----------------------------------------------------------------------------------------
    h = 720
    g = apartment(h)
    g += G(back_head("jonah", rim="#6fb8ff", cloth="#3a3c44"), 450, 520, 1.15)
    g += P("M 384,560 C 400,600 500,600 516,560", stroke="#121216", sw=10)
    g += vignette(W, h, .7)
    P_.append(pnl(h, g, [cap(4, 4, 34, "Now. 1:47 a.m.", "time")]))
    # P8 -----------------------------------------------------------------------------------------
    h = 560
    g = vgrad(W, h, [(0, "#0a0c14"), (1, "#141824")]) + R(0, 0, W, h, "#2a1e16", op=.4)
    for k in range(8):
        g += P(f"M 0,{60 + k * 70} Q 400,{40 + k * 70} 800,{70 + k * 70}", stroke="#3a2c20", sw=2, op=.5)
    scr = T(0, -150, "1:47", 64, "#f4f6ff", anchor="middle", font="Arial") + T(0, -112, "Tuesday, March 14", 18, "#c8d0e8", anchor="middle", font="Arial")
    scr += R(-160, -70, 320, 104, "#f4f5fa", rx=14, op=.96) + C(-134, -36, 15, "#f2c230") + T(-134, -30, "L", 16, "#3a2a10", anchor="middle", font="Arial", weight="bold")
    scr += T(-110, -42, "LILY", 18, "#111", font="Arial", weight="bold") + T(130, -42, "now", 14, "#777", anchor="end", font="Arial")
    scr += T(-110, -16, "thinking about mom today.", 16, "#333", font="Arial") + T(-110, 8, "call me after your run?", 16, "#333", font="Arial")
    g += phone(400, 280, 360, 500, scr, rot=-6)
    g += vignette(W, h, .7)
    P_.append(pnl(h, g))
    # P9 -----------------------------------------------------------------------------------------
    h = 560
    g = vgrad(W, h, [(0, "#0a0c14"), (1, "#141824")])
    scr = R(-170, -240, 340, 50, "#1c2030") + T(-150, -208, "‹  Lily", 22, "#cfe0ff", font="Arial")
    scr += R(-150, -170, 260, 44, "#2a3a5a", rx=18) + T(-136, -142, "thinking about mom today.", 15, "#e8eeff", font="Arial")
    scr += R(-150, -118, 230, 44, "#2a3a5a", rx=18) + T(-136, -90, "call me after your run?", 15, "#e8eeff", font="Arial")
    scr += R(-160, 0, 320, 44, "#f4f5fa", rx=20) + T(-140, 29, "o", 22, "#111", font="Arial") + R(-125, 9, 2.5, 26, "#3a7aff")
    for r in range(3):
        for k in range(9):
            scr += R(-160 + k * 36, 64 + r * 50, 32, 42, "#2a2e3a", rx=6)
    scr += R(92, 164, 64, 42, "#4a5068", rx=6) + T(124, 192, "⌫", 22, "#fff", anchor="middle", font="Arial")
    g += phone(400, 300, 360, 520, scr)
    g += thumb_press(520, 476, 1.7, skin=mix("#efd9c8", "#4a6aa8", .2))
    g += sfx(640, 430, "tk.", 46, "#cfe0ff", rot=-8, sw=5)
    P_.append(pnl(h, g, [cap(4, 6, 28, "After the run.")]))
    # P10 ----------------------------------------------------------------------------------------
    h = 780
    g = apartment(h, figure_back=False) + R(0, 0, W, h, "#000", op=.45)
    g += hd("jonah", 400, 300, 1.6, dict(mouth="flat"), MON)
    g += tube([(540, 900, 96), (470, 740, 74), (440, 676, 64)], "#7c7f88", "#4a4c54", cap=False)
    g += hand2(438, 678, ang=-38, s=1.25, skin=mix("#efd9c8", "#4a6aa8", .22), curl=(.0, .0, .95, .95), thumb=.8, side=-1, spread=.3)
    g += vignette(W, h, .7)
    P_.append(pnl(h, g, [cap(4, 5, 42, "The chest thing again. Three weeks now."), cap(3, 86, 34, "Heartburn. Probably.")]))
    # P11 ----------------------------------------------------------------------------------------
    h = 440
    g = R(0, 0, W, h, "#0a0d16")
    mid = uid("cr")
    g += f'<defs>{clip(mid, f"M 0,0 h {W} v {h} h {-W} Z")}</defs><g clip-path="url(#{mid})">' + hd("jonah", 400, 20, 5.0, dict(mouth="open"), MON) + "</g>"
    for x, y in ((372, 262), (424, 236)):
        g += E(x, y, 14, 9, "#f4f6ff", stroke=LINE, sw=2) + P(f"M {x - 9},{y} L {x + 9},{y}", stroke="#c8ccd8", sw=1.6) + P(f"M {x},{y - 20} l 0,-40 M {x - 8},{y - 18} l -1,-30 M {x + 8},{y - 18} l 1,-30", stroke="#ffffff", sw=2, op=.7)
    g += sfx(640, 120, "krnch", 54, "#e8eeff", rot=8, sw=6)
    P_.append(pnl(h, g))
    # P12 ----------------------------------------------------------------------------------------
    h = 560
    inner = G(pixel_screen("title", 700, 400, ps=6), 50, 80)
    inner += R(50, 40, 700, 40, "#0e1220") + C(76, 60, 8, "#ff3a4a", flt="glow") + T(92, 68, "LIVE", 22, "#ff6a7a", font="VT323")
    inner += T(160, 68, "STILLWATER — ANNUAL RUN", 26, "#e8eeff", font="VT323")
    inner += R(50, 480, 700, 40, "#0e1220") + T(66, 508, "untitled_mom_build_09 — ANY%", 26, "#c9a5ff", font="VT323")
    inner += T(560, 68, "812", 24, "#6a7088", font="VT323") + P("M 556,62 L 596,62", stroke="#6a7088", sw=2)
    inner += T(604, 68, "2,340", 24, "#8a90a8", font="VT323") + P("M 600,62 L 652,62", stroke="#8a90a8", sw=2) + T(660, 68, "4,019", 28, "#7ee08a", font="VT323", flt="glow")
    inner += R(560, 330, 170, 130, "#05060a", stroke="#3a3f58", sw=2)
    inner += G(head("jonah", dict(mouth="flat"), MON), 645, 400, .42)
    g = monitor(30, 30, 740, 500, inner, glow="#5a9cff")
    P_.append(pnl(h, g))
    # P13 ----------------------------------------------------------------------------------------
    h = 600
    g = vgrad(W, h, [(0, "#090b14"), (1, "#0e1222")]) + R(170, 20, 460, 560, "#0b0e1a", rx=12, stroke="#2a3150", sw=2)
    g += T(190, 54, "STREAM CHAT", 24, "#8a90a8", font="VT323") + P("M 190,66 L 610,66", stroke="#2a3150", sw=1.5)
    P_.append(pnl(h, g, [chat(23, 13, 54, chart_rows("the robot returns", "year 13. respect", "does this man own facial muscles", "only human alive who runs this game lol", "world record vs himself AGAIN"))]))
    # P14 ----------------------------------------------------------------------------------------
    h = 720
    g = apartment(h) + R(0, 0, W, h, "#000", op=.5)
    g += hd("jonah", 400, 320, 1.6, dict(mouth="flat", headset=True), MON)
    g += vignette(W, h, .7)
    P_.append(pnl(h, g, [bub(4, 6, 40, "Hey. Same rules as every year.", "r", 75, "flat"), bub(58, 22, 38, "No commentary. No resets.", "l", 25, "flat"),
                         chat(54, 80, 44, chart_rows('he said "hey." he\'s chatty tonight'), "mini")]))
    # P15 ----------------------------------------------------------------------------------------
    h = 500
    g = monitor(14, 14, 772, 472, G(pixel_screen("title", 772, 472, ps=8), 14, 14), glow="#8a5cff", bezel=8)
    P_.append(pnl(h, g))
    # P16 ----------------------------------------------------------------------------------------
    h = 620
    g = vgrad(W, h, [(0, "#0a0b12"), (1, "#141824")])
    for sx_ in (90, 710):
        g += R(sx_ - 50, 120, 100, 200, "#121318", rx=8, stroke=LINE, sw=2) + C(sx_, 180, 30, "#0a0a0e", stroke="#2a2c36", sw=4) + C(sx_, 270, 18, "#0a0a0e", stroke="#2a2c36", sw=3)
    g += controller(400, 430, 1.35)
    g += G(tube([(560, 700, 70), (470, 520, 44), (444, 470, 30), (432, 440, 22)], mix("#efd9c8", "#4a6aa8", .2), "#7a6a8a"), 0, 0)
    g += speed_lines(432, 440, 300, 300, n=24, r0=40, color="#ffd56b", op=.35, seed=4)
    g += notes(400, 190, n=9, spread=300, seed=7)
    g += sfx(400, 140, "TING-TA-LING ♪", 70, "#ffd56b", rot=-4, glow="glow", sw=7)
    P_.append(pnl(h, g, [cap(3, 70, 30, "Her chime. Three notes."), cap(56, 78, 42, 'She wrote it on our kitchen keyboard when I was seven, then made me press "start" forty times to "test it."')]))
    # P17 ----------------------------------------------------------------------------------------
    h = 520
    g = monitor(14, 14, 772, 492, G(pixel_screen("dialog", 772, 492, ps=8), 14, 14), glow="#8a5cff", bezel=8)
    P_.append(pnl(h, g, [dict(t="pix", x=8, y=66, w=86, text='"Hi, kiddos. This one isn\'t finished yet. Neither am I, probably. Be nice to the bugs. Bugs are secret doors."')]))
    # P18 ----------------------------------------------------------------------------------------
    h = 520
    g = vgrad(W, h, [(0, "#06070c"), (1, "#10131c")]) + controller(400, 300, 2.2, glow="#5a9cff")
    sk = mix("#efd9c8", "#4a6aa8", .22)
    g += G(thumb_press(0, 0, 2.0, sk), 230, 300) + G(thumb_press(0, 0, 2.0, sk), 600, 300, sx=-2.0, s=2.0).replace("scale(-2.0,2.0)", "scale(-2.0,2.0)")
    g += vignette(W, h, .8)
    P_.append(pnl(h, g, [cap(4, 6, 46, "Every year, I lose exactly one frame here.")]))
    # P19 ----------------------------------------------------------------------------------------
    h = 500
    g = vgrad(W, h, [(0, "#06070c"), (1, "#10131c")]) + controller(400, 330, 2.0, glow="#5a9cff")
    g += G(thumb_press(0, 0, 1.8, sk), 250, 330) + G(thumb_press(0, 0, 1.8, sk), 560, 320, sx=-1.8, s=1.8)
    for x, y in ((250, 300), (560, 290)):
        g += P(f"M {x - 60},{y - 50} q -20,20 0,40 M {x + 60},{y - 50} q 20,20 0,40", stroke="#cfe0ff", sw=3, op=.7)
    g += R(220, 30, 360, 90, "#05060a", rx=8, stroke="#7ee08a", sw=2, op=.9) + T(400, 98, "00:00.000", 72, "#7ee08a", anchor="middle", font="VT323", flt="glow")
    g += sfx(130, 200, "tak", 50, "#e8eeff", rot=-12, sw=6) + sfx(680, 210, "tak", 50, "#e8eeff", rot=10, sw=6) + sfx(420, 460, "tak", 44, "#e8eeff", rot=-4, sw=6)
    P_.append(pnl(h, g))
    # P20 ----------------------------------------------------------------------------------------
    h = 640
    cid = uid("dg")
    g = R(0, 0, W, h, "#05060a") + f'<defs>{clip(cid, f"M 0,40 L {W},0 L {W},{h - 60} L 0,{h} Z")}</defs>'
    g += f'<g clip-path="url(#{cid})">' + G(pixel_screen("forest", 900, 680, ps=8), -50, -20, rot=-3) + speed_lines(470, 300, 900, 700, n=50, r0=260, color="#ffffff", op=.15, seed=2) + "</g>"
    g += P(f"M 0,40 L {W},0 M {W},{h - 60} L 0,{h}", stroke="#c9a5ff", sw=3)
    P_.append(pnl(h, g, [chat(54, 8, 42, chart_rows("THE BARRIER CLIP", "three frames. THREE."), "mini"),
                         cap(3, 66, 46, "Level 2. The barrier pulses every six seconds, and she left a three-frame gap at the refresh."),
                         cap(56, 84, 40, "She called it a bug. I called it a door.")]))
    # P21 ----------------------------------------------------------------------------------------
    h = 440
    g = monitor(14, 14, 772, 412, G(pixel_screen("levelup", 772, 412, ps=8), 14, 14), glow="#ffd56b", bezel=8)
    g += sfx(560, 120, "TING-TA-LING", 48, "#ffd56b", rot=8, glow="glow", sw=6)
    P_.append(pnl(h, g, [chat(3, 74, 30, chart_rows("the chime :')"), "mini")]))
    # P22 ----------------------------------------------------------------------------------------
    h = 600
    g = R(0, 0, W, h, "#05070e") + rglow(400, 300, 380, "#3a6aaa", .3)
    g += hd("jonah", 400, 250, 2.3, dict(mouth="flat", sweat=True, headset=True), MON)
    g += sfx(130, 520, "thmp...", 44, "#d0465a", rot=-6, sw=5) + sfx(650, 560, "thmp...", 38, "#d0465a", rot=6, sw=5)
    g += vignette(W, h, .7)
    P_.append(pnl(h, g, [cap(66, 6, 30, "Keep going.")]))
    # P23 ----------------------------------------------------------------------------------------
    h = 620
    g = monitor(14, 14, 772, 592, G(pixel_screen("city", 772, 592, ps=8), 14, 14), glow="#8a5cff", bezel=8)
    P_.append(pnl(h, g, [chat(56, 12, 40, chart_rows("the stand-still stealth section lmao", "this game was literally built for him"), "mini"),
                         cap(3, 60, 42, "Level 4. The monsters can't see you. They see your heart meter."),
                         cap(3, 77, 34, "Stay calm and you're invisible."), cap(58, 88, 38, "I was very good at Level 4.")]))
    # P24 ----------------------------------------------------------------------------------------
    h = 440
    g = vgrad(W, h, [(0, "#0a0c14"), (1, "#151926")]) + R(0, 0, W, h, "#2a1e16", op=.35)
    g += phone(400, 260, 380, 200, face_down=True, rot=4)
    for k in range(3):
        g += P(f"M {196 - k * 16},{200 + k * 6} q -10,30 0,60 M {604 + k * 16},{200 + k * 6} q 10,30 0,60", stroke="#cfe0ff", sw=3, op=.7 - k * .2)
    g += sfx(400, 110, "bzzzt", 66, "#cfe0ff", rot=-4, sw=6)
    P_.append(pnl(h, g, [cap(56, 82, 40, "Lily. ...After the run.")]))
    # P25 ----------------------------------------------------------------------------------------
    h = 680
    g = monitor(14, 14, 772, 652, G(pixel_screen("tower", 772, 652, ps=8), 14, 14), glow="#f4f0ff", bezel=8)
    g += T(400, 90, "LEVEL 6 — THE TOWER", 54, "#f4f0ff", anchor="middle", font="VT323", flt="glow")
    P_.append(pnl(h, g, [cap(3, 72, 40, "The last level. She never finished it."), cap(52, 86, 44, "No boss. Just a climb, and a door at the top that doesn't open.")]))
    # P26 ----------------------------------------------------------------------------------------
    h = 560
    g = R(0, 0, W, h, "#070912") + speed_lines(400, 280, W, h, n=60, r0=60, color="#5a6aaa", op=.25, seed=6)
    P_.append(pnl(h, g, [dict(t="burst", items=[("-4.2 PACE", 6, 10, 46, "#7ee08a"), ("HE'S GONNA DO IT AGAIN", 30, 34, 40, "#ffb35a"),
                                                    ("how is he this CALM", 8, 60, 34, "#9d8cff"), ("STILLWATER STILLWATER", 34, 80, 42, "#6fd0ff")])]))
    # P27 ----------------------------------------------------------------------------------------
    h = 920
    g = R(0, 0, W, h, "#030408") + rglow(400, 600, 420, "#3a5aa8", .25)
    g += hd("jonah", 400, 330, 2.0, dict(eyes="pin", sweat=True, mouth="flat", headset=True), dict(MON, rim="#e8f2ff"))
    for seed, (x, y) in enumerate(((400, 700),)):
        g += cracks(x, y, n=9, length=300, color="#e8f2ff", seed=33, sw=4.5)
    g += sfx(170, 860, "THMP—", 70, "#ff4a5a", rot=-8, sw=7, glow="glow") + sfx(420, 900, "THMP—", 76, "#ff4a5a", rot=-2, sw=7, glow="glow") + sfx(660, 860, "THMP—", 70, "#ff4a5a", rot=8, sw=7, glow="glow")
    P_.append(pnl(h, g, [cap(4, 5, 30, "Three more jumps.")]))
    # P28 ----------------------------------------------------------------------------------------
    h = 500
    g = monitor(14, 14, 772, 472, G(pixel_screen("ledge", 772, 472, ps=8), 14, 14), glow="#f4f0ff", bezel=8)
    g += R(540, 400, 220, 50, "#05060a", rx=6, stroke="#7ee08a", sw=2) + T(650, 435, "FRAME 2,473,309", 26, "#7ee08a", anchor="middle", font="VT323")
    P_.append(pnl(h, g, [cap(3, 6, 28, "Three frames.")]))
    # P29 ----------------------------------------------------------------------------------------
    h = 560
    g = R(0, 0, W, h, "#f4f6ff") + speed_lines(470, 330, W, h, n=140, r0=110, color="#05060a", op=.9, seed=8, width=(1, 6))
    g += C(470, 340, 70, "#1c1d24", stroke=LINE, sw=4) + C(470, 340, 52, "#3a7a4a") + C(456, 326, 16, "#8ad8a0", op=.7)
    g += thumb_press(470, 330, 3.4, "#efd9c8")
    g += sfx(220, 170, "TAK.", 150, "#05060a", rot=-10, stroke="#ffffff", sw=10)
    P_.append(pnl(h, g))
    # P30 ----------------------------------------------------------------------------------------
    h = 720
    inner = G(pixel_screen("thanks", 772, 692, ps=8), 14, 14)
    inner += R(200, 520, 400, 110, "#05060a", rx=8, stroke="#ffd56b", sw=3) + T(400, 590, "41:13.207", 70, "#ffd56b", anchor="middle", font="VT323", flt="glow") + T(400, 620, "NEW RECORD", 28, "#7ee08a", anchor="middle", font="VT323")
    g = monitor(14, 14, 772, 692, inner, glow="#ffd56b", bezel=8)
    P_.append(pnl(h, g, [dict(t="burst", items=[("WORLD RECORD", 4, 6, 40, "#ffd56b"), ("LETS GOOOOO", 62, 10, 34, "#7ee08a"), ("13 YEARS", 6, 22, 30, "#6fd0ff"),
                                                    ("SHE'D BE SO PROUD", 52, 26, 30, "#ff7aa8"), ("HIS FACE DIDN'T MOVE LMAO", 4, 88, 30, "#9d8cff"), ("STILLWATER!!!", 60, 90, 38, "#ffb35a")])]))
    # P31 ----------------------------------------------------------------------------------------
    h = 560
    g = apartment(h) + R(0, 0, W, h, "#000", op=.55) + rglow(400, 260, 300, "#ffd56b", .12)
    g += hd("jonah", 400, 230, 1.9, dict(mouth="flat", headset=True), MON)
    g += vignette(W, h, .7)
    P_.append(pnl(h, g, [bub(68, 40, 18, "...GG.", "l", 40)]))
    # P32 ----------------------------------------------------------------------------------------
    h = 520
    g = vgrad(W, h, [(0, "#0a0c14"), (1, "#151926")]) + R(0, 0, W, h, "#2a1e16", op=.35)
    g += phone(620, 320, 300, 170, face_down=True, rot=-6)
    g += tube([(-80, 330, 110), (120, 310, 90), (250, 300, 70)], "#7c7f88", "#4a4c54", cap=False)
    g += hand2(262, 300, ang=96, s=2.0, skin=mix("#efd9c8", "#4a6aa8", .2), curl=(.15, .1, .15, .3), thumb=.3, side=-1)
    for k in range(3):
        g += P(f"M {330 + k * 14},{170 - k * 10} q 10,-12 20,0 M {330 + k * 14},{420 + k * 10} q 10,12 20,0", stroke="#cfe0ff", sw=2.6, op=.75)
    P_.append(pnl(h, g, [cap(3, 6, 34, "Call Lily. Tell her—")]))
    # P33 ----------------------------------------------------------------------------------------
    h = 400
    g = R(0, 0, W, h, "#000") + P("M 0,200 L 160,200 L 190,90 L 220,310 L 250,200 L 380,200 L 410,60 L 440,330 L 470,200 L 800,200", stroke="#ffffff", sw=5, flt="glow")
    g += P("M 0,200 L 160,200 L 190,90 L 220,310 L 250,200 L 380,200 L 410,60 L 440,330 L 470,200 L 800,200", stroke="#ff4a5a", sw=14, op=.25, flt="blur6")
    g += sfx(300, 110, "THMP—", 60, "#ffffff", rot=-4, sw=5) + T(640, 170, "—", 70, "#ffffff", anchor="middle", font="Bangers")
    P_.append(pnl(h, g, cls="neg"))
    # P34 ----------------------------------------------------------------------------------------
    h = 660
    g = apartment(h) + R(0, 0, W, h, "#000", op=.4)
    jg, sc = figure("jonah", "jonah", rim="#6fb8ff")
    g += G(jg, 300, 260, .56, rot=-68)
    g += G(P("M -70,0 L 70,0 L 60,-120 L -60,-120 Z", "#1a1b22", stroke=LINE, sw=3) + P("M 0,0 L 0,90 M -60,90 L 60,90", stroke="#2a2c36", sw=8), 520, 520, rot=38)
    g += controller(650, 600, .55, glow="#5a9cff") + P("M 600,590 C 560,520 520,470 460,430", stroke="#121216", sw=3)
    g += speed_lines(400, 330, W, h, n=40, r0=260, color="#cfe0ff", op=.18, seed=12)
    g += sfx(220, 600, "THUD.", 80, "#e8eeff", rot=-10, sw=7) + sfx(690, 520, "klak.", 44, "#cfe0ff", rot=12, sw=5)
    P_.append(pnl(h, g))
    # P35 ----------------------------------------------------------------------------------------
    h = 780
    g = R(0, 0, W, h, "#04050a") + rglow(400, 180, 360, "#3a6aaa", .35) + R(0, h * .55, W, h * .45, "#121420")
    rnd = random.Random(14)
    for _ in range(260):
        x, y = rnd.uniform(0, W), rnd.uniform(h * .55, h)
        g += P(f"M {x:.0f},{y:.0f} l {rnd.uniform(-3, 3):.0f},-6", stroke="#22263a", sw=1.4)
    g += monitor(160, 40, 480, 240, G(pixel_screen("thanks", 480, 240, ps=5), 160, 40), glow="#5a9cff")
    g += G(head("jonah", dict(eyes="half", mouth="flat", hl=False), MON), 330, 560, 1.5, rot=-90)
    g += phone(640, 640, 160, 260, notif(-74, -40, 148, "LILY", "call me after", 12) + T(0, -80, "1:49", 30, "#f4f6ff", anchor="middle", font="Arial"), rot=82)
    g += P("M 520,760 C 560,700 640,720 700,680", stroke="#121216", sw=4)
    P_.append(pnl(h, g, [chat(56, 6, 40, chart_rows("?", "where'd he go", "stillwater??", "is he ok", "someone call someone"), "mini"),
                         cap(5, 90, 22, "...sorry, Lil.", "tiny")]))
    P_.append(dict(gutter=520, fade=True))
    # P36-37 -------------------------------------------------------------------------------------
    P_.append(pnl(460, R(0, 0, W, 460, "#000"), [cap(16, 40, 68, "They say your life flashes before your eyes.", "center")]))
    h = 460
    g = R(0, 0, W, h, "#000")
    for k in range(8):
        a = k / 8 * math.tau
        g += C(400 + math.cos(a) * 22, 230 + math.sin(a) * 22, 4.2, "#ffffff", op=round(.15 + k * .1, 2))
    P_.append(pnl(h, g, [cap(36, 72, 28, "Mine buffered.", "center")]))
    # P38 ----------------------------------------------------------------------------------------
    h = 1150
    g = void_bg(W, h, 3) + G(human_silhouette(90, "#0a0612"), 400, 560, rot=24) + rglow(400, 520, 90, "#b48cff", .3)
    g += T(690, 200, "fwoooooooooo", 44, "#c9a5ff", font="Bangers", rot=90, ls=6, op=.85)
    P_.append(pnl(h, g))
    # P39 ----------------------------------------------------------------------------------------
    h = 520
    g = void_bg(W, h, 4) + R(0, 0, W, h, "#000", op=.4)
    wg, wh = drip_window(130, 120, 540, ["[ Soul detected. ]", "[ Searching for anchor... ]", "[ Anchor not found. ]"], size=34)
    g += wg
    P_.append(pnl(h, g))
    # P40 ----------------------------------------------------------------------------------------
    h = 720
    g = void_bg(W, h, 5) + G(human_silhouette(220, "#0a0612"), 400, 560, rot=14)
    g += particles(300, 280, 260, 330, n=120, color="#c9a5ff", rmax=3.4, seed=9) + particles(240, 240, 360, 400, n=60, color="#ffffff", rmax=1.6, seed=10)
    wg, wh = drip_window(170, 40, 460, ["[ WARNING: Soul dispersing. ]"], size=32)
    g += wg
    P_.append(pnl(h, g))
    # P41 ----------------------------------------------------------------------------------------
    h = 740
    g = void_bg(W, h, 6) + R(0, 0, W, h, "#000", op=.3)
    g += tube([(760, 800, 120), (640, 660, 96), (560, 580, 80)], "#d8cfe6", "#7a6a9a", cap=False)
    g += hand2(556, 584, ang=-42, s=2.1, skin="#e6def0", shade="#8a7aa8", curl=(.15, .1, .15, .25), thumb=.4, spread=1.7)
    g += particles(200, 120, 360, 330, n=110, color="#d9c4ff", rmax=3.2, seed=11) + particles(240, 200, 300, 300, n=50, color="#ffffff", rmax=1.8, seed=12)
    th = "M -40,120 C 140,160 260,520 480,560"
    for k in range(3):
        th += f" M {470 + k * 18},{612 - k * 16} a 62,20 -40 1 1 1,-1"
    g += P(th, stroke="#ffcf6a", sw=6, flt="glow2") + P(th, stroke="#fff6d8", sw=2)
    P_.append(pnl(h, g, [bub(6, 8, 24, "...got you.", None, 0, "tinyb")]))
    # P42 ----------------------------------------------------------------------------------------
    h = 500
    g = void_bg(W, h, 7) + R(0, 0, W, h, "#000", op=.4)
    wg, wh = drip_window(150, 110, 500, ["[ Soul caught. ]", "[ Body: deceased. ]", "[ Substituting. ]"], size=34)
    g += wg
    P_.append(pnl(h, g))
    # P43 ----------------------------------------------------------------------------------------
    h = 580
    g = R(0, 0, W, h, "#e8e0f4") + speed_lines(400, 330, W, h, n=90, r0=150, color="#2a1a40", op=.5, seed=13)
    g += mud_splash(400, 360, 260, seed=3)
    g += sfx(400, 140, "SHLUMP", 120, "#0a070e", rot=-4, stroke="#e8e0f4", sw=8)
    P_.append(pnl(h, g))
    P_.append(dict(gutter=320))
    # P44 ----------------------------------------------------------------------------------------
    h = 1040
    g = vgrad(W, h, [(0, "#0b0618"), (.5, "#24123e"), (1, "#0a0710")]) + mist(-100, 200, W + 200, 600, n=8, color="#8a5cc0", op=.4, seed=4, rmin=120, rmax=260)
    g += silt_ground(W, h, h * .66, seed=5)
    g += mud_splash(400, h * .68, 170, seed=8)
    g += tube([(400, h * .75, 60), (404, h * .62, 54), (410, h * .5, 46)], "#e2dce6", "#8a7a9a", cap=False)
    g += hand2(410, h * .5, ang=4, s=2.1, skin="#e2dce6", curl=(.05, 0, .05, .1), spread=1.8, thumb=.5, cracks_col="#a673ff")
    g += P("M 392,560 q 6,40 -4,90 M 424,620 q -4,30 4,56 M 404,700 q 3,20 0,40", stroke="#0a070e", sw=6) + cracks(408, 640, 3, 50, "#a673ff", seed=61, base=-1.6, spread=1.2)
    g += sfx(400, 220, "SHLK—!", 100, "#e8e0f4", rot=-6, stroke="#0a070e", sw=9, glow="glow")
    P_.append(pnl(h, g))
    # P45 ----------------------------------------------------------------------------------------
    h = 820
    g = vgrad(W, h, [(0, "#0b0618"), (1, "#1a0e2c")]) + mist(-100, 100, W + 200, 400, n=6, color="#8a5cc0", op=.35, seed=6) + silt_ground(W, h, h * .58, seed=7)
    g += hd("wren_tunic", 400, 330, 1.4, dict(mouth="cough", sludge=True, cracks=True, eyes="half", brow="worried"), VIOL, rot=6)
    for s_ in (-1, 1):
        g += tube([(400 + s_ * 165, 556, 74), (400 + s_ * 250, 650, 60), (400 + s_ * 200, 726, 48)], "#e2dce6", "#7a6a8a")
        g += hand2(400 + s_ * 196, 730, ang=180 - s_ * 30, s=1.4, skin="#d8d0dc", curl=(.45, .4, .45, .5), side=s_, cracks_col="#a673ff", spread=1.3)
        g += cracks(400 + s_ * 230, 660, 3, 40, "#a673ff", seed=50 + s_)
    g += mud_splash(400, 800, 120, seed=21)
    g += silt_ground(W, h, h * .965, seed=8, glossy=False)
    g += sfx(150, 140, "HKK—", 70, "#e8e0f4", rot=-10, sw=7) + sfx(640, 190, "HAKK—", 80, "#e8e0f4", rot=8, sw=7)
    P_.append(pnl(h, g))
    # P46 ----------------------------------------------------------------------------------------
    h = 660
    g = vgrad(W, h, [(0, "#0b0618"), (1, "#24123e")]) + mist(-100, 100, W + 200, 400, n=6, color="#8a5cc0", op=.3, seed=7)
    g += hand2(250, 700, ang=-8, s=2.6, skin="#e2dce6", curl=(.1, .05, .05, .15), spread=1.4, thumb=.4, cracks_col="#a673ff")
    g += hand2(560, 700, ang=8, s=2.6, skin="#e2dce6", curl=(.1, .05, .05, .15), spread=1.4, thumb=.4, side=-1, cracks_col="#a673ff")
    g += cracks(240, 520, 5, 90, "#a673ff", seed=41) + cracks(570, 520, 5, 90, "#a673ff", seed=42)
    P_.append(pnl(h, g, [cap(4, 6, 40, "...These aren't my hands.")]))
    # P47 ----------------------------------------------------------------------------------------
    h = 660
    g = vgrad(W, h, [(0, "#100a1a"), (1, "#07050b")]) + silt_ground(W, h, h * .7, seed=9)
    g += iron_tag(270, 300, .95, rot=-6)
    g += bottle_lantern(600, h * .8, 1.6, rot=74)
    P_.append(pnl(h, g))
    # P48 ----------------------------------------------------------------------------------------
    h = 1220
    g = drowned_ruins(W, h, horizon=.6, seed=3)
    g += P(f"M 0,{h * .9} Q 300,{h * .84} 520,{h * .88} T {W},{h * .86} L {W},{h} L 0,{h} Z", "#06040a")
    g += G(human_silhouette(70, "#06040a"), 240, h * .875)
    g += vignette(W, h, .6)
    P_.append(pnl(h, g, [cap(4, 4, 30, "Not my hands."), cap(66, 92, 30, "Not my sky.")], cls="big"))
    # P49 ----------------------------------------------------------------------------------------
    h = 640
    g = vgrad(W, h, [(0, "#1a0e2c"), (1, "#0b0618")]) + mist(-100, 50, W + 200, 600, n=9, color="#9a6ac0", op=.45, seed=12)
    g += hd("wren_tunic", 430, 300, 1.75, dict(look=(-5, 0), cracks=True, mouth="flat"), VIOL, rot=-4)
    for k in range(5):
        g += P(f"M {-20 + k * 30},{180 + k * 70} C 140,{140 + k * 70} 200,{260 + k * 60} 340,{200 + k * 60}", stroke="#c9a5ff", sw=3, op=.35, flt="blur2")
    g += T(80, 120, "hsss...", 36, "#c9a5ff", font="Patrick Hand", rot=-8) + T(560, 600, "hsss...", 32, "#c9a5ff", font="Patrick Hand", rot=6) + T(90, 560, "hsss...", 28, "#c9a5ff", font="Patrick Hand")
    P_.append(pnl(h, g, [cap(62, 6, 34, "Something's whispering.")]))
    # P50 ----------------------------------------------------------------------------------------
    h = 760
    g = vgrad(W, h, [(0, "#120a20"), (1, "#05030a")]) + silt_ground(W, h, h * .78, seed=13)
    g += mist(-100, 200, W + 200, 500, n=9, color="#7a5ab0", op=.5, seed=14)
    g += G(murmur(1.0, facing=-1), 440, h * .8, 2.0)
    g += mist(-100, h * .6, W + 200, 300, n=6, color="#5a3a8a", op=.5, seed=15)
    P_.append(pnl(h, g, [dict(t="monster", x=4, y=6, w=46, text="...where... where did I... where...")]))
    # P51 ----------------------------------------------------------------------------------------
    h = 620
    g = R(0, 0, W, h, "#07050c") + rglow(400, 300, 360, "#5a3a8a", .3)
    g += hd("wren_tunic", 400, 270, 2.3, dict(cracks=True, mouth="flat", hl=False), VIOL)
    P_.append(pnl(h, g, [cap(4, 6, 24, "Don't move."), cap(4, 18, 24, "Don't feel."), cap(66, 84, 30, "You're good at this.")]))
    # P52 ----------------------------------------------------------------------------------------
    h = 660
    g = R(0, 0, W, h, "#07050c") + rglow(500, 330, 380, "#5a3a8a", .35)
    g += hd("wren_tunic", 560, 290, 2.4, dict(cracks=True, mouth="flat", hl=False, look=(-3, 0)), VIOL)
    g += G(murmur_skull(), 18, 560, 2.15, sx=-2.15)
    g += P("M -40,560 C 40,420 120,330 170,300 L 300,330 C 200,360 120,470 60,700 L -40,700 Z", "#120c1a", stroke=LINE, sw=2)
    g += mist(-100, 300, 560, 360, n=5, color="#7a5ab0", op=.35, seed=16)
    g += T(300, 470, "snf...", 40, "#c9a5ff", font="Patrick Hand", rot=-6) + T(120, 250, "snf...", 34, "#c9a5ff", font="Patrick Hand", rot=4)
    P_.append(pnl(h, g))
    # P53 ----------------------------------------------------------------------------------------
    h = 600
    g = vgrad(W, h, [(0, "#120a20"), (1, "#05030a")]) + silt_ground(W, h, h * .7, seed=17)
    g += G(murmur(1.0, facing=1), 560, h * .72, 1.1, op=.75)
    g += mist(300, 100, 600, 500, n=8, color="#7a5ab0", op=.6, seed=18)
    g += G(back_head("wren_tunic"), 170, 560, 1.15)
    P_.append(pnl(h, g, [cap(4, 6, 38, "It isn't looking with eyes.")]))
    # P54 ----------------------------------------------------------------------------------------
    h = 540
    g = vgrad(W, h, [(0, "#120a20"), (1, "#05030a")]) + mist(-100, 0, W + 200, h, n=12, color="#7a5ab0", op=.7, seed=19)
    g += sfx(360, 220, "SKREEEE—", 96, "#e8e0f4", rot=-6, stroke="#2a1a40", sw=8) + sfx(520, 420, "KRNCH.", 110, "#c9a5ff", rot=6, stroke="#05030a", sw=9, glow="glow")
    P_.append(pnl(h, g))
    # P55 ----------------------------------------------------------------------------------------
    h = 580
    g = vgrad(W, h, [(0, "#0b0618"), (1, "#07050b")]) + silt_ground(W, h, h * .62, seed=20)
    g += tube([(-60, 300, 130), (200, 290, 120), (440, 300, 100), (560, 420, 86), (640, 600, 76)], "#ddd5e2", "#7a6a8a", cap=False)
    rnd = random.Random(55)
    for _ in range(14):
        x, y = rnd.uniform(200, 620), rnd.uniform(260, 560)
        g += E(x, y, rnd.uniform(8, 22), rnd.uniform(4, 10), "#2a2030", op=.55)
    g += cracks(470, 340, 5, 60, "#a673ff", seed=8)
    rnd2 = random.Random(5)
    hem = "M -60,220 L 260,232 " + " ".join(f"L {260 - k * 30},{300 + rnd2.uniform(20, 70):.0f}" for k in range(11)) + " Z"
    g += P(hem, "#6c6a68", stroke=LINE, sw=2) + P("M -60,240 L 250,250", stroke="#3e3c3b", sw=2)
    g += knot(470, 470, 34, seed=12)
    g += P("M 420,490 l -60,10 M 424,508 l -70,22", stroke="#c9a5ff", sw=3, op=.6)
    g += T(150, 470, "tik...", 34, "#c9a5ff", font="Patrick Hand", rot=-8) + T(240, 530, "tik...", 30, "#c9a5ff", font="Patrick Hand", rot=-8) + T(520, 430, "tk.", 40, "#e8e0f4", font="Patrick Hand")
    P_.append(pnl(h, g))
    # P56 ----------------------------------------------------------------------------------------
    h = 680
    g = R(0, 0, W, h, "#07050c") + rglow(400, 560, 360, "#8a5cff", .35)
    g += hd("wren_tunic", 400, 250, 2.0, dict(cracks=True, eyes="half", look=(0, 4), mouth="flat"), dict(VIOL, rim="#c9a5ff"), rot=8)
    g += knot(400, 600, 40, seed=5)
    g += T(600, 470, "grrrrrrr", 40, "#e8e0f4", font="Patrick Hand", rot=-6) + T(610, 500, "(stomach)", 20, "#a89ac0", font="Patrick Hand", rot=-6)
    P_.append(pnl(h, g, [cap(4, 4, 40, "I should not eat the glowing monster rock."), cap(4, 84, 30, "I am so hungry.")]))
    # P57 ----------------------------------------------------------------------------------------
    h = 500
    g = R(0, 0, W, h, "#07050c")
    mid = uid("cr")
    g += f'<defs>{clip(mid, f"M 0,0 h {W} v {h} h {-W} Z")}</defs><g clip-path="url(#{mid})">' + hd("wren_tunic", 400, -110, 4.6, dict(cracks=True, mouth="flat"), VIOL) + "</g>"
    g += E(400, 420, 40, 26, "#b48cff", op=.6, flt="blur6") + C(400, 420, 12, "#efe4ff", flt="glow")
    g += sfx(620, 200, "GLK.", 96, "#e8e0f4", rot=8, stroke="#05030a", sw=8)
    P_.append(pnl(h, g))
    # P58 ----------------------------------------------------------------------------------------
    h = 540
    g = G(drawer_scene(W, h), 0, 0) + R(0, 0, W, h, "#7a4aa8", op=.25)
    g = f'<g filter="url(#blur2)">{g}</g>' + vignette(W, h, .9)
    P_.append(pnl(h, g, [dict(t="whisper", x=48, y=8, w=46, text="...where did I put it...")], cls="memory"))
    # P59 ----------------------------------------------------------------------------------------
    h = 940
    g = R(0, 0, W, h, "#06040c") + rglow(400, 420, 480, "#8a5cff", .55) + rglow(400, 400, 300, "#ffcf6a", .25)
    g += speed_lines(400, 420, W, h, n=70, r0=330, color="#c9a5ff", op=.3, seed=21)
    wg, wh = drip_window(90, 220, 620, ["Knot absorbed: 1", "Skill acquired: GNAW", "Passive: SILT MEND", "Form: SILT WRETCH (Stage 0) · Lv 1", "UNDERTOW  ▮▯▯▯▯▯▯▯▯▯  3%"], size=31, title="[ UNDERTALLY ]  ⟨hidden layer opened⟩")
    g += wg
    for i, (nx, ny, ns) in enumerate(((70, 120, 1.1), (180, 70, .8), (640, 80, 1.0), (730, 170, .8), (60, 640, .9), (720, 600, 1.1), (130, 820, .8), (650, 830, .9), (300, 760, .7), (520, 740, .8))):
        g += note_glyph(nx, ny, ns, "#ffd56b" if i % 3 else "#c9a5ff")
    g += sfx(400, 140, "TING-TA-LING", 96, "#ffd56b", rot=-3, stroke="#2a1450", sw=9, glow="glow2")
    g += G(human_silhouette(160, "#05030a"), 400, 920)
    P_.append(pnl(h, g))
    # P60 ----------------------------------------------------------------------------------------
    h = 840
    g = R(0, 0, W, h, "#05030a") + rglow(400, 840, 520, "#8a5cff", .5)
    g += hd("wren_tunic", 400, 320, 3.0, dict(eyes="wide", glow="#b48cff", cracks=True, mouth="flat", brow="soft"), UNDER)
    g += particles(0, 400, W, 440, n=40, color="#ffd56b", rmax=2.6, seed=22)
    g += vignette(W, h, .7)
    P_.append(pnl(h, g, [cap(54, 88, 42, "...That's Mom's chime.", "final")]))
    return P_
