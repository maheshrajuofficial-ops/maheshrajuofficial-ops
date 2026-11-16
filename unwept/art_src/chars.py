"""Character heads, hair and bust outfits for UNWEPT. Head frame: face centre (0,0), chin ~y70, hair top ~-100."""
import math, random
from art import *

LINE = "#120c18"

# ------------------------------------------------------------------ cast configs
CAST = {
    "wren": dict(face="male", skin="#e9e3ec", hair="wren", hair_col="#1e1f28", hair_hi="#59607e", eye="sleepy",
                 eye_col="#8d93a6", brow="flat", marks=["vein"], outfit="lanternhall"),
    "wren_tunic": dict(face="male", skin="#e2dce6", hair="wren", hair_col="#1e1f28", hair_hi="#59607e", eye="sleepy",
                       eye_col="#8d93a6", brow="flat", marks=["vein"], outfit="tunic"),
    "jonah": dict(face="male", skin="#efd9c8", hair="earth", hair_col="#16161c", hair_hi="#4a4d60", eye="sleepy",
                  eye_col="#6b4a36", brow="flat", marks=["circles"], outfit="hoodie"),
    "jonah11": dict(face="child", skin="#efd9c8", hair="plastered", hair_col="#121217", hair_hi="#545a70", eye="soft",
                    eye_col="#6b4a36", brow="flat", marks=[], outfit="suit_kid"),
    "lily4": dict(face="child", skin="#f6dfcf", hair="pigtails", hair_col="#a77a52", hair_hi="#d8ad7e", eye="big",
                  eye_col="#7a5a3e", brow="worried", marks=["blush"], outfit="raincoat"),
    "lily17": dict(face="female", skin="#f3dccb", hair="lilyteen", hair_col="#a77a52", hair_hi="#d8ad7e", eye="big",
                   eye_col="#7a5a3e", brow="soft", marks=[], outfit="lilyteen"),
    "june": dict(face="young", skin="#f2d8c4", hair="june", hair_col="#c4612b", hair_hi="#f0a067", eye="big",
                 eye_col="#d08a2a", brow="soft", marks=["freckles", "blush"], outfit="work"),
    "otto": dict(face="round", skin="#f0d2bd", hair="otto", hair_col="#6e4426", hair_hi="#a8744a", eye="soft",
                 eye_col="#5e7a4a", brow="worried", marks=["blush_big"], outfit="otto", acc=["glasses"]),
    "solenne": dict(face="female", skin="#f4ecee", hair="solenne", hair_col="#e7ebf3", hair_hi="#ffffff", eye="sharpf",
                    eye_col="#8fd0ff", brow="soft", marks=["beauty"], outfit="beacon"),
    "dorian": dict(face="male", skin="#f0dccb", hair="dorian", hair_col="#e0b648", hair_hi="#fff0b0", eye="sharp",
                   eye_col="#e2a12a", brow="sharp", marks=[], outfit="lantern", acc=["earring"]),
    "iona": dict(face="strong", skin="#6e4630", hair="iona", hair_col="#8f9198", hair_hi="#c8cad0", eye="sharp",
                 eye_col="#4a3426", brow="sharp", marks=["jawscar"], outfit="vigil"),
    "severin": dict(face="gaunt", skin="#efe9e4", hair="severin", hair_col="#eeeef2", hair_hi="#ffffff", eye="narrow",
                    eye_col="#d0d6dd", brow="flat", marks=["gaunt"], outfit="concord", acc=["circlet"]),
    "miriam": dict(face="female", skin="#f0d6c2", hair="miriam", hair_col="#3b2a21", hair_hi="#7b5a44", eye="soft",
                   eye_col="#7a5236", brow="soft", marks=["ink"], outfit="cardigan"),
    "maren": dict(face="female", skin="#eed2bc", hair="maren", hair_col="#5a3a2a", hair_hi="#8a6048", eye="soft",
                  eye_col="#6a4a36", brow="soft", marks=["blush"], outfit="maren"),
}

FACES = {
    "male": "M -46,-14 L -45,18 Q -42,34 -30,48 L -9,67 Q 0,73 9,67 L 30,48 Q 42,34 45,18 L 46,-14 C 46,-66 -46,-66 -46,-14 Z",
    "strong": "M -47,-14 L -46,22 Q -44,38 -32,50 L -11,67 Q 0,72 11,67 L 32,50 Q 44,38 46,22 L 47,-14 C 47,-66 -47,-66 -47,-14 Z",
    "female": "M -44,-14 L -43,16 Q -40,34 -26,50 L -9,64 Q 0,69 9,64 L 26,50 Q 40,34 43,16 L 44,-14 C 44,-64 -44,-64 -44,-14 Z",
    "young": "M -44,-14 C -45,20 -38,42 -22,56 Q -8,66 0,66 Q 8,66 22,56 C 38,42 45,20 44,-14 C 44,-64 -44,-64 -44,-14 Z",
    "child": "M -47,-14 C -49,26 -38,50 -18,60 Q 0,67 18,60 C 38,50 49,26 47,-14 C 47,-66 -47,-66 -47,-14 Z",
    "round": "M -50,-14 C -52,26 -42,52 -20,63 Q 0,70 20,63 C 42,52 52,26 50,-14 C 50,-66 -50,-66 -50,-14 Z",
    "gaunt": "M -42,-14 L -42,22 Q -40,42 -27,57 L -9,74 Q 0,79 9,74 L 27,57 Q 40,42 42,22 L 42,-14 C 42,-64 -42,-64 -42,-14 Z",
}
# eye geometry: inner-corner x, eye y, width, upper height, lower height, slant, iris r
EYES = {
    "sleepy": dict(ix=8, ey=4, w=27, hu=8.5, hl=5.5, slant=1.5, r=8.6, cy=2.2, lash=3.2),
    "sharp": dict(ix=8, ey=4, w=27, hu=10, hl=5, slant=4.5, r=8.4, cy=0.8, lash=3.4),
    "narrow": dict(ix=8, ey=4, w=26, hu=6.5, hl=4, slant=2.5, r=7.5, cy=1.0, lash=2.8),
    "soft": dict(ix=7, ey=6, w=27, hu=12, hl=8, slant=0.5, r=10, cy=0.5, lash=3.2),
    "sharpf": dict(ix=7, ey=5, w=28, hu=12.5, hl=7, slant=4, r=9.8, cy=0.6, lash=3.8),
    "big": dict(ix=6, ey=8, w=27, hu=15, hl=10, slant=0.5, r=11.5, cy=0.5, lash=3.6),
}


