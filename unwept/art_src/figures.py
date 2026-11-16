"""Full-body standing figures (front view, light from upper-left). Frame: feet at y~965, head top ~0."""
import math, random
from art import *
from chars import head, CAST, LINE, null_patch

HS = 0.72  # head scale
HY = 82    # head centre y


def limb(ax, ay, bx, by, wa, wb, fill, shade=None, stroke=LINE, sw=2, round_end=True):
    dx, dy = bx - ax, by - ay
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    a1 = (ax + nx * wa / 2, ay + ny * wa / 2)
    a2 = (ax - nx * wa / 2, ay - ny * wa / 2)
    b1 = (bx + nx * wb / 2, by + ny * wb / 2)
    b2 = (bx - nx * wb / 2, by - ny * wb / 2)
    mx, my = (ax + bx) / 2, (ay + by) / 2
    wm = (wa + wb) / 4 + 2.5
    m1 = (mx + nx * wm, my + ny * wm)
    m2 = (mx - nx * wm, my - ny * wm)
    end = f"A {wb / 2:.1f},{wb / 2:.1f} 0 0 1 {b2[0]:.1f},{b2[1]:.1f}" if round_end else f"L {b2[0]:.1f},{b2[1]:.1f}"
    d = (f"M {a1[0]:.1f},{a1[1]:.1f} Q {m1[0]:.1f},{m1[1]:.1f} {b1[0]:.1f},{b1[1]:.1f} {end} "
         f"Q {m2[0]:.1f},{m2[1]:.1f} {a2[0]:.1f},{a2[1]:.1f} Z")
    out = P(d, fill, stroke=stroke, sw=sw)
    if shade:
        # shade the side facing +x (away from the light)
        sgn = -1 if nx > 0 else 1
        c1 = (ax + sgn * nx * wa * .05, ay + sgn * ny * wa * .05)
        c2 = (bx + sgn * nx * wb * .05, by + sgn * ny * wb * .05)
        e1 = (ax + sgn * nx * wa / 2, ay + sgn * ny * wa / 2)
        e2 = (bx + sgn * nx * wb / 2, by + sgn * ny * wb / 2)
        me = (mx + sgn * nx * wm, my + sgn * ny * wm)
        out += P(f"M {c1[0]:.1f},{c1[1]:.1f} L {c2[0]:.1f},{c2[1]:.1f} L {e2[0]:.1f},{e2[1]:.1f} Q {me[0]:.1f},{me[1]:.1f} {e1[0]:.1f},{e1[1]:.1f} Z", shade, op=.75)
    return out


def _offsets(pts):
    L, Rr = [], []
    n = len(pts)
    for i, (x, y, w) in enumerate(pts):
        if i == 0:
            dx, dy = pts[1][0] - x, pts[1][1] - y
        elif i == n - 1:
            dx, dy = x - pts[i - 1][0], y - pts[i - 1][1]
        else:
            dx, dy = pts[i + 1][0] - pts[i - 1][0], pts[i + 1][1] - pts[i - 1][1]
        l = math.hypot(dx, dy) or 1
        nx, ny = -dy / l, dx / l
        L.append((x + nx * w / 2, y + ny * w / 2))
        Rr.append((x - nx * w / 2, y - ny * w / 2))
    return L, Rr


def _cr(points):
    """Catmull-Rom through points -> cubic segments string (without initial M)."""
    s = ""
    p = [points[0]] + points + [points[-1]]
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        s += f" C {c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return s


def tube(pts, fill, shade=None, stroke=LINE, sw=2, cap=True, rim=None):
    """pts: [(x,y,width),...] centreline. Light from the left: shade on the +x side."""
    L, Rr = _offsets(pts)
    w_end = pts[-1][2]
    end = f" A {w_end / 2:.1f},{w_end / 2:.1f} 0 0 {1 if pts[-1][1] >= pts[-2][1] else 0} {Rr[-1][0]:.1f},{Rr[-1][1]:.1f}" if cap else f" L {Rr[-1][0]:.1f},{Rr[-1][1]:.1f}"
    d = f"M {L[0][0]:.1f},{L[0][1]:.1f}" + _cr(L) + end + _cr(Rr[::-1]) + " Z"
    out = P(d, fill, stroke=stroke, sw=sw)
    if shade:
        side = [(a if a[0] > b[0] else b) for a, b in zip(L, Rr)]
        mid = [((x + (sx - x) * .1), y) for (x, y, w), (sx, sy) in zip(pts, side)]
        sd = f"M {mid[0][0]:.1f},{mid[0][1]:.1f}" + _cr(mid) + f" L {side[-1][0]:.1f},{side[-1][1]:.1f}" + _cr(side[::-1]) + " Z"
        out += P(sd, shade, op=.7)
    if rim:
        side = [(a if a[0] > b[0] else b) for a, b in zip(L, Rr)]
        out += P(f"M {side[0][0]:.1f},{side[0][1]:.1f}" + _cr(side), stroke=rim, sw=2.2, op=.8, flt="glow")
    return out


