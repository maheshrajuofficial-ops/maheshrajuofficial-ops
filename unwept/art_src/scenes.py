"""Backgrounds, hands, props and pixel-art game screens for Chapter 1."""
import math, random
from art import *
from figures import tube

LINE = "#120c18"


def vgrad(W, H, stops, x=0, y=0):
    gid = uid("vg")
    return f"<defs>{lin(gid, [(o, c, 1) for o, c in stops])}</defs>" + R(x, y, W, H, f"url(#{gid})")


def rglow(cx, cy, r, col, op=1.0):
    gid = uid("rg")
    return f"<defs>{rad(gid, [(0, col, op), (1, col, 0)])}</defs>" + C(cx, cy, r, f"url(#{gid})")


def vignette(W, H, op=.75):
    gid = uid("vn")
    return f"<defs>{rad(gid, [(0, '#000', 0), (.65, '#000', 0), (1, '#000', op)], r=.75)}</defs>" + R(0, 0, W, H, f"url(#{gid})")

# ------------------------------------------------------------------ hands

def hand2(x, y, ang=0, s=1, skin="#efd9c8", shade=None, curl=(0, 0, 0, 0), thumb=0.0, spread=1.0, nails=True,
          side=1, glove=None, cracks_col=None, lines=True):
    shade = shade or mix(skin, "#4a2e6e", .4)
    fill = glove or skin
    sh = shade if not glove else dark(glove, .4)
    out = []
    # thumb (behind palm edge)
    ta = math.radians(-128 - thumb * 40)
    tx0, ty0 = -20, -16
    t1 = (tx0 + math.cos(ta) * 22, ty0 + math.sin(ta) * 22)
    ta2 = ta + math.radians(18 + thumb * 30)
    t2 = (t1[0] + math.cos(ta2) * 18, t1[1] + math.sin(ta2) * 18)
    out.append(tube([(tx0, ty0, 18), (t1[0], t1[1], 14), (t2[0], t2[1], 11)], fill, sh, sw=1.8))
    out.append(P("M -20,0 C -25,-20 -27,-44 -25,-62 C -10,-66 10,-66 25,-61 C 26,-40 24,-18 20,0 Z", fill, stroke=LINE, sw=1.8))
    out.append(P("M 8,-62 C 20,-62 26,-58 25,-40 C 24,-20 22,-8 20,0 L 10,0 C 14,-20 14,-40 8,-62 Z", sh, op=.7))
    bx = [-18.5, -6.5, 6, 18]
    Ls = [40, 50, 47, 36]
    ws = [11.5, 12.5, 12, 10.5]
    for i in range(4):
        a = math.radians(-90 + spread * (i - 1.5) * 7)
        c = curl[i]
        pts = [(bx[i], -58, ws[i])]
        px, py = bx[i], -58
        for k, (frac, wk) in enumerate(((.45, .95), (.32, .88), (.23, .8))):
            a += math.radians(c * 32) * (1 if side > 0 else 1)
            l = Ls[i] * frac * (1 - c * .55)
            px, py = px + math.cos(a) * l, py + math.sin(a) * l
            pts.append((px, py, ws[i] * wk))
        out.append(tube(pts, fill, sh, sw=1.6))
        if lines and not glove:
            for (jx, jy, jw) in pts[1:3]:
                out.append(P(f"M {jx - jw * .3:.1f},{jy:.1f} q {jw * .3:.1f},2 {jw * .6:.1f},0", stroke=dark(shade, .2), sw=1.1, op=.7))
        if nails and not glove:
            tx, ty, tw = pts[-1]
            out.append(E(tx, ty + 2.5, tw * .3, tw * .38, light(skin, .3), op=.8))
    if cracks_col:
        out.append(cracks(0, -30, n=4, length=34, color=cracks_col, seed=int(x + y) % 97, sw=1.6))
    return G("".join(out), x, y, s, rot=ang, sx=s * side)