from hair import *

# ------------------------------------------------------------------ eyes

def one_eye(g, side, col, mode="normal", look=(0, 0), glow=None, sclera="#f6f3f7", skin_sh="#c8a0a0", hl=True):
    """Draw eye for viewer-right side in local coords; mirrored for side=-1. Returns svg."""
    w, hu, hlo, sl, r, cy = g["w"], g["hu"], g["hl"], g["slant"], g["r"], g["cy"]
    if mode == "wide":
        hu *= 1.32; hlo *= 1.25; r *= 0.86
    if mode == "pin":
        hu *= 1.25; hlo *= 1.15
    if mode == "half":
        hu *= 0.55; cy += 2.5
    up = f"M 0,0 C {w * .22:.1f},{-hu:.1f} {w * .68:.1f},{-hu * 1.06 - sl:.1f} {w:.1f},{-sl:.1f}"
    shape = up + f" C {w * .78:.1f},{hlo - sl * .4:.1f} {w * .32:.1f},{hlo:.1f} 0,0 Z"
    out = []
    if mode == "closed":
        out.append(P(f"M 0,0 C {w * .3:.1f},{hlo * .9:.1f} {w * .7:.1f},{hlo * .8 - sl:.1f} {w + 2:.1f},{-sl - 1:.1f}", stroke=LINE, sw=g["lash"]))
        out.append(P(f"M {w * .5:.1f},{hlo * .9 + 2:.1f} l 1,4 M {w * .75:.1f},{hlo * .6:.1f} l 2,4", stroke=LINE, sw=1.2))
    else:
        cid = uid("ec")
        out.append(f"<defs>{clip(cid, shape)}</defs>")
        out.append(P(shape, sclera))
        ix, iy = w * 0.47 + look[0] * side, cy + look[1]
        inner = []
        inner.append(P(f"M -2,-2 C {w * .22},{-hu - 2} {w * .7},{-hu - 2 - sl} {w + 2},{-sl - 2} L {w + 2},{-sl + 3} C {w * .6},{-hu * .3} {w * .3},{-hu * .3} -2,4 Z", skin_sh, op=.55))
        if mode == "pin":
            inner.append(C(ix, iy, r * 0.42, dark(col, .2)))
            inner.append(C(ix, iy, 1.4, "#000"))
        else:
            gid = uid("ir")
            out.append(f"<defs>{rad(gid, [(0, light(col, .35), 1), (0.6, col, 1), (1, dark(col, .55), 1)], cx=.5, cy=.68, r=.6)}</defs>")
            if glow:
                inner.append(C(ix, iy, r * 1.25, glow, op=.5, flt="blur2"))
            inner.append(C(ix, iy, r, f"url(#{gid})", stroke=dark(col, .65), sw=1.2))
            inner.append(C(ix, iy, r * 0.42, dark(col, .8) if mode != "dead" else dark(col, .6)))
            inner.append(P(f"M {ix - r},{iy - r * .2} A {r},{r} 0 0 1 {ix + r},{iy - r * .2} L {ix + r},{iy - r - 2} L {ix - r},{iy - r - 2} Z", "#000", op=.35))
            if glow:
                inner.append(C(ix + r * .25 * side, iy + r * .45, r * .32, glow, op=.95, flt="glow"))
            if hl and mode != "dead":
                inner.append(E(ix - r * .38 * side, iy - r * .38, r * .27, r * .22, "#ffffff", op=.95))
                inner.append(C(ix + r * .35 * side, iy + r * .38, r * .1, "#ffffff", op=.8))
        out.append(f'<g clip-path="url(#{cid})">{"".join(inner)}</g>')
        lt = g["lash"]
        lash = (f"M -1,1 C {w * .22:.1f},{-hu:.1f} {w * .68:.1f},{-hu * 1.06 - sl:.1f} {w:.1f},{-sl:.1f} "
                f"L {w + 5:.1f},{-sl - 3.5:.1f} C {w * .7:.1f},{-hu * 1.06 - sl - lt:.1f} {w * .2:.1f},{-hu - lt * .6:.1f} -2,-1.5 Z")
        out.append(P(lash, LINE))
        out.append(P(f"M {w * .45:.1f},{hlo * .95:.1f} C {w * .7:.1f},{hlo * .8:.1f} {w * .9:.1f},{hlo * .5 - sl * .6:.1f} {w + 1:.1f},{-sl + 1:.1f}", stroke=dark(skin_sh, .3), sw=1.3))
        out.append(P(f"M {w * .18:.1f},{-hu - 3.5:.1f} C {w * .45:.1f},{-hu - 6.5 - sl * .5:.1f} {w * .75:.1f},{-hu - 6 - sl:.1f} {w * .98:.1f},{-sl - 4.5:.1f}", stroke=dark(skin_sh, .25), sw=1.1, op=.8))
    tr = f'translate({g["ix"] * side},{g["ey"]}) scale({side},1)'
    return f'<g transform="{tr}">{"".join(out)}</g>'