def hand(x, y, s, col, kind="open", side=1):
    """simple hand hanging down at (x,y) wrist."""
    line = LINE
    if kind == "fist":
        d = "M -11,0 C -14,10 -13,24 -6,28 L 8,28 C 14,24 14,10 11,0 Z"
        extra = P("M -8,14 L 9,14 M -8,20 L 9,20", stroke=dark(col, .4), sw=1.2)
    else:
        d = "M -11,0 C -13,14 -12,30 -7,38 L -4,38 L -4,30 L 0,40 L 4,40 L 5,30 L 8,36 L 11,34 C 13,22 13,10 11,0 Z"
        extra = P("M -12,6 C -18,14 -18,22 -14,26", col, stroke=line, sw=1.6)
    return G(P(d, col, stroke=line, sw=1.8) + extra + P("M 4,4 L 6,26", stroke=dark(col, .3), sw=1.2, op=.6), x, y, s, sx=side * s)


def boot(x, y, col, side=1, tall=0, trim=None):
    d = f"M -15,{-tall} L -16,0 C -18,22 -20,34 -16,40 L {20 * side if side > 0 else 14},{42} C {40 if side > 0 else 30},44 {40 if side > 0 else 30},30 22,22 L 16,0 L 15,{-tall} Z"
    shoe = f"M -16,-4 C -18,22 -20,34 -16,40 L 26,42 C 42,42 40,28 22,20 L 16,-4 Z"
    body = ""
    if tall:
        body += P(f"M -17,{-tall} L -16,0 L 16,0 L 17,{-tall} Z", col, stroke=LINE, sw=1.8)
        if trim:
            body += P(f"M -17,{-tall + 6} L 17,{-tall + 6}", stroke=trim, sw=3)
    body += P(shoe, col, stroke=LINE, sw=1.8) + P("M -14,38 L 30,40", stroke=dark(col, .5), sw=3) + P("M -6,6 Q 4,10 12,4", stroke=light(col, .3), sw=1.4, op=.6)
    return G(body, x, y, sx=side, s=1)


def prop(kind, x, y, s=1, rot=0):
    if kind == "bread":
        g = (E(0, 0, 30, 19, "#d79a4a", stroke=LINE, sw=1.8) + E(-4, -5, 22, 10, "#e9b46a", op=.8)
             + P("M -14,-12 Q -10,-2 -16,6 M -2,-15 Q 2,-4 -4,6 M 10,-14 Q 14,-4 8,6", stroke="#8a5a22", sw=2)
             + E(-10, -9, 6, 3, "#fff2cc", op=.7))
    elif kind == "lantern":
        g = (P("M -4,-60 Q 0,-74 4,-60", stroke="#555", sw=2) + R(-10, -60, 20, 8, "#3a3a40", rx=2, stroke=LINE, sw=1.5)
             + P("M -16,-52 C -24,-30 -22,-4 -14,4 L 14,4 C 22,-4 24,-30 16,-52 Z", "#aac4d4", stroke=LINE, sw=1.8, op=.55)
             + P("M -6,-46 L 2,-30 L -4,-20 L 6,-6", stroke="#ffffff", sw=1.4, op=.8) + R(-14, 2, 28, 7, "#3a3a40", rx=2, stroke=LINE, sw=1.5))
    elif kind == "wrench":
        g = (P("M 0,0 L 0,-90", stroke="#8a9098", sw=9) + P("M 0,0 L 0,-90", stroke="#c9ced6", sw=3)
             + P("M -14,-90 L -14,-112 L -6,-104 L 6,-104 L 14,-112 L 14,-90 Q 0,-82 -14,-90 Z", "#9aa0a8", stroke=LINE, sw=1.6))
    elif kind == "notebook":
        g = (R(-22, -30, 44, 58, "#7a3a2a", rx=3, stroke=LINE, sw=1.8) + R(-18, -26, 36, 50, "#f2ead6", rx=2)
             + P("M -12,-14 L 12,-14 M -12,-6 L 10,-6 M -12,2 L 12,2", stroke="#9a8a6a", sw=1.4) + C(0, 12, 6, "#1b1b22") + P("M 0,8 L 0,14", stroke="#fff", sw=1.4))
    elif kind == "rapier":
        g = (P("M 0,0 L 0,330", stroke="#e9eef6", sw=4) + P("M 0,0 L 0,330", stroke="#ffffff", sw=1.4) + P("M 0,0 L 0,330", stroke="#bfe6ff", sw=8, op=.25, flt="glow")
             + P("M -18,0 Q 0,-20 18,0 Q 0,10 -18,0 Z", "#e6c060", stroke=LINE, sw=1.6) + R(-4, -36, 8, 34, "#f4f0e8", rx=2, stroke=LINE, sw=1.4) + C(0, -40, 6, "#e6c060", stroke=LINE, sw=1.4))
    elif kind == "glaive":
        g = (P("M 0,-436 L 0,420", stroke="#2a2a30", sw=9) + P("M -2,-436 L -2,420", stroke="#55555f", sw=2)
             + P("M -14,-470 C -26,-500 -8,-530 0,-560 C 8,-530 26,-500 14,-470 Z", "#c9ced6", stroke=LINE, sw=1.8)
             + R(-16, -480, 32, 18, "#a87a34", rx=3, stroke=LINE, sw=1.6) + R(-12, -470, 24, 34, "#3a2a14", rx=4, stroke=LINE, sw=1.4) + C(0, -453, 12, "#ffd27a", op=.8, flt="glow2") + C(0, -453, 6, "#fff4cc"))
    elif kind == "tag":
        g = R(-9, 0, 18, 24, "#55565c", rx=2, stroke=LINE, sw=1.4)
    else:
        g = ""
    return G(g, x, y, s, rot=rot)