def thumb_press(x, y, s=1, skin="#efd9c8", blur=False):
    """a thumb seen from above pressing down (for controller close-ups)."""
    sh = mix(skin, "#4a2e6e", .4)
    g = tube([(-90, 40, 40), (-40, 10, 32), (0, 0, 26)], skin, sh, sw=2)
    g += E(4, -2, 9, 11, light(skin, .35), op=.9, rot=-20) + P("M -40,4 q 4,10 0,20", stroke=sh, sw=1.6)
    return G(g, x, y, s)

# ------------------------------------------------------------------ props

def controller(x, y, s=1, glow="#4aa3ff"):
    g = P("M -150,-40 C -120,-70 120,-70 150,-40 C 190,0 200,90 160,110 C 130,124 110,90 80,60 L -80,60 C -110,90 -130,124 -160,110 C -200,90 -190,0 -150,-40 Z", "#1c1d24", stroke=LINE, sw=3)
    g += P("M -140,-46 C -110,-62 110,-62 140,-46", stroke="#4a4c5a", sw=3)
    g += R(-104, -16, 16, 46, "#0e0e12", rx=3) + R(-119, -1, 46, 16, "#0e0e12", rx=3)
    for dx, dy, col in ((96, -20, "#e2544a"), (122, 6, "#4ab0e2"), (96, 30, "#62d27a"), (70, 6, "#e2c84a")):
        g += C(dx, dy, 11, "#0e0e12") + C(dx, dy, 8.5, dark(col, .2)) + C(dx - 2, dy - 2, 3, light(col, .3), op=.8)
    g += C(-44, 44, 22, "#0e0e12", stroke="#3a3c48", sw=2) + C(44, 44, 22, "#0e0e12", stroke="#3a3c48", sw=2)
    g += R(-22, -24, 14, 6, "#3a3c48", rx=3) + R(8, -24, 14, 6, "#3a3c48", rx=3)
    g += P("M -150,-40 C -120,-70 120,-70 150,-40", stroke=glow, sw=2, op=.5, flt="glow")
    return G(g, x, y, s)


def phone(x, y, w, h, screen="", rot=0, face_down=False, glow=True):
    if face_down:
        g = R(-w / 2, -h / 2, w, h, "#1a1b22", rx=14, stroke=LINE, sw=2.4) + R(-w / 2 + 10, -h / 2 + 10, 40, 40, "#26272f", rx=10) + C(-w / 2 + 30, -h / 2 + 30, 8, "#0d0d10")
        return G(g, x, y, rot=rot)
    sid = uid("ph")
    g = ""
    if glow:
        g += R(-w / 2 - 20, -h / 2 - 20, w + 40, h + 40, "#9ad0ff", rx=30, op=.25, flt="blur14")
    g += R(-w / 2, -h / 2, w, h, "#0d0d12", rx=16, stroke=LINE, sw=2.4)
    g += f"<defs>{clip(sid, f'M {-w / 2 + 6},{-h / 2 + 6} h {w - 12} v {h - 12} h {-w + 12} Z')}</defs>"
    g += f'<g clip-path="url(#{sid})">' + R(-w / 2 + 6, -h / 2 + 6, w - 12, h - 12, "#14182a") + screen + "</g>"
    return G(g, x, y, rot=rot)


def notif(x, y, w, sender, text, size=18):
    g = R(x, y, w, 70, "#f4f5fa", rx=12, op=.96) + C(x + 26, y + 35, 14, "#f2c230") + T(x + 26, y + 41, "L", 16, "#3a2a10", anchor="middle", font="Arial", weight="bold")
    g += T(x + 50, y + 28, sender, size, "#111", font="Arial", weight="bold") + T(x + 50, y + 52, text, size - 2, "#333", font="Arial")
    return g


def monitor(x, y, w, h, inner="", glow="#4aa3ff", bezel=10):
    sid = uid("mn")
    g = R(x - 30, y - 30, w + 60, h + 60, glow, rx=30, op=.18, flt="blur30")
    g += R(x - bezel, y - bezel, w + 2 * bezel, h + 2 * bezel, "#0a0a0e", rx=6, stroke=LINE, sw=2)
    g += f"<defs>{clip(sid, f'M {x},{y} h {w} v {h} h {-w} Z')}</defs>"
    g += f'<g clip-path="url(#{sid})">' + R(x, y, w, h, "#0a1020") + inner + R(x, y, w, h * .45, "#ffffff", op=.04) + "</g>"
    return g