def brow(g, side, kind, col):
    w, hu, sl = g["w"], g["hu"], g["slant"]
    bi, bo, th = {"flat": (0, 0, 4.2), "sharp": (3, -3, 4.6), "worried": (-6, 3, 3.6), "angry": (7, -5, 5),
                  "soft": (-1, 0, 3.2), "up": (-8, -6, 4)}[kind]
    y0 = -hu - 9 + bi
    y1 = -hu - 12 - sl + bo
    d = (f"M -2,{y0:.1f} Q {w * .5:.1f},{(y0 + y1) / 2 - 4:.1f} {w + 5:.1f},{y1:.1f} "
         f"Q {w * .5:.1f},{(y0 + y1) / 2 - 4 + th * .9:.1f} -1,{y0 + th:.1f} Z")
    tr = f'translate({g["ix"] * side},{g["ey"]}) scale({side},1)'
    return f'<g transform="{tr}">{P(d, col, stroke=LINE, sw=0.8)}</g>'

# ------------------------------------------------------------------ outfits (bust)

def shoulders(k=1.0):
    return (f"M -24,92 C {-60 * k},{98} {-118 * k},{108} {-150 * k},{140} L {-172 * k},270 L {172 * k},270 "
            f"L {150 * k},140 C {118 * k},108 {60 * k},98 24,92 Z")


def null_patch(x, y, s=1):
    return G(C(0, 0, 17, "#5d606a", stroke=LINE, sw=1.4) + C(0, 0, 13, "none", stroke="#8a8e99", sw=1.2) +
             P("M -5,-8 L 5,-8 L 6,6 L -6,6 Z", "#3a3c44", stroke="#9a9ea8", sw=1.2) + P("M -3,-11 Q 0,-15 3,-11", stroke="#9a9ea8", sw=1.4), x, y, s)