def greatsword_back(flame=True):
    g = ""
    # blade runs from hilt above viewer-right shoulder down behind the body to lower-left
    if flame:
        g += P("M 70,120 C 10,260 -40,420 -110,640 L -40,640 C 0,420 60,260 120,110 Z", "#ff7a1a", op=.5, flt="blur6")
        g += P("M 140,40 C 170,0 150,-40 176,-70 C 186,-20 176,30 150,70 Z", "#ffb03a", op=.85, flt="glow")
        g += P("M -96,600 C -130,640 -110,690 -140,720 C -100,700 -80,660 -70,620 Z", "#ffb03a", op=.85, flt="glow")
    g += P("M 96,96 L 128,108 L -60,640 L -92,628 Z", "#7c818c", stroke=LINE, sw=2) + P("M 112,102 L -76,634", stroke="#e8ecf2", sw=2.4)
    g += P("M 74,82 L 150,118", stroke="#c8962c", sw=11) + P("M 74,82 L 150,118", stroke="#ffe08a", sw=2.5, op=.7)
    g += P("M 116,96 L 142,30", stroke="#3a2a20", sw=12) + C(145, 22, 10, "#c8962c", stroke=LINE, sw=1.4)
    return g


# ------------------------------------------------------------------ outfit configs
FIG = {
    "wren": dict(sw=86, ww=54, hw=66, top="#1e2538", top_d="#121726", pants="#1a1c24", boots="#121216", boot_tall=60,
                 coat=dict(hem=640, open=False, col="#1e2538", trim="#3a4462"), sleeve="#1e2538", hands="#121216",
                 arms=("down", "hold"), props={"r": ("bread", 0)}, collar="high", buttons="#c8963c", patch=True),
    "wren_exile": dict(sw=82, ww=50, hw=60, top="#6c6a68", top_d="#4a4846", pants="#3e3a36", boots=None, boot_tall=0,
                       tunic=True, sleeve=None, hands="skin", arms=("down", "hold"), props={"r": ("lantern", 0)},
                       collar=None, cracks=True, tag=True),
    "jonah": dict(sw=84, ww=58, hw=64, top="#7c7f88", top_d="#5a5c64", pants="#2b3446", boots="#e8e8ea", boot_tall=0,
                  hoodie=True, sleeve="#7c7f88", hands="skin", arms=("pocket", "pocket"), collar=None),
    "june": dict(hs=1.12, sw=70, ww=46, hw=56, top="#5e6a3a", top_d="#434b28", pants="#3a3428", boots="#4a3220", boot_tall=70,
                 coat=dict(hem=470, open=True, col="#5e6a3a", trim="#6e7a46"), shirt="#2c3a40", sleeve="#5e6a3a", rolled=True,
                 hands="skin", arms=("down", "hold"), props={"r": ("wrench", 0)}, belt="#6a4a2a", scale=0.86),
    "otto": dict(sw=96, ww=70, hw=74, top="#1e2538", top_d="#121726", pants="#232838", boots="#2a1c14", boot_tall=30,
                 coat=dict(hem=620, open=True, col="#1e2538", trim="#27304a"), shirt="#e9e2d2", sleeve="#1e2538", hands="skin",
                 arms=("down", "hold"), props={"r": ("notebook", 0)}, satchel=True, scale=1.04),
    "solenne": dict(sw=72, ww=44, hw=60, top="#f3f1ec", top_d="#cfd3dc", pants="#e9e9ee", boots="#f4f4f6", boot_tall=180,
                    boot_trim="#d4a640", coat=dict(hem=600, open=True, col="#f3f1ec", trim="#d4a640"), shirt="#f3f1ec",
                    sleeve="#f3f1ec", hands="#ffffff", arms=("down", "hold"), props={"r": ("rapier", 0)}, cape="#ffffff",
                    collar="high", gold="#d4a640"),
    "dorian": dict(sw=92, ww=58, hw=66, top="#16121a", top_d="#0c0a10", pants="#16121a", boots="#0c0a0e", boot_tall=150,
                   boot_trim="#a82c2c", coat=dict(hem=600, open=True, col="#16121a", trim="#a82c2c"), shirt="#16121a",
                   sleeve="#16121a", hands="#2a1a1a", arms=("hip", "down"), furcape=True, sword_back=True, collar="high",
                   gold="#d4a640", scale=1.04),
    "iona": dict(sw=90, ww=60, hw=68, top="#243a2c", top_d="#162418", pants="#1c241e", boots="#1a140e", boot_tall=150,
                 coat=dict(hem=830, open=True, col="#243a2c", trim="#3a5a44"), shirt="#1c2a20", sleeve="#243a2c",
                 hands="skin", arms=("hold", "down"), props={"l": ("glaive", 0)}, brass_arm=True, collar="high", scale=1.04),
    "severin": dict(sw=80, ww=52, hw=64, top="#f2f0ec", top_d="#d5d8de", pants="#f2f0ec", boots=None, robe=True,
                    sleeve="#f2f0ec", hands="#ffffff", arms=("clasp", "clasp"), collar="high", gold="#d2a644", scale=1.06),
    "miriam": dict(sw=72, ww=48, hw=62, top="#d9ccb2", top_d="#b8a888", pants="#3d4a66", boots="#6a4a3a", boot_tall=0,
                   coat=dict(hem=520, open=True, col="#d9ccb2", trim="#cdbf9f"), shirt="#f1ede4", sleeve="#d9ccb2",
                   hands="skin", arms=("down", "hold"), props={"r": ("notebook", 0)}),
    "jonah11": dict(sw=54, ww=42, hw=46, top="#16161c", top_d="#0c0c10", pants="#16161c", boots="#0a0a0c", boot_tall=0,
                    coat=dict(hem=520, open=True, col="#1c1c24", trim="#1c1c24"), shirt="#e8e8ee", sleeve="#1c1c24", hands="skin",
                    arms=("down", "down"), child=True, scale=0.74, hs=1.3),
    "lily4": dict(sw=50, ww=40, hw=44, top="#f2c230", top_d="#c9961c", pants="#3a4a6a", boots="#e23b4a", boot_tall=60,
                  coat=dict(hem=560, open=False, col="#f2c230", trim="#e6b222"), sleeve="#f2c230", hands="skin",
                  arms=("down", "down"), child=True, scale=0.6, hs=1.45),
}