def can(x, y, s=1, col="#3ad06a", tipped=False):
    g = R(-12, -40, 24, 40, col, rx=4, stroke=LINE, sw=1.6) + R(-12, -40, 24, 6, "#c8ccd4", rx=3) + R(-6, -30, 6, 22, "#ffffff", op=.25) + R(4, -36, 7, 36, "#000", op=.25)
    return G(g, x, y, s, rot=90 if tipped else 0)


def gravestone(x, y, s=1, col="#2a3040", text=None):
    g = P("M -50,0 L -50,-110 C -50,-150 50,-150 50,-110 L 50,0 Z", col, stroke=LINE, sw=2)
    g += P("M 30,-130 C 44,-120 46,-100 46,0 L 50,0 L 50,-110 C 50,-130 40,-140 30,-130 Z", "#000", op=.35)
    if text:
        for i, line in enumerate(text):
            g += T(0, -96 + i * 22, line, 15 if i else 17, "#aeb6c6", anchor="middle", font="Georgia", weight="bold" if i == 0 else "normal")
    return G(g, x, y, s)


def umbrella_mourner(x, y, s=1, bend=0.5, col="#0d0f16", umb="#08090d", seed=1, umbrella=True, rim="#5a6a8a"):
    rnd = random.Random(seed)
    hy = -262 + bend * 26
    hx = bend * 12
    g = ""
    g += P("M -22,-118 L -24,0 L -8,0 L -6,-118 Z M 6,-118 L 8,0 L 24,0 L 22,-118 Z", col)
    sh = -236 + bend * 6
    g += P(f"M -36,{sh} Q 0,{sh - 14} 36,{sh} L 50,-96 Q 0,-88 -50,-96 Z", col)
    g += P(f"M -36,{sh} Q -40,{sh + 40} -46,-110", stroke=rim, sw=1.4, op=.35)
    g += C(hx, hy, 21, col)
    g += P(f"M -14,{sh + 2} Q {hx - 10},{hy + 14} {hx + 14},{hy + 16}", stroke=col, sw=12)
    if rnd.random() < .45:
        g += E(hx + 6, hy + 10, 9, 6, "#c8ccd8", op=.75)
    if umbrella:
        ux, uy = 8, -340 + bend * 16
        g += P(f"M 22,{sh + 6} L 10,{sh + 44}", stroke=col, sw=12) + P(f"M {ux},{uy + 6} L {ux},{sh + 46}", stroke="#202432", sw=3)
        g += P(f"M {ux - 100},{uy + 40} Q {ux},{uy - 56} {ux + 100},{uy + 40} Q {ux + 75},{uy + 28} {ux + 50},{uy + 40} Q {ux + 25},{uy + 26} {ux},{uy + 40} Q {ux - 25},{uy + 26} {ux - 50},{uy + 40} Q {ux - 75},{uy + 28} {ux - 100},{uy + 40} Z", umb, stroke="#3a4560", sw=1.4)
        g += P(f"M {ux - 92},{uy + 34} Q {ux - 40},{uy - 28} {ux + 10},{uy - 10}", stroke="#8ea2c8", sw=1.6, op=.45)
        g += P(f"M {ux},{uy - 14} L {ux},{uy - 4}", stroke="#202432", sw=3)
    return G(g, x, y, s)

# ------------------------------------------------------------------ pixel art
PAL = {"k": "#06040c", "w": "#f4f0ff", "y": "#ffd56b", "o": "#ff9a3a", "v": "#8a5cff", "V": "#c9a5ff", "b": "#2a1d52",
       "g": "#7a7f99", "G": "#3e4256", "s": "#f0c8a8", "h": "#3b2a21", "H": "#6a4a36", "r": "#e2544a", "c": "#d9ccb2",
       "p": "#e7b84a", "n": "#18122e", "m": "#4a3a8a", "x": "#0f1230", "z": "#5ac0ff"}

BOY = ["...kkk...",
       "..khhhk..",
       "..kssk...",
       "..kssk.y.",
       ".kGGGGkyy",
       ".kGGGGkyy",
       "..kGGk...",
       "..k..k...",
       ".kk..kk.."]