def outfit(name, skin, shade, light_rim=None):
    sh = shoulders
    out = []
    if name == "lanternhall":
        coat, cd = "#1e2538", "#121726"
        out.append(P(sh(1.0), coat, stroke=LINE, sw=2))
        out.append(P("M 30,96 C 70,104 120,114 150,140 L 172,270 L 60,270 Z", cd, op=.8))
        out.append(P("M -2,128 L -2,270 M 2,128 L 2,270", stroke="#0b0f1a", sw=2))
        out.append(P("M -30,60 L -34,118 Q 0,136 34,118 L 30,60 Q 0,72 -30,60 Z", coat, stroke=LINE, sw=2))
        out.append(P("M 0,72 L 0,132", stroke="#0b0f1a", sw=2) + P("M -30,64 Q 0,76 30,64", stroke="#3a4462", sw=2))
        for y in (148, 190, 232):
            out.append(C(-12, y, 5, "#c8963c", stroke="#5b3d10", sw=1.2) + C(-13.5, y - 1.5, 1.6, "#ffe4a0"))
        out.append(P("M -150,140 C -110,116 -60,104 -28,100", stroke="#3a4462", sw=2.4, op=.8))
        out.append(null_patch(108, 150))
    elif name == "hoodie":
        c, cd = "#7c7f88", "#5a5c64"
        out.append(P(sh(1.0), c, stroke=LINE, sw=2))
        out.append(P("M 30,96 C 70,104 120,114 150,140 L 172,270 L 60,270 Z", cd, op=.8))
        out.append(P("M -70,96 C -62,70 -30,70 -24,92 Q 0,112 24,92 C 30,70 62,70 70,96 C 60,130 -60,130 -70,96 Z", "#8a8d96", stroke=LINE, sw=2))
        out.append(P("M -14,116 L -16,178 M 14,116 L 16,182", stroke="#d8d8dc", sw=3))
        # headset around neck
        out.append(P("M -52,86 C -48,130 48,130 52,86", stroke="#121216", sw=9))
        out.append(E(-56, 104, 20, 24, "#18181d", stroke=LINE, sw=1.5, rot=-14) + E(-56, 104, 12, 15, "#2a2a33", rot=-14))
        out.append(E(56, 104, 20, 24, "#18181d", stroke=LINE, sw=1.5, rot=14) + E(56, 104, 12, 15, "#2a2a33", rot=14))
        out.append(P("M -66,92 Q -60,84 -50,88", stroke="#6fb8ff", sw=2, op=.7))
    elif name == "suit_kid":
        out.append(P(sh(0.86), "#16161c", stroke=LINE, sw=2))
        out.append(P("M -22,92 L 0,170 L 22,92 Z", "#e8e8ee", stroke=LINE, sw=1.5))
        out.append(P("M -5,104 L 5,104 L 7,160 L 0,172 L -7,160 Z", "#0b0b0e"))
        out.append(P("M -22,92 L -40,104 L 0,200 Z M 22,92 L 40,104 L 0,200 Z", "#202028", stroke=LINE, sw=1.5))
        out.append(P("M -150,150 L -120,270 M 140,150 L 120,270", stroke="#2e2e38", sw=2))
    elif name == "tunic":
        c = "#6c6a68"
        out.append(P(sh(0.96), c, stroke=LINE, sw=2))
        out.append(P("M 30,96 C 70,104 120,114 145,140 L 168,270 L 60,270 Z", dark(c, .3), op=.8))
        out.append(P("M -34,94 Q 0,140 34,94 L 26,92 Q 0,124 -26,92 Z", "#4d4b4a", stroke=LINE, sw=1.5))
        rnd = random.Random(3)
        for _ in range(9):
            x, y = rnd.uniform(-130, 130), rnd.uniform(140, 250)
            out.append(P(f"M {x:.0f},{y:.0f} l {rnd.uniform(6, 18):.0f},{rnd.uniform(-4, 4):.0f}", stroke="#3e3c3b", sw=1.5))
        out.append(P("M -24,94 C -20,130 -8,150 0,160 C 8,150 20,130 24,94", stroke="#2a2420", sw=2))
        out.append(R(-12, 156, 24, 32, "#55565c", rx=3, stroke=LINE, sw=1.5) + C(0, 161, 2.2, "#222"))
        out.append(P("M -7,170 L 7,170 M -7,176 L 5,176 M -7,182 L 7,182", stroke="#8a8c94", sw=1.4))
    elif name == "raincoat":
        c = "#f2c230"
        out.append(P(sh(0.7), c, stroke=LINE, sw=2))
        out.append(P("M 22,96 C 50,102 84,112 104,140 L 120,270 L 40,270 Z", "#c9961c", op=.8))
        out.append(P("M -60,96 C -40,74 -20,80 -20,92 Q 0,104 20,92 C 20,80 40,74 60,96 C 40,118 -40,118 -60,96 Z", "#e6b222", stroke=LINE, sw=2))
        out.append(P("M 0,108 L 0,270", stroke="#9a7212", sw=2) + C(-8, 150, 4, "#fff4c0", stroke=LINE, sw=1) + C(-8, 196, 4, "#fff4c0", stroke=LINE, sw=1))
        out.append(P("M -96,150 Q -80,140 -70,148", stroke="#fff6c8", sw=3, op=.8))
    elif name == "work":
        c = "#5e6a3a"
        out.append(P(sh(0.84), c, stroke=LINE, sw=2))
        out.append(P("M 26,96 C 60,104 100,114 126,140 L 146,270 L 50,270 Z", dark(c, .3), op=.8))
        out.append(P("M -24,92 L -10,190 L 10,190 L 24,92 Q 0,104 -24,92 Z", "#2c3a40", stroke=LINE, sw=1.5))
        out.append(P("M -24,92 L -54,98 L -20,196 L -8,190 Z M 24,92 L 54,98 L 20,196 L 8,190 Z", "#6e7a46", stroke=LINE, sw=1.6))
        out.append(P("M -110,170 Q -90,160 -70,176 M 80,190 Q 100,182 118,196", stroke="#2a2a1a", sw=3, op=.6))
        out.append(E(-90, 200, 16, 8, "#2a2a1a", op=.35))
    elif name == "otto":
        coat = "#1e2538"
        out.append(P(sh(1.08), coat, stroke=LINE, sw=2))
        out.append(P("M 30,96 C 70,104 126,114 160,140 L 184,270 L 60,270 Z", "#121726", op=.8))
        out.append(P("M -26,92 L -6,170 L 6,170 L 26,92 Q 0,106 -26,92 Z", "#e9e2d2", stroke=LINE, sw=1.5))
        out.append(P("M -26,92 L -58,98 L -40,150 L -8,176 Z M 26,92 L 58,98 L 40,150 L 8,176 Z", "#27304a", stroke=LINE, sw=1.6))
        out.append(P("M -120,116 L 120,270", stroke="#7a4e2a", sw=14) + P("M -120,116 L 120,270", stroke="#5a3418", sw=2))
        out.append(C(-70, 150, 12, "#111", stroke="#ddd", sw=1.5) + P("M -70,141 L -70,156", stroke="#fff", sw=3) + P("M -76,146 Q -70,138 -64,146", stroke="#fff", sw=1.6))
    elif name == "beacon":
        c = "#f3f1ec"
        out.append(P(sh(0.86), c, stroke=LINE, sw=2))
        out.append(P("M 26,96 C 60,104 100,114 128,140 L 148,270 L 50,270 Z", "#cfd3dc", op=.8))
        out.append(P("M -28,62 L -32,114 Q 0,130 32,114 L 28,62 Q 0,74 -28,62 Z", c, stroke=LINE, sw=1.8))
        out.append(P("M -28,66 Q 0,78 28,66", stroke="#d4a640", sw=2.4))
        out.append(P("M 0,120 L 0,270", stroke="#d4a640", sw=3) + P("M -10,120 L -10,270 M 10,120 L 10,270", stroke="#e9e3d4", sw=1.4))
        # short white shoulder cape
        out.append(P("M -150,134 C -120,104 -60,96 -30,104 L -40,150 C -80,160 -120,180 -142,220 Z", "#ffffff", stroke=LINE, sw=1.8))
        out.append(P("M 150,134 C 120,104 60,96 30,104 L 40,150 C 80,160 120,180 142,220 Z", "#e8eaf0", stroke=LINE, sw=1.8))
        out.append(P("M -142,220 C -120,180 -80,160 -40,150 M 142,220 C 120,180 80,160 40,150", stroke="#d4a640", sw=3))
        out.append(C(-36, 128, 7, "#e6b84a", stroke="#7a5a10", sw=1.4) + C(36, 128, 7, "#e6b84a", stroke="#7a5a10", sw=1.4))
    elif name == "lantern":
        c = "#16121a"
        out.append(P(sh(1.04), c, stroke=LINE, sw=2))
        out.append(P("M -26,64 L -30,116 Q 0,130 30,116 L 26,64 Q 0,76 -26,64 Z", c, stroke=LINE, sw=1.8))
        out.append(P("M -26,68 Q 0,80 26,68", stroke="#c73a3a", sw=2.6))
        out.append(P("M -8,120 L -8,270 M 8,120 L 8,270", stroke="#a82c2c", sw=3))
        out.append(P("M -20,136 L 20,136 M -20,176 L 20,176 M -20,216 L 20,216", stroke="#d4a640", sw=2.4))
        # fur half-cape over viewer-left shoulder
        out.append(P("M -164,150 C -150,110 -90,90 -30,100 L -40,140 C -70,150 -110,190 -130,270 L -176,270 Z", "#8a1e22", stroke=LINE, sw=1.8))
        rnd = random.Random(2)
        fur = "M -166,152 " + " ".join(f"Q {-160 + i * 13 + rnd.uniform(-3, 3):.0f},{118 - i * 4 + rnd.uniform(-8, 0):.0f} {-152 + i * 13:.0f},{124 - i * 4:.0f}" for i in range(10)) + " L -40,112 L -30,100 C -90,90 -150,110 -166,152 Z"
        out.append(P(fur, "#d9cdb8", stroke=LINE, sw=1.4))
        # greatsword hilt over viewer-right shoulder
        out.append(P("M 96,40 L 132,130", stroke="#3a2a20", sw=10) + P("M 78,64 L 120,44", stroke="#c8962c", sw=8) + C(88, 22, 8, "#c8962c", stroke=LINE, sw=1.4))
    elif name == "vigil":
        c = "#243a2c"
        out.append(P(sh(1.06), c, stroke=LINE, sw=2))
        out.append(P("M -28,66 L -32,118 Q 0,132 32,118 L 28,66 Q 0,78 -28,66 Z", c, stroke=LINE, sw=1.8))
        out.append(P("M -12,150 L -8,270 M 12,150 L 8,270", stroke="#162418", sw=2))
        out.append(G(P("M 0,-12 L 8,0 L 0,12 L -8,0 Z", "#cfd4da", stroke=LINE, sw=1.2) + C(0, 0, 3, "#6fc7ff", flt="glow"), -80, 150))
        # brass left arm/pauldron (viewer right)
        out.append(P("M 60,98 C 110,90 160,110 176,160 L 182,270 L 110,270 L 100,160 Z", "#a87a34", stroke=LINE, sw=2))
        out.append(P("M 70,104 C 110,98 150,116 164,150", stroke="#f2c878", sw=3, op=.8))
        out.append(C(146, 196, 10, "#ffd27a", flt="glow2") + C(146, 196, 6, "#fff4cc"))
        out.append(P("M 110,170 L 176,176", stroke="#6a4a1c", sw=2))
    elif name == "concord":
        c = "#f2f0ec"
        out.append(P(sh(0.92), c, stroke=LINE, sw=2))
        out.append(P("M 26,96 C 60,104 106,114 134,140 L 156,270 L 50,270 Z", "#d5d8de", op=.8))
        out.append(P("M -26,44 L -34,118 Q 0,134 34,118 L 26,44 Q 0,58 -26,44 Z", c, stroke=LINE, sw=1.8))
        out.append(P("M -26,50 Q 0,62 26,50", stroke="#d2a644", sw=2.4) + P("M 0,130 L 0,270", stroke="#d2a644", sw=4))
        for x, y in [(-90, 170), (90, 170), (-60, 230), (60, 230)]:
            out.append(G(C(0, 0, 11, "none", stroke="#d2a644", sw=1.6) + P("M -6,0 L 6,0 M 0,-6 L 0,6", stroke="#d2a644", sw=1.4), x, y))
    elif name == "cardigan":
        c = "#d9ccb2"
        out.append(P(sh(0.86), c, stroke=LINE, sw=2))
        out.append(P("M 26,96 C 60,104 100,114 128,140 L 148,270 L 50,270 Z", "#b8a888", op=.8))
        out.append(P("M -24,92 L -4,190 L 4,190 L 24,92 Q 0,108 -24,92 Z", "#f1ede4", stroke=LINE, sw=1.5))
        out.append(P("M -24,92 L -52,100 L -16,270 L -6,270 Z M 24,92 L 52,100 L 16,270 L 6,270 Z", "#cdbf9f", stroke=LINE, sw=1.5))
        rnd = random.Random(5)
        for _ in range(26):
            x, y = rnd.uniform(-140, 140), rnd.uniform(130, 260)
            out.append(P(f"M {x:.0f},{y:.0f} l 2,4 l 2,-4", stroke="#b5a585", sw=1.1))
    elif name == "maren":
        c = "#e9dcc6"
        out.append(P(sh(0.86), c, stroke=LINE, sw=2))
        out.append(P("M -70,96 C -40,80 40,80 70,96 C 64,126 30,138 0,138 C -30,138 -64,126 -70,96 Z", "#c42a2a", stroke=LINE, sw=2))
        out.append(P("M 20,130 L 40,220 L 56,210 L 34,128 Z", "#a82020", stroke=LINE, sw=1.6))
        out.append(P("M -60,104 Q 0,124 60,104", stroke="#e85050", sw=2, op=.8))
    elif name == "lilyteen":
        c = "#3b4a66"
        out.append(P(sh(0.84), c, stroke=LINE, sw=2))
        out.append(P("M -24,92 Q 0,112 24,92 L 26,104 Q 0,124 -26,104 Z", "#d9d0c4", stroke=LINE, sw=1.5))
    return "".join(out)