def figure(key, fig_key=None, expr=None, lit=None, rim="#9a7bff"):
    rim_ = rim
    f = FIG[fig_key or key]
    cfg = CAST[key]
    skin = cfg["skin"]
    sh = mix(skin, "#4a2e6e", .38)
    sw_, ww, hw = f["sw"], f["ww"], f["hw"]
    child = f.get("child")
    leg_top = 470 if not child else 470
    knee_y, ank_y = 700, 922
    hands_col = skin if f.get("hands") in (None, "skin") else f["hands"]
    out = []
    # ---- behind body
    if f.get("cape"):
        out.append(P(f"M {-sw_ - 6},170 C {-sw_ - 40},300 {-sw_ - 30},420 {-sw_ - 50},520 L {sw_ + 50},520 C {sw_ + 30},420 {sw_ + 40},300 {sw_ + 6},170 Z", dark(f["cape"], .15), stroke=LINE, sw=2))
    if f.get("sword_back"):
        out.append(greatsword_back())
    if f.get("robe"):
        out.append(P(f"M {-hw - 10},430 C {-hw - 40},600 {-hw - 70},800 {-hw - 90},960 L {hw + 90},960 C {hw + 70},800 {hw + 40},600 {hw + 10},430 Z", f["top"], stroke=LINE, sw=2))
        out.append(P(f"M 10,440 C 40,600 60,800 {hw + 90},960 L {hw + 90},960 L {hw + 90},960 C {hw + 70},800 {hw + 40},600 {hw + 10},430 Z", f["top_d"], op=.85))
        out.append(P(f"M {-hw - 90},956 L {hw + 90},956", stroke=f["gold"], sw=5))
        for x in (-60, -20, 30, 70):
            out.append(P(f"M {x * .4},460 Q {x * .9},700 {x * 1.4},950", stroke=f["top_d"], sw=2))
        out.append(P("M 0,450 L 0,956", stroke=f["gold"], sw=6))
    hs = HS * f.get("hs", 1.0)
    hy = 135 - 66 * hs
    out.append(head(key, expr=expr, lit=dict(rim=rim, **(lit or {})), body=False, part="back").join(['<g transform="translate(0,%.1f) scale(%s)">' % (hy, hs), "</g>"]))
    # ---- legs
    lx, rx = -30, 30
    if not f.get("robe"):
        pants = f["pants"]
        psh = dark(pants, .35)
        out.append(tube([(-hw + 26, leg_top - 30, 68), (lx - 6, 580, 58), (lx - 10, knee_y, 42), (lx - 13, 800, 44), (lx - 12, ank_y, 30)], pants, psh, cap=False))
        out.append(tube([(hw - 26, leg_top - 30, 68), (rx + 10, 580, 58), (rx + 14, knee_y, 42), (rx + 20, 800, 44), (rx + 22, ank_y, 30)], pants, psh, cap=False, rim=rim))
        if f.get("tunic"):
            for X in (lx - 12, rx + 22):
                out.append(P(f"M {X - 15},{ank_y - 60} L {X + 15},{ank_y - 60} L {X + 13},{ank_y - 20} L {X - 13},{ank_y - 20} Z", "#8a7a66", stroke=LINE, sw=1.4))
                out.append(P(f"M {X - 14},{ank_y - 50} L {X + 14},{ank_y - 44} M {X - 13},{ank_y - 36} L {X + 13},{ank_y - 30}", stroke="#5a4a3a", sw=1.4))
            out.append(G(P("M -14,0 C -18,24 -18,34 -14,40 L 22,40 C 34,38 30,28 18,20 L 14,0 Z", skin, stroke=LINE, sw=1.8), lx - 12, ank_y - 2))
            out.append(G(P("M -14,0 C -18,24 -18,34 -14,40 L 22,40 C 34,38 30,28 18,20 L 14,0 Z", sh, stroke=LINE, sw=1.8), rx + 22, ank_y - 2, sx=-1, s=1))
        if f.get("boots"):
            out.append(boot(lx - 12, ank_y, f["boots"], -1, f.get("boot_tall", 0), f.get("boot_trim")))
            out.append(boot(rx + 22, ank_y, f["boots"], 1, f.get("boot_tall", 0), f.get("boot_trim")))
    # ---- torso
    top, topd = f["top"], f["top_d"]
    torso = (f"M -16,140 L {-sw_ + 14},160 Q {-sw_ - 2},166 {-sw_ - 4},196 L {-ww},372 L {-hw},452 L {hw},452 L {ww},372 "
             f"L {sw_ + 4},196 Q {sw_ + 2},166 {sw_ - 14},160 L 16,140 Z")
    if f.get("robe"):
        torso = (f"M -16,140 L {-sw_ + 14},160 Q {-sw_ - 2},166 {-sw_ - 4},196 L {-ww - 4},372 L {-hw - 10},440 L {hw + 10},440 L {ww + 4},372 "
                 f"L {sw_ + 4},196 Q {sw_ + 2},166 {sw_ - 14},160 L 16,140 Z")
    out.append(P(torso, top, stroke=LINE, sw=2.2))
    out.append(P(f"M 20,150 L {sw_ - 14},162 Q {sw_ + 2},168 {sw_ + 4},196 L {ww},372 L {hw},452 L 30,452 C 40,360 30,240 20,150 Z", topd, op=.8))
    if f.get("shirt") and f.get("coat", {}).get("open"):
        out.append(P(f"M -20,146 L -30,452 L 30,452 L 20,146 Z", f["shirt"], stroke=LINE, sw=1.6))
        out.append(P(f"M 4,150 L 18,452 L 30,452 L 20,146 Z", dark(f["shirt"], .25), op=.7))
        out.append(P(f"M -20,146 L -46,170 L -34,452 L -30,452 Z M 20,146 L 46,170 L 34,452 L 30,452 Z", f["coat"]["trim"], stroke=LINE, sw=1.6))
    if f.get("hoodie"):
        out.append(P("M -70,166 C -62,128 -30,128 -24,150 Q 0,170 24,150 C 30,128 62,128 70,166 C 60,196 -60,196 -70,166 Z", light(top, .1), stroke=LINE, sw=2))
        out.append(P("M -14,182 L -16,250 M 14,182 L 16,254", stroke="#d8d8dc", sw=3))
        out.append(P(f"M -52,330 L 52,330 L 58,420 L -58,420 Z", dark(top, .08), stroke=LINE, sw=1.6))
        out.append(P(f"M {-hw},452 L {hw},452 L {hw - 2},470 L {-hw + 2},470 Z", dark(top, .2), stroke=LINE, sw=1.6))
        out.append(P("M -50,150 C -46,190 46,190 50,150", stroke="#121216", sw=8))
        out.append(E(-50, 166, 15, 18, "#18181d", stroke=LINE, sw=1.4, rot=-14) + E(50, 166, 15, 18, "#18181d", stroke=LINE, sw=1.4, rot=14))
    if f.get("tunic"):
        rnd = random.Random(7)
        hem = f"M {-hw - 6},440 " + " ".join(f"L {-hw - 6 + i * (2 * hw + 12) / 12:.0f},{560 + rnd.uniform(-26, 18):.0f}" for i in range(13)) + f" L {hw + 6},440 Z"
        out.append(P(hem, top, stroke=LINE, sw=2))
        out.append(P(f"M {-hw},452 L {hw},452", stroke="#3a2a20", sw=7))
        out.append(P("M -30,148 Q 0,196 30,148", "#4d4b4a", stroke=LINE, sw=1.6))
        for _ in range(8):
            x, y = rnd.uniform(-60, 60), rnd.uniform(200, 520)
            out.append(P(f"M {x:.0f},{y:.0f} l {rnd.uniform(8, 18):.0f},{rnd.uniform(-5, 5):.0f}", stroke="#3e3c3b", sw=1.6))
    # coat skirt
    coat = f.get("coat")
    if coat:
        hem = coat["hem"]
        col = coat["col"]
        if coat["open"]:
            for s in (-1, 1):
                d = f"M {s * 6},380 L {s * ww},372 L {s * hw},452 C {s * (hw + 14)},{(452 + hem) / 2} {s * (hw + 26)},{hem - 40} {s * (hw + 34)},{hem} L {s * 30},{hem - 6} C {s * 24},{hem - 120} {s * 22},520 {s * 30},452 Z"
                out.append(P(d, col if s < 0 else dark(col, .22), stroke=LINE, sw=2))
                out.append(P(f"M {s * 30},452 C {s * 22},520 {s * 24},{hem - 120} {s * 30},{hem - 6}", stroke=coat["trim"], sw=4))
                out.append(P(f"M {s * (hw - 4)},480 C {s * (hw + 4)},560 {s * (hw + 10)},{hem - 60} {s * (hw + 8)},{hem - 10}", stroke=dark(col, .4), sw=1.6))
        else:
            d = f"M {-ww},372 L {-hw},452 C {-hw - 12},{(452 + hem) / 2} {-hw - 24},{hem - 40} {-hw - 30},{hem} L {hw + 30},{hem} C {hw + 24},{hem - 40} {hw + 12},{(452 + hem) / 2} {hw},452 L {ww},372 Z"
            out.append(P(d, col, stroke=LINE, sw=2))
            out.append(P(f"M 10,452 L 30,{hem} L {hw + 30},{hem} C {hw + 24},{hem - 40} {hw + 12},{(452 + hem) / 2} {hw},452 Z", dark(col, .3), op=.8))
            out.append(P(f"M 4,452 L 10,{hem}", stroke=LINE, sw=2) + P(f"M {-hw + 10},500 L {-hw},{hem - 20} M {hw - 20},500 L {hw},{hem - 30}", stroke=dark(col, .4), sw=1.6))
    if f.get("belt"):
        out.append(R(-hw + 4, 432, 2 * hw - 8, 18, f["belt"], rx=3, stroke=LINE, sw=1.6))
        for x in (-34, -10, 24):
            out.append(R(x, 440, 14, 26, dark(f["belt"], .2), rx=2, stroke=LINE, sw=1.3))
        out.append(R(-8, 434, 16, 14, "#c8a050", rx=2, stroke=LINE, sw=1.2))
    if coat and not coat["open"]:
        out.append(P("M 0,150 L 0,452", stroke=dark(top, .5), sw=2))
        if f.get("buttons"):
            for y in (220, 280, 340, 400):
                out.append(C(-10, y, 5.5, f["buttons"], stroke="#4a3010", sw=1.2) + C(-11.5, y - 1.5, 1.8, "#ffe6a8"))
    if f.get("gold"):
        out.append(P(f"M {-ww + 2},372 L {ww - 2},372", stroke=f["gold"], sw=3))
        if f.get("robe"):
            out.append(P("M 0,150 L 0,440", stroke=f["gold"], sw=5))
            for y in (220, 300):
                out.append(G(C(0, 0, 12, "none", stroke=f["gold"], sw=1.8) + P("M -7,0 L 7,0 M 0,-7 L 0,7", stroke=f["gold"], sw=1.6), -40, y) + G(C(0, 0, 12, "none", stroke=f["gold"], sw=1.8) + P("M -7,0 L 7,0 M 0,-7 L 0,7", stroke=f["gold"], sw=1.6), 40, y))
    if f.get("satchel"):
        out.append(P("M -70,170 L 70,420", stroke="#7a4e2a", sw=14) + P("M -70,170 L 70,420", stroke="#5a3418", sw=2))
        out.append(R(40, 400, 70, 60, "#8a5a32", rx=6, stroke=LINE, sw=1.8) + R(40, 400, 70, 24, "#7a4e2a", rx=6, stroke=LINE, sw=1.6))
        out.append(P("M 48,404 L 56,384 L 66,404 M 74,404 L 82,388 L 92,404", "#f2ead6", stroke=LINE, sw=1))
        out.append(C(-46, 220, 10, "#111", stroke="#ddd", sw=1.4) + P("M -46,212 L -46,226", stroke="#fff", sw=2.4))
    if f.get("patch"):
        out.append(null_patch(sw_ - 24, 210, 0.9))
    if f.get("cape"):
        out.append(P(f"M {-sw_ - 8},168 C {-sw_ + 10},146 -40,140 -26,146 L -34,210 C -60,226 {-sw_ - 10},250 {-sw_ - 26},300 Z", f["cape"], stroke=LINE, sw=1.8))
        out.append(P(f"M {sw_ + 8},168 C {sw_ - 10},146 40,140 26,146 L 34,210 C 60,226 {sw_ + 10},250 {sw_ + 26},300 Z", dark(f["cape"], .12), stroke=LINE, sw=1.8))
        out.append(P(f"M {-sw_ - 26},300 C {-sw_ - 10},250 -60,226 -34,210 M {sw_ + 26},300 C {sw_ + 10},250 60,226 34,210", stroke=f["gold"], sw=3.4))
        out.append(C(-30, 196, 7, "#e6b84a", stroke="#7a5a10", sw=1.4) + C(30, 196, 7, "#e6b84a", stroke="#7a5a10", sw=1.4))
    if f.get("furcape"):
        out.append(P(f"M {-sw_ - 22},180 C {-sw_ - 10},140 -60,130 -20,146 L -30,220 C -60,240 {-sw_ - 30},330 {-sw_ - 40},560 L {-sw_ - 70},560 Z", "#8a1e22", stroke=LINE, sw=2))
        out.append(P(f"M {-sw_ - 40},560 C {-sw_ - 30},330 -60,240 -30,220", stroke="#5a1012", sw=3))
        rnd = random.Random(2)
        fur = f"M {-sw_ - 24},186 " + " ".join(f"Q {-sw_ - 20 + i * 9 + rnd.uniform(-3, 3):.0f},{150 - i * 2 + rnd.uniform(-8, 0):.0f} {-sw_ - 14 + i * 9:.0f},{156 - i * 2:.0f}" for i in range(10)) + " L -18,176 L -20,150 C -60,136 -90,140 {} Z".format(f"{-sw_ - 24},186")
        out.append(P(fur, "#d9cdb8", stroke=LINE, sw=1.4))
    # ---- arms
    skin_or = lambda c: skin if c in (None, "skin") else c
    sleeve = f.get("sleeve") or skin
    for s, pose in ((-1, f["arms"][0]), (1, f["arms"][1])):
        sx = s * (sw_ - 4)
        if pose == "down":
            el, wr = (s * (sw_ + 10), 350), (s * (sw_ + 6), 500)
        elif pose == "hold":
            el, wr = (s * (sw_ + 14), 340), (s * (sw_ - 14), 470)
        elif pose == "pocket":
            el, wr = (s * (sw_ + 16), 330), (s * 40, 420)
        elif pose == "hip":
            el, wr = (s * (sw_ + 50), 300), (s * (hw + 4), 420)
        elif pose == "clasp":
            el, wr = (s * (sw_ + 4), 330), (s * 14, 420)
        sl = sleeve
        brass = f.get("brass_arm") and s > 0
        if brass:
            sl = "#a87a34"
        shd = dark(sl, .35)
        out.append(E(sx + s * 2, 194, 26, 30, sl, stroke=LINE, sw=2) + (E(sx + 8, 196, 14, 26, shd, op=.6) if s > 0 else ""))
        fore = sl
        if f.get("tunic") or f.get("rolled"):
            fore = skin
        mid1 = ((sx + el[0]) / 2 + s * 3, (186 + el[1]) / 2)
        mid2 = ((el[0] + wr[0]) / 2 + s * 2, (el[1] + wr[1]) / 2)
        rr = rim if s > 0 else None
        if f.get("robe"):
            out.append(tube([(sx, 182, 48), mid1 + (44,), el + (40,), mid2 + (50,), wr + (62,)], sl, shd, cap=False, rim=rr))
        elif fore == sl:
            out.append(tube([(sx, 182, 48), mid1 + (42,), el + (34,), mid2 + (34,), wr + (26,)], sl, shd, rim=rr))
        else:
            out.append(tube([el + (32,), mid2 + (32,), wr + (24,)], fore, sh, rim=rr))
            out.append(tube([(sx, 182, 48), mid1 + (42,), (el[0], el[1] + 6, 36)], sl, shd, rim=rr))
        if f.get("rolled"):
            out.append(tube([(el[0], el[1] - 14, 44), (el[0] + (wr[0] - el[0]) * .14, el[1] + 18, 40)], f["sleeve"], dark(f["sleeve"], .3), cap=False))
        if brass:
            out.append(C(el[0], el[1], 10, "#ffd27a", flt="glow2") + C(el[0], el[1], 6, "#fff4cc"))
            out.append(C(wr[0], wr[1], 8, "#ffd27a", flt="glow2") + C(wr[0], wr[1], 4.5, "#fff4cc"))
            out.append(P(f"M {sx},200 L {el[0]},{el[1] - 14}", stroke="#f2c878", sw=3, op=.7))
        if f.get("cracks") and pose == "down":
            out.append(cracks(wr[0], wr[1] - 40, n=3, length=28, color="#a673ff", seed=5 + s, sw=1.6, base=-1.4, spread=2))
        if pose not in ("pocket", "clasp"):
            hc = hands_col if not brass else "#a87a34"
            out.append(hand(wr[0], wr[1] - 2, 1.0, hc, "fist" if pose in ("hold", "hip") else "open", side=-s))
    if f.get("arms")[0] == "clasp":
        out.append(G(E(0, 0, 26, 18, f.get("hands", skin), stroke=LINE, sw=1.8) + P("M -10,-6 L 12,6 M -12,4 L 8,12", stroke="#c8ccd4", sw=1.4), 0, 430))
    if f.get("hoodie"):
        out.append(P("M -54,396 Q 0,380 54,396", stroke=dark(top, .4), sw=2))
    # props
    for side, (kind, rot) in (f.get("props") or {}).items():
        s = -1 if side == "l" else 1
        pose = f["arms"][0 if s < 0 else 1]
        if pose == "hold":
            wr = (s * (sw_ - 14), 470)
        else:
            wr = (s * (sw_ + 6), 500)
        if kind == "bread":
            out.append(prop("bread", wr[0] - 4 * s, wr[1] + 6))
        elif kind == "lantern":
            out.append(prop("lantern", wr[0], wr[1] + 90))
        elif kind == "wrench":
            out.append(prop("wrench", wr[0], wr[1] + 30, rot=-8))
        elif kind == "notebook":
            out.append(prop("notebook", wr[0] - 6 * s, wr[1] + 10, rot=-8))
        elif kind == "rapier":
            out.append(prop("rapier", wr[0], wr[1] + 10, rot=-12))
        elif kind == "glaive":
            out.append(prop("glaive", wr[0] - 2, wr[1] + 10))
    if f.get("tag"):
        out.append(P("M -24,150 C -20,190 -8,210 0,220 C 8,210 20,190 24,150", stroke="#2a2420", sw=2) + R(-10, 216, 20, 26, "#55565c", rx=2, stroke=LINE, sw=1.5) + C(0, 221, 2, "#222"))
    # ---- neck + collar + head
    nk = 13
    out.append(P(f"M {-nk},100 L {-nk - 2},160 L {nk + 2},160 L {nk},100 Z", skin, stroke=LINE, sw=1.8) + P(f"M {-nk - 2},118 Q 0,150 {nk + 2},118 L {nk + 2},140 Q 0,154 {-nk - 2},140 Z", sh, op=.8))
    if cfg["marks"] and "vein" in cfg["marks"]:
        out.append(P("M -26,98 C -22,116 -18,130 -12,150", stroke="#141018", sw=2) + P("M -26,98 C -22,116 -18,130 -12,150", stroke="#9a6bff", sw=1, op=.5, flt="glow"))
    if f.get("collar") == "high":
        col = top if not f.get("robe") else f["top"]
        out.append(P("M -22,118 L -26,160 Q 0,172 26,160 L 22,118 Q 0,128 -22,118 Z", col, stroke=LINE, sw=1.8) + P("M 0,126 L 0,168", stroke=dark(col, .5), sw=1.6))
        if f.get("gold"):
            out.append(P("M -22,122 Q 0,132 22,122", stroke=f["gold"], sw=2.4))
    hs = HS * f.get("hs", 1.0)
    hy = 135 - 66 * hs
    out.append(head(key, expr=expr, lit=dict(rim=rim, **(lit or {})), body=False, part="front").join(['<g transform="translate(0,%.1f) scale(%s)">' % (hy, hs), "</g>"]))
    g = "".join(out)
    sc = f.get("scale", 1.0)
    return g, sc