SHADOW = ["...kkkk...",
          ".kknnnnkk.",
          "knnvnnvnnk",
          "knnnnnnnnk",
          "knnnnnnnnk",
          ".knkknkkn.",
          ".k..k..k.."]

MOM = ["....hhh.....",
       "...hhhhh.p..",
       "..hhhhhhhp..",
       "..hhsssshp..",
       "..hsksksh...",
       "..hssssss...",
       "...ssrss....",
       "....sss.....",
       "..cccccccc..",
       ".cccccccccc.",
       ".cccccccccc."]

HEART = [".rr.rr.", "rrrrrrr", "rrrrrrr", ".rrrrr.", "..rrr..", "...r..."]


_FS = [1.0]


def pix_text(x, y, txt, size, col="#f4f0ff", anchor="start", glow=False):
    return T(x, y, txt, size * _FS[0], col, font="VT323", anchor=anchor, flt="glow" if glow else None)


def pixel_screen(kind, W, H, ps=8, t=0):
    """Draws a chunky pixel game screen sized W x H (in panel units)."""
    out = []
    _FS[0] = max(.32, W / 800)
    rnd = random.Random(kind)
    if kind == "title":
        out.append(vgrad(W, H, [(0, "#120a2a"), (.6, "#3a1f6e"), (1, "#5a2f8e")]))
        for _ in range(60):
            out.append(R(rnd.randrange(0, W // ps) * ps, rnd.randrange(0, int(H * .55) // ps) * ps, ps * .6, ps * .6, "#f4f0ff", op=round(rnd.uniform(.3, 1), 2)))
        hill = []
        for i in range(W // ps + 1):
            hy = H * .74 - math.sin(i / (W / ps) * math.pi) * H * .12
            hill.append(R(i * ps, int(hy // ps) * ps, ps, H, "#06040c"))
        out.append("".join(hill))
        out.append(rglow(W / 2, H * .6, 70, "#ffd56b", .55))
        out.append(pixels(["..k..", ".kyk.", "kyyyk", "kyoyk", "kyyyk", ".kkk."], W / 2 - 2.5 * ps, H * .6 - 3 * ps, ps, PAL))
        out.append(pix_text(W / 2, H * .2, "untitled", 54, "#f4f0ff", "middle", True))
        out.append(pix_text(W / 2, H * .2 + 34 * _FS[0], "(for jonah & lily)", 30, "#c9a5ff", "middle"))
        out.append(pix_text(W / 2, H * .9, "build 0.9  —  PRESS START", 30, "#ffd56b", "middle", True))
    elif kind == "forest":
        out.append(vgrad(W, H, [(0, "#0a0716"), (1, "#1a1036")]))
        for i in range(14):
            x = rnd.randrange(0, W // ps) * ps
            h = rnd.randrange(int(H * .4), int(H * .9))
            out.append(R(x, H - h, ps * rnd.randrange(2, 4), h, "#06040c"))
            out.append(pixels(["..k..", ".kkk.", "kkkkk"], x - 2 * ps + ps, H - h - 3 * ps, ps, PAL))
        out.append(R(0, H * .82, W, H * .18, "#06040c"))
        bx = W * .58
        out.append(R(bx - 20, 0, 40, H * .82, "#f4f0ff", op=.25, flt="glow2"))
        for yy in range(0, int(H * .82), ps * 2):
            out.append(R(bx - 4, yy, 8, ps, "#f4f0ff", op=.9))
        out.append(pixels(BOY, bx - 4.5 * ps, H * .82 - 9 * ps, ps, PAL))
        for k in range(1, 4):
            out.append(pixels(BOY, bx - 4.5 * ps - k * 7 * ps, H * .82 - 9 * ps, ps, {**PAL, "G": "#3e4256", "s": "#c9a5ff", "h": "#5a4a8a"}).join([f'<g opacity="{.5 - k * .12:.2f}">', "</g>"]))
    elif kind == "city":
        out.append(vgrad(W, H, [(0, "#0c0a1e"), (1, "#20184a")]))
        for i in range(10):
            x = i * W / 10 + rnd.randint(-10, 10)
            h = rnd.randrange(int(H * .3), int(H * .7))
            out.append(R(int(x // ps) * ps, H * .7 - h, ps * rnd.randrange(5, 9), h, "#14102a"))
            for wy in range(int(H * .7 - h + 2 * ps), int(H * .7), ps * 3):
                if rnd.random() < .5:
                    out.append(R(int(x // ps) * ps + ps, wy, ps, ps, "#3a2f6e"))
        out.append(R(0, H * .7, W, H * .3, "#06040c"))
        for yy in range(int(H * .7), H, ps * 2):
            out.append(R(rnd.randrange(0, W), yy, ps * 6, ps * .5, "#2a1d52"))
        out.append(R(W * .45, H * .42, ps * 3, H * .3, "#2a2440"))
        out.append(pixels(BOY, W * .45 + ps * 3, H * .7 - 9 * ps, ps, PAL))
        out.append(pixels(HEART, W * .45 + ps * 4, H * .7 - 17 * ps, ps, {"r": "#6a6a78", ".": None}))
        out.append(pixels(SHADOW, W * .18, H * .7 - 7 * ps, ps, PAL))
        out.append(pixels(SHADOW, W * .72, H * .7 - 7 * ps, ps, PAL))
        out.append(pix_text(16, 34, "LV 4 — THE DROWNED BLOCKS", 30, "#c9a5ff"))
    elif kind == "tower":
        out.append(vgrad(W, H, [(0, "#05030c"), (.7, "#1a1036"), (1, "#2a1d52")]))
        for _ in range(70):
            out.append(R(rnd.randrange(0, W // ps) * ps, rnd.randrange(0, H // ps) * ps, ps * .6, ps * .6, "#f4f0ff", op=round(rnd.uniform(.3, 1), 2)))
        cx = W / 2
        out.append(rglow(cx, H * .5, H * .5, "#f4f0ff", .35))
        for yy in range(int(H * .08), int(H * .86), ps):
            wdt = 2 + int((yy / H) * 6)
            out.append(R(cx - wdt * ps / 2, yy, wdt * ps, ps, "#f4f0ff" if (yy // ps) % 4 else "#c9a5ff"))
        out.append(R(0, H * .86, W, H * .14, "#06040c"))
        out.append(P(f"M {cx - 120},{H * .86} Q {cx},{H * .78} {cx + 120},{H * .86} Z", "#1a1036"))
    elif kind == "ledge":
        out.append(vgrad(W, H, [(0, "#05030c"), (1, "#1a1036")]))
        cx = W / 2
        for yy in range(int(H * .45), H, ps):
            out.append(R(cx - 5 * ps, yy, 10 * ps, ps, "#f4f0ff" if (yy // ps) % 4 else "#c9a5ff"))
        out.append(R(cx - 7 * ps, H * .45 - ps, 14 * ps, ps, "#ffd56b"))
        out.append(pixels(BOY, cx - 4.5 * ps + ps * 3, H * .45 - 10 * ps, ps, PAL))
        out.append(R(cx - 3 * ps, H * .08, 6 * ps, 9 * ps, "#06040c", stroke="#ffd56b", sw=3))
        out.append(pix_text(cx, H * .08 - 10, "?", 40, "#ffd56b", "middle", True))
    elif kind == "dialog":
        out.append(vgrad(W, H, [(0, "#120a2a"), (1, "#2a1d52")]))
        out.append(R(20, H * .38, W - 40, H * .56, "#06040c", stroke="#f4f0ff", sw=4))
        out.append(R(36, H * .44, 12 * 9 + 16, 11 * 9 + 16, "#2a1d52", stroke="#c9a5ff", sw=2))
        out.append(pixels(MOM, 44, H * .44 + 8, 9, PAL))
        out.append(pix_text(170, H * .44 + 30, "MOM.wav", 34, "#ffd56b", glow=True))
    elif kind == "levelup":
        out.append(vgrad(W, H, [(0, "#1a1036"), (1, "#3a1f6e")]))
        out.append(R(W * .2, H * .3, W * .6, H * .4, "#06040c", stroke="#ffd56b", sw=5))
        out.append(pix_text(W / 2, H * .56, "LEVEL UP!", 72, "#ffd56b", "middle", True))
        for i in range(14):
            a = i / 14 * math.tau
            out.append(R(W / 2 + math.cos(a) * W * .38, H / 2 + math.sin(a) * H * .38, ps, ps, "#ffd56b"))
    elif kind == "thanks":
        out.append(R(0, 0, W, H, "#06040c"))
        out.append(pix_text(W / 2, H * .38, "THANK YOU FOR PLAYING", 52, "#f4f0ff", "middle", True))
        out.append(pix_text(W / 2, H * .38 + 40, "(unfinished)", 34, "#c9a5ff", "middle"))
        out.append(pixels(["..k..", ".kyk.", "kyyyk", "kyoyk", "kyyyk", ".kkk."], W / 2 - 2.5 * ps, H * .58, ps, PAL))
    return "".join(out)

# ------------------------------------------------------------------ environments

def drowned_ruins(W, H, horizon=0.58, dome=True, seed=3, detail=1.0):
    rnd = random.Random(seed)
    hy = H * horizon
    out = [vgrad(W, H, [(0, "#0b0618"), (.45, "#2a1546"), (.8, "#5a2f6e"), (1, "#7a4a7e")])]
    out.append(mist(-100, hy - 200, W + 200, 260, n=6, color="#b07ac8", op=.25, seed=seed, rmin=120, rmax=260))
    if dome:
        out.append(rglow(W * .78, hy, W * .22, "#f4f0ff", .55))
        out.append(P(f"M {W * .78 - 70},{hy} A 70,46 0 0 1 {W * .78 + 70},{hy} Z", "#f4f0ff", op=.75, flt="glow2"))
    for layer, (col, hmax, n) in enumerate((("#3a2650", .32, 14), ("#24163a", .42, 10), ("#140c22", .55, 7))):
        for i in range(n):
            x = rnd.uniform(-40, W)
            w = rnd.uniform(30, 90) * (1 + layer * .4)
            h = rnd.uniform(.12, hmax) * H
            tilt = rnd.uniform(-8, 8)
            top = hy - h
            d = f"M {x},{hy + 10} L {x + tilt},{top + 20} L {x + w * .3 + tilt},{top} L {x + w * .5 + tilt},{top + rnd.uniform(10, 40)} L {x + w * .8 + tilt},{top + rnd.uniform(0, 30)} L {x + w + tilt},{top + 30} L {x + w},{hy + 10} Z"
            out.append(P(d, col))
            if layer == 2:
                for wy in range(int(top + 40), int(hy), 34):
                    out.append(R(x + w * .25 + tilt * .5, wy, w * .16, 18, "#05030a", rx=w * .08))
                    out.append(R(x + w * .6 + tilt * .5, wy, w * .16, 18, "#05030a", rx=w * .08))
    # cathedral half-sunk
    cx, cw = W * .32, W * .34
    base = hy + 6
    cath = (f"M {cx},{base} L {cx},{base - 170} L {cx + cw * .12},{base - 240} L {cx + cw * .24},{base - 170} L {cx + cw * .24},{base - 220} "
            f"L {cx + cw * .5},{base - 330} L {cx + cw * .62},{base - 250} L {cx + cw * .66},{base - 300} L {cx + cw * .7},{base - 230} L {cx + cw * .76},{base - 220} L {cx + cw},{base - 160} L {cx + cw},{base} Z")
    out.append(P(cath, "#0d0818", stroke="#3a2650", sw=1.5))
    out.append(C(cx + cw * .5, base - 190, 34, "none", stroke="#6a4a8a", sw=3) + C(cx + cw * .5, base - 190, 34, "#1a1030"))
    for k in range(8):
        a = k / 8 * math.tau
        out.append(P(f"M {cx + cw * .5},{base - 190} L {cx + cw * .5 + math.cos(a) * 34:.1f},{base - 190 + math.sin(a) * 34:.1f}", stroke="#6a4a8a", sw=2))
    out.append(C(cx + cw * .5, base - 190, 10, "#8a5cff", op=.6, flt="glow"))
    for ax in (.1, .32, .68, .9):
        out.append(P(f"M {cx + cw * ax - 14},{base} L {cx + cw * ax - 14},{base - 70} Q {cx + cw * ax},{base - 100} {cx + cw * ax + 14},{base - 70} L {cx + cw * ax + 14},{base} Z", "#05030a"))
    # water
    out.append(vgrad(W, H - hy, [(0, "#1a0f2a"), (1, "#05030a")], 0, hy))
    for i in range(int(90 * detail)):
        x = rnd.uniform(0, W)
        y = rnd.uniform(hy + 4, H)
        out.append(R(x, y, rnd.uniform(20, 120), 1.6, "#b07ac8", op=round(rnd.uniform(.08, .35), 2)))
    out.append(R(W * .78 - 50, hy + 4, 100, H * .25, "#f4f0ff", op=.12, flt="blur14"))
    # mist rivers
    out.append(mist(-100, hy - 30, W + 200, 120, n=8, color="#9a6ac0", op=.35, seed=seed + 1, rmin=140, rmax=280))
    out.append(mist(-100, hy + 60, W + 200, 200, n=7, color="#6a4a9a", op=.3, seed=seed + 2, rmin=120, rmax=240))
    return "".join(out)


def silt_ground(W, H, top, seed=4, glossy=True):
    rnd = random.Random(seed)
    out = [P(f"M 0,{top} " + " ".join(f"Q {x + 40},{top + rnd.uniform(-14, 14):.0f} {x + 80},{top + rnd.uniform(-8, 8):.0f}" for x in range(0, W + 80, 80)) + f" L {W},{H} L 0,{H} Z", "#07050b")]
    if glossy:
        for _ in range(26):
            x, y = rnd.uniform(0, W), rnd.uniform(top + 10, H)
            out.append(E(x, y, rnd.uniform(20, 70), rnd.uniform(2, 5), "#6a4a9a", op=round(rnd.uniform(.15, .45), 2)))
        for _ in range(16):
            x, y = rnd.uniform(0, W), rnd.uniform(top + 10, H)
            out.append(P(f"M {x:.0f},{y:.0f} q 12,-8 24,0", stroke="#2a1d40", sw=2))
    return "".join(out)


def void_bg(W, H, seed=1):
    return (vgrad(W, H, [(0, "#05030a"), (.5, "#1a0a33"), (1, "#05030a")]) + rglow(W / 2, H / 2, max(W, H) * .6, "#5a2fa0", .45)
            + vlines(W, H, n=50, color="#c9a5ff", op=.35, seed=seed) + particles(0, 0, W, H, n=60, color="#c9a5ff", rmax=1.8, seed=seed))


def mud_splash(cx, cy, r=200, seed=2, col="#0a070e", hl="#7a5aa8"):
    rnd = random.Random(seed)
    out = []
    for i in range(22):
        a = rnd.uniform(-math.pi, 0) if rnd.random() < .8 else rnd.uniform(0, math.pi)
        L = rnd.uniform(.4, 1.1) * r
        w = rnd.uniform(8, 26)
        x1, y1 = cx + math.cos(a) * L, cy + math.sin(a) * L
        nx, ny = -math.sin(a), math.cos(a)
        out.append(P(f"M {cx + nx * w:.0f},{cy + ny * w:.0f} Q {cx + math.cos(a) * L * .6 + nx * w * .6:.0f},{cy + math.sin(a) * L * .6 + ny * w * .6:.0f} {x1:.0f},{y1:.0f} Q {cx + math.cos(a) * L * .6 - nx * w * .6:.0f},{cy + math.sin(a) * L * .6 - ny * w * .6:.0f} {cx - nx * w:.0f},{cy - ny * w:.0f} Z", col))
        out.append(C(x1 + math.cos(a) * 14, y1 + math.sin(a) * 14, w * .45, col))
        out.append(P(f"M {cx + math.cos(a) * L * .3:.0f},{cy + math.sin(a) * L * .3:.0f} L {cx + math.cos(a) * L * .75:.0f},{cy + math.sin(a) * L * .75:.0f}", stroke=hl, sw=1.6, op=.6))
    for _ in range(30):
        a = rnd.uniform(-math.pi, math.pi)
        L = rnd.uniform(.8, 1.5) * r
        out.append(C(cx + math.cos(a) * L, cy + math.sin(a) * L * .8, rnd.uniform(3, 9), col))
    return "".join(out)


def iron_tag(x, y, s=1, rot=0):
    g = P("M -200,-80 L -40,-140", stroke="#2a2420", sw=6)
    g += R(-120, -100, 240, 300, "#5a5c64", rx=14, stroke=LINE, sw=3) + R(-108, -88, 216, 276, "#6c6e78", rx=10)
    g += C(0, -70, 14, "#22222a", stroke=LINE, sw=2)
    for i, (txt, sz) in enumerate((("WREN", 46), ("CALLOWAY", 34), ("— UNLIT —", 28), ("SNUFFED", 28), ("YEAR 312", 28))):
        g += T(0, -10 + i * 42, txt, sz, "#2a2a30", anchor="middle", font="Georgia", weight="bold")
        g += T(1.5, -8.5 + i * 42, txt, sz, "#9a9ca8", anchor="middle", font="Georgia", weight="bold", op=.35)
    rnd = random.Random(4)
    for _ in range(18):
        g += C(rnd.uniform(-100, 100), rnd.uniform(-90, 180), rnd.uniform(3, 10), "#7a4a2a", op=.45)
    g += P("M -108,-88 L 108,-88", stroke="#a0a2ae", sw=3, op=.8)
    return G(g, x, y, s, rot=rot)


def bottle_lantern(x, y, s=1, rot=0, lit=False):
    g = P("M -10,-150 Q 0,-176 10,-150", stroke="#555", sw=4) + R(-22, -150, 44, 18, "#3a3a40", rx=4, stroke=LINE, sw=2)
    g += P("M -40,-134 C -60,-80 -56,-10 -36,10 L 36,10 C 56,-10 60,-80 40,-134 Z", "#9ab8c8", stroke=LINE, sw=2.4, op=.5)
    g += P("M -30,-120 C -44,-70 -40,-20 -26,0", stroke="#ffffff", sw=4, op=.5)
    g += P("M -8,-128 L 6,-92 L -6,-70 L 10,-40 L 2,-20", stroke="#ffffff", sw=2.4, op=.85) + P("M 6,-92 L 26,-84 M -6,-70 L -24,-60", stroke="#ffffff", sw=1.6, op=.7)
    g += R(-34, 6, 68, 16, "#3a3a40", rx=4, stroke=LINE, sw=2)
    g += P("M -6,-36 Q 0,-52 6,-36 Q 0,-30 -6,-36 Z", "#555", op=.8)
    if lit:
        g += C(0, -50, 30, "#ffd56b", op=.6, flt="glow2")
    return G(g, x, y, s, rot=rot)


def drawer_scene(W, H):
    out = [vgrad(W, H, [(0, "#3a2a1a"), (1, "#1a1008")])]
    out.append(P(f"M 60,{H * .3} L {W - 60},{H * .3} L {W - 20},{H} L 20,{H} Z", "#5a3e24", stroke="#1a1008", sw=3))
    out.append(P(f"M 100,{H * .36} L {W - 100},{H * .36} L {W - 70},{H} L 70,{H} Z", "#2a1c10"))
    rnd = random.Random(9)
    for _ in range(10):
        x, y = rnd.uniform(140, W - 140), rnd.uniform(H * .45, H * .9)
        out.append(P(f"M {x:.0f},{y:.0f} l {rnd.uniform(40, 90):.0f},{rnd.uniform(-20, 20):.0f}", stroke="#a89a80", sw=rnd.uniform(3, 7)))
    out.append(hand2(W * .55, H * 1.02, ang=-10, s=2.2, skin="#d8b89a", curl=(.35, .25, .3, .45), thumb=.2, spread=1.4))
    for _ in range(14):
        x, y = rnd.uniform(W * .4, W * .75), rnd.uniform(H * .5, H * .9)
        out.append(P(f"M {x:.0f},{y:.0f} q 10,-4 18,2", stroke="#8a6a50", sw=1.4, op=.7))
    return "".join(out)