# ------------------------------------------------------------------ head

def head(key, expr=None, lit=None, body=True, cfg_over=None, part="all"):
    cfg = dict(CAST[key])
    if cfg_over:
        cfg.update(cfg_over)
    ex = dict(eyes="normal", mouth="flat", look=(0, 0), sweat=False, tears=False, wet=False, cracks=False,
              glow=None, blush=False, brow=None, sludge=False, hl=True)
    if expr:
        ex.update(expr)
    lt = dict(rim="#9a7bff", rim_side=1, shade="#4a2e6e", amb=None, amb_t=0.0, rim_w=3.0, key="#fff4e8")
    if lit:
        lt.update(lit)
    skin = cfg["skin"]
    if lt["amb"]:
        skin = mix(skin, lt["amb"], lt["amb_t"])
    skin_sh = mix(skin, lt["shade"], 0.38)
    skin_sh2 = mix(skin, lt["shade"], 0.6)
    face = FACES[cfg["face"]]
    eg = dict(EYES[cfg["eye"]])
    if cfg["face"] == "child":
        eg["ey"] += 8
    hair_col = cfg["hair_col"]
    hair_hi = cfg["hair_hi"]
    if lt["amb"]:
        hair_col = mix(hair_col, lt["amb"], lt["amb_t"] * 0.6)
        hair_hi = mix(hair_hi, lt["amb"], lt["amb_t"] * 0.4)
    if ex["wet"]:
        hair_col = dark(hair_col, .25)
    back, front, spec = hair_style(cfg["hair"], hair_col, hair_hi, ex)
    fid = uid("fc")
    if part == "front":
        back = ""
    out = [f"<defs>{clip(fid, face)}</defs>", back]
    if lt["rim"] and cfg["hair"] in STYLES and part != "front":
        rid2 = uid("rh")
        rx = 20 if lt["rim_side"] > 0 else -200
        out.append(f'<defs><clipPath id="{rid2}"><rect x="{rx}" y="-130" width="180" height="170"/></clipPath></defs>')
        out.append(f'<g clip-path="url(#{rid2})" filter="url(#glow)" opacity=".8">' + P(STYLES[cfg["hair"]]["back"], "none", stroke=lt["rim"], sw=2.6) + "</g>")
    if part == "back":
        return "".join(out)
    if body:
        nk = 19 if cfg["face"] not in ("female", "young", "child") else 16
        out.append(P(f"M {-nk},30 L {-nk - 3},118 L {nk + 3},118 L {nk},30 Z", skin, stroke=LINE, sw=1.8))
        out.append(P(f"M {-nk - 3},50 Q 0,98 {nk + 3},50 L {nk + 3},88 Q 0,106 {-nk - 3},88 Z", skin_sh2 if cfg["face"] in ("male", "strong", "gaunt") else skin_sh, op=.85))
        out.append(P(f"M 6,60 L {nk + 3},60 L {nk + 3},118 L 10,118 Z", skin_sh, op=.8))
        if "vein" in cfg["marks"]:
            out.append(P("M -40,24 C -34,46 -28,58 -22,72 C -18,84 -20,96 -14,112", stroke="#141018", sw=2.4))
            out.append(P("M -28,58 l -6,8 M -20,88 l 6,6 M -24,74 l -5,4", stroke="#141018", sw=1.3))
            out.append(P("M -40,24 C -34,46 -28,58 -22,72 C -20,84 -20,96 -14,112", stroke="#9a6bff", sw=1, op=.55, flt="glow"))
        out.append(outfit(cfg["outfit"], skin, skin_sh))
        oid = uid("og")
        out.append(f"<defs>{lin(oid, [(0, '#000', 0), (1, '#000', .55)])}</defs>" + P(shoulders(1.1), f"url(#{oid})"))
    for s in (-1, 1):
        ex_x = 44 if cfg["face"] != "round" else 48
        out.append(G(P("M 0,-8 C 12,-14 15,12 2,22 Z", skin if s < 0 else skin_sh, stroke=LINE, sw=1.6) + P("M 3,-2 C 8,0 8,10 3,14", stroke=skin_sh2, sw=1.4), ex_x * s, 0, sx=s, s=1))
    if "earring" in cfg.get("acc", []):
        out.append(C(52, 26, 6, "none", stroke="#e8b83a", sw=2.4) + C(50, 30, 1.5, "#fff6c0"))
    out.append(P(face, skin, stroke=LINE, sw=2.2))
    kid = uid("kl")
    inner = [f"<defs>{rad(kid, [(0, lt['key'], .45), (1, lt['key'], 0)], cx=.3, cy=.25, r=.6)}</defs>",
             R(-60, -80, 120, 160, f"url(#{kid})")]
    sh_d = "M 22,-80 Q 38,-36 33,-6 Q 29,14 24,22 Q 30,32 33,40 L 26,50 Q 20,56 22,62 L 8,72 L 80,90 L 80,-80 Z"
    inner.append(P(sh_d, skin_sh))
    inner.append(P("M -8,64 Q 0,68 8,64 L 6,72 L -6,72 Z", skin_sh, op=.7))
    if spec:
        inner.append(forehead_shadow(spec, skin_sh2 if cfg["face"] != "child" else skin_sh))
    else:
        inner.append(P("M -60,-40 L 60,-40 L 60,-14 Q 0,-34 -60,-14 Z", skin_sh, op=.6))
    if "circles" in cfg["marks"]:
        for s in (-1, 1):
            inner.append(G(P(f"M 2,{eg['hl'] + 3} Q {eg['w'] * .5},{eg['hl'] + 10} {eg['w'] + 2},{eg['hl'] - 1}", stroke=mix(skin_sh2, '#4a3a6a', .3), sw=3.4, op=.55), eg["ix"] * s, eg["ey"], sx=s, s=1))
    if "gaunt" in cfg["marks"]:
        inner.append(P("M -34,20 Q -28,36 -20,44 M 34,20 Q 28,36 20,44", stroke=skin_sh2, sw=2, op=.7))
        inner.append(P("M -10,52 Q -16,60 -12,66 M 10,52 Q 16,60 12,66", stroke=skin_sh2, sw=1.4, op=.6))
    if "blush" in cfg["marks"] or ex["blush"]:
        inner.append(E(-28, eg["ey"] + 20, 12, 6, "#ff7a8a", op=.35, flt="blur2") + E(28, eg["ey"] + 20, 12, 6, "#ff7a8a", op=.35, flt="blur2"))
        inner.append(P(f"M -34,{eg['ey'] + 18} l 3,-4 M -28,{eg['ey'] + 19} l 3,-4 M 24,{eg['ey'] + 19} l 3,-4 M 30,{eg['ey'] + 18} l 3,-4", stroke="#e05a6a", sw=1.2, op=.6))
    if "blush_big" in cfg["marks"]:
        inner.append(E(-30, 30, 15, 8, "#ff6a7a", op=.45, flt="blur2") + E(30, 30, 15, 8, "#ff6a7a", op=.45, flt="blur2"))
    if "freckles" in cfg["marks"]:
        rnd = random.Random(12)
        for s in (-1, 1):
            for _ in range(7):
                inner.append(C(s * rnd.uniform(14, 34), eg["ey"] + rnd.uniform(16, 28), rnd.uniform(.9, 1.6), "#b8623a", op=.75))
    if "ink" in cfg["marks"]:
        inner.append(P("M 22,30 q 6,-2 10,2 q -4,4 -10,-2 Z", "#2a2a40", op=.6))
    if "jawscar" in cfg["marks"]:
        inner.append(P("M -40,16 Q -32,44 -12,62", stroke=dark(skin, .45), sw=3) + P("M -39,16 Q -31,44 -11,62", stroke=light(skin, .25), sw=1))
    if ex["cracks"]:
        inner.append(cracks(-20, 34, n=4, length=34, color="#a673ff", seed=21, sw=1.8))
        inner.append(cracks(30, -30, n=3, length=26, color="#a673ff", seed=4, sw=1.6))
    if ex["wet"]:
        inner.append(P("M -36,10 Q -38,30 -34,44 M 30,6 Q 33,24 30,40 M -10,44 Q -9,54 -11,60", stroke="#e8f0ff", sw=1.6, op=.7))
        inner.append("".join(C(x, y, 2, "#e8f0ff", op=.8) for x, y in [(-34, 46), (30, 42), (-12, 62), (14, 20)]))
    out.append(f'<g clip-path="url(#{fid})">{"".join(inner)}</g>')
    mode = ex["eyes"]
    for s in (-1, 1):
        out.append(one_eye(eg, s, cfg["eye_col"], mode, ex["look"], ex["glow"], skin_sh=skin_sh, hl=ex["hl"]))
    if ex.get("welling"):
        for s in (-1, 1):
            out.append(G(P(f"M 2,{eg['hl'] * .8} C {eg['w'] * .3},{eg['hl'] + 3} {eg['w'] * .7},{eg['hl'] + 2} {eg['w']},{eg['hl'] * .2 - eg['slant']}", stroke="#cfeaff", sw=2.6, op=.9)
                           + C(eg['w'] * .62, eg['hl'] * .3, 2.6, "#ffffff", op=.95) + C(eg['w'] * .35, eg['hl'] * .55, 1.8, "#ffffff", op=.9), eg["ix"] * s, eg["ey"], sx=s, s=1))
    ny = 0 if cfg["face"] != "child" else 6
    out.append(P(f"M 4,{14 + ny} Q 6,{28 + ny} 8,{35 + ny}", stroke=skin_sh2, sw=1.6))
    out.append(P(f"M -3,{39 + ny} Q 2,{42.5 + ny} 7,{38 + ny}", stroke=dark(skin_sh2, .2), sw=1.8))
    out.append(P(f"M 7,{38 + ny} L 12,{44 + ny} L 3,{44 + ny} Z", skin_sh, op=.6))
    out.append(C(-3, 36 + ny, 1.6, "#fff", op=.6))
    my = 53 if cfg["face"] not in ("child", "young") else 52
    if cfg["face"] == "gaunt":
        my = 58
    lipc = dark(skin_sh2, .45)
    mouths = {
        "flat": P(f"M -9,{my} Q 0,{my + 1.2} 9,{my}", stroke=lipc, sw=2) + P(f"M -4,{my + 5} Q 0,{my + 6} 4,{my + 5}", stroke=skin_sh2, sw=1.5),
        "frown": P(f"M -9,{my + 1.5} Q 0,{my - 2} 9,{my + 1.5}", stroke=lipc, sw=2),
        "smile": P(f"M -10,{my - 1} Q 0,{my + 6} 10,{my - 1}", stroke=lipc, sw=2),
        "smirk": P(f"M -8,{my + 1} Q 2,{my + 2} 11,{my - 3}", stroke=lipc, sw=2),
        "tiny": P(f"M -5,{my} L 5,{my}", stroke=lipc, sw=1.8),
        "open": P(f"M -8,{my - 1} Q 0,{my - 3} 8,{my - 1} Q 6,{my + 9} 0,{my + 10} Q -6,{my + 9} -8,{my - 1} Z", "#3a1820", stroke=LINE, sw=1.4) + P(f"M -4,{my + 7} Q 0,{my + 4} 4,{my + 7}", "#c0505a"),
        "cough": P(f"M -12,{my - 3} Q 0,{my - 6} 12,{my - 3} Q 9,{my + 13} 0,{my + 14} Q -9,{my + 13} -12,{my - 3} Z", "#120a10", stroke=LINE, sw=1.4),
        "o": E(0, my + 2, 4.5, 5.5, "#3a1820", stroke=LINE, sw=1.4),
        "grit": P(f"M -11,{my - 2} L 11,{my - 2} L 10,{my + 5} L -10,{my + 5} Z", "#f4f0f0", stroke=LINE, sw=1.6) + P(f"M -11,{my + 1.5} L 11,{my + 1.5}", stroke="#888", sw=1),
        "sob": P(f"M -10,{my + 2} Q 0,{my - 6} 10,{my + 2} Q 6,{my + 8} 0,{my + 8} Q -6,{my + 8} -10,{my + 2} Z", "#3a1820", stroke=LINE, sw=1.4),
    }
    out.append(mouths[ex["mouth"]])
    if ex["sludge"]:
        out.append(P(f"M 9,{my + 4} C 12,{my + 14} 8,{my + 22} 11,{my + 30} C 15,{my + 22} 15,{my + 12} 12,{my + 3} Z", "#0b070e"))
    if ex["tears"]:
        for s in (-1, 1):
            out.append(P(f"M {s * 20},{eg['ey'] + eg['hl'] + 2} Q {s * 22},{eg['ey'] + 30} {s * 19},{eg['ey'] + 48}", stroke="#bfe6ff", sw=3, op=.85))
    if "beauty" in cfg["marks"]:
        out.append(C(34, eg["ey"] + 16, 1.8, "#3a2a30"))
    if "glasses" in cfg.get("acc", []):
        for s in (-1, 1):
            out.append(C(s * 22, 6, 19, "#ffffff", op=.12) + C(s * 22, 6, 19, "none", stroke="#2a1f18", sw=3))
            out.append(P(f"M {s * 30},{-6} Q {s * 22},{-10} {s * 14},{-4}", stroke="#ffffff", sw=2.4, op=.8))
        out.append(P("M -4,2 Q 0,-2 4,2", stroke="#2a1f18", sw=3) + P("M -41,2 L -48,-2 M 41,2 L 48,-2", stroke="#2a1f18", sw=3))
    # rim light on jaw/cheek (under the hair)
    if lt["rim"]:
        rid = uid("rm")
        side = lt["rim_side"]
        rx = 14 if side > 0 else -200
        out.append(f'<defs><clipPath id="{rid}"><rect x="{rx}" y="-24" width="186" height="300"/></clipPath></defs>')
        out.append(f'<g clip-path="url(#{rid})" filter="url(#glow)">' + P(face, "none", stroke=lt["rim"], sw=lt["rim_w"], op=.95) + "</g>")
    out.append(front)
    bcol = dark(cfg["hair_col"], .25) if cfg["hair"] not in ("solenne", "severin", "iona") else dark(cfg["hair_col"], .5)
    for s in (-1, 1):
        out.append(f'<g opacity=".92">{brow(eg, s, ex["brow"] or cfg["brow"], bcol)}</g>')
    if "headset_on" in cfg.get("acc", []) or ex.get("headset"):
        out.append(P("M -54,-4 C -60,-90 -30,-120 0,-122 C 30,-120 60,-90 54,-4", stroke="#101014", sw=10) + P("M -50,-30 C -52,-90 -26,-114 0,-116", stroke="#3a3a46", sw=2.4))
        for s in (-1, 1):
            out.append(E(s * 54, 8, 15, 22, "#18181d", stroke=LINE, sw=1.6) + E(s * 56, 8, 9, 15, "#2a2a33") + P(f"M {s * 50},-6 Q {s * 54},-12 {s * 60},-6", stroke="#6fb8ff", sw=1.6, op=.8))
        out.append(P("M -54,20 C -50,44 -36,54 -16,56", stroke="#18181d", sw=3) + C(-14, 56, 3.5, "#18181d"))
    if "circlet" in cfg.get("acc", []):
        out.append(P("M -46,-54 Q 0,-78 46,-54", stroke="#d8b04a", sw=3) + P("M 0,-72 L -5,-64 L 0,-58 L 5,-64 Z", "#ffe08a", stroke="#8a6a10", sw=1))
    if ex["sweat"]:
        out.append(G(P("M 0,0 Q 7,11 0,16 Q -7,11 0,0 Z", "#dff2ff", stroke="#7aa8d0", sw=1.2) + C(-1.5, 10, 1.8, "#fff"), 40, -36))
    return "".join(out)


def back_head(key, rim="#b48cff", body=True, cloth="#6c6a68"):
    cfg = CAST[key]
    col, hi = cfg["hair_col"], cfg["hair_hi"]
    gid, gdef = hgrad(col, hi)
    fill = f"url(#{gid})"
    skin_sh = mix(cfg["skin"], "#4a2e6e", .45)
    out = [gdef]
    if body:
        out.append(P(shoulders(0.96), cloth, stroke=LINE, sw=2) + P("M 30,96 C 70,104 120,114 145,140 L 168,270 L 60,270 Z", dark(cloth, .3), op=.8))
        out.append(P("M -20,20 L -24,110 L 24,110 L 20,20 Z", skin_sh, stroke=LINE, sw=1.6))
    for s_ in (-1, 1):
        out.append(G(P("M 0,-8 C 12,-14 15,12 2,22 Z", skin_sh, stroke=LINE, sw=1.6), 46 * s_, 0, sx=s_, s=1))
    out.append(P("M -60,30 C -70,-52 -44,-112 0,-114 C 44,-112 70,-52 60,30 C 40,48 20,40 0,54 C -20,40 -40,48 -60,30 Z", fill, stroke=LINE, sw=1.6))
    out.append(locks([(-44, -10, -52, 52, 24, -6), (-18, 0, -20, 66, 24, -2), (10, 0, 12, 66, 24, 2), (38, -10, 48, 52, 24, 6)], fill, hi))
    if cfg["hair"] == "wren":
        out.append(P(leaf_d(44, -80, 54, 10, 14, 6), "#e9edf6", stroke=LINE, sw=1.2))
    out.append(sheen := "".join(P(leaf_d(x, -96, x + dx, -70, 8, 0), hi, op=.7) for x, dx in ((-30, -6), (-10, -2), (10, 2), (30, 6))))
    if rim:
        rid = uid("rb")
        out.append(f'<defs><clipPath id="{rid}"><rect x="16" y="-130" width="180" height="420"/></clipPath></defs>')
        out.append(f'<g clip-path="url(#{rid})" filter="url(#glow)">' + P("M -60,30 C -70,-52 -44,-112 0,-114 C 44,-112 70,-52 60,30", stroke=rim, sw=2.6) + (P(shoulders(0.96), stroke=rim, sw=2.4) if body else "") + "</g>")
    return "".join(out)
