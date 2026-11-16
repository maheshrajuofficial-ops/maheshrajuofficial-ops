"""Builds UNWEPT Arc 1 / Chapter 1 illustrated comic + character design sheets as one HTML file."""
import sys, html as H
from art import *
from chars import head, CAST
from figures import figure
from beasts import hush, hush_mask, murmur, wail, dirge, lament, crumb, human_silhouette
from scenes import drowned_ruins, rglow, vgrad, vignette, bottle_lantern, silt_ground
import panels

OUT = sys.argv[1] if len(sys.argv) > 1 else "comic.html"
ONLY = sys.argv[2] if len(sys.argv) > 2 else None
esc = lambda s: H.escape(s, quote=True)


def svg(vb, body, cls="", extra=""):
    return f'<svg class="{cls}" viewBox="{vb}" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg" {extra}>{body}</svg>'

# ------------------------------------------------------------------ cover

def cover():
    W, Hh = 800, 1140
    g = drowned_ruins(W, Hh, horizon=.74, seed=8, detail=.6)
    g += R(0, 0, W, Hh, "#05030a", op=.35)
    # the Pale on the horizon (wall of white light)
    g += R(560, 260, 240, 590, "#f4f0ff", op=.18, flt="blur30") + R(640, 300, 160, 550, "#ffffff", op=.22, flt="blur14")
    # giant Hush rising behind, made of violet mist
    g += rglow(400, 470, 430, "#8a5cff", .55)
    g += G(hush(with_mist=False), 400, 215, .95, op=.95)
    g += mist(-100, 600, W + 200, 300, n=8, color="#6a3ab0", op=.55, seed=31, rmin=140, rmax=280)
    g += P(f"M 0,{Hh * .86} Q 260,{Hh * .82} 420,{Hh * .85} T {W},{Hh * .84} L {W},{Hh} L 0,{Hh} Z", "#05030a")
    fg, sc = figure("wren_tunic", "wren_exile", expr=dict(cracks=True, hl=False), rim="#c9a5ff")
    k = .44
    g += E(400, Hh * .955, 120, 16, "#000", op=.6, flt="blur6")
    g += G(fg, 400, Hh * .955 - 965 * k, k)
    g += particles(0, 300, W, 800, n=90, color="#c9a5ff", rmax=2.4, seed=33)
    g += vignette(W, Hh, .8)
    return f'''<section id="cover" class="cover">{svg(f"0 0 {W} {Hh}", g, "cover-art")}
<div class="cover-title"><div class="kicker">A VERTICAL-SCROLL MANHWA</div><h1>UNWEPT</h1>
<div class="sub">ARC 1 · UNLIT</div><div class="tag">He never cried. Now the monsters can't find him.</div>
<nav class="cover-nav"><a href="#cast">Character designs</a><a href="#ch1">Read Chapter 1</a></nav></div></section>'''

# ------------------------------------------------------------------ character sheets

def stage(figs, w_each=380, top=-70, bottom=1010, glow="#8a5cff", labels=True):
    n = len(figs)
    W = w_each * n
    body = vgrad(W, bottom - top, [(0, "#0d0a18"), (1, "#05040a")], x=0, y=top)
    body += rglow(W / 2, 420, W * .55, glow, .28)
    body += "".join(P(f"M {x},{top} L {x},{bottom}", stroke="#ffffff", sw=1, op=.04) for x in range(0, W, 40))
    body += "".join(P(f"M 0,{y} L {W},{y}", stroke="#ffffff", sw=1, op=.04) for y in range(0, bottom, 40))
    for i, (g, scale, label) in enumerate(figs):
        cx = w_each * i + w_each / 2
        body += E(cx, 968, 120 * scale, 14, "#000", op=.7, flt="blur6")
        body += G(g, cx, 970 - 965 * scale, scale)
        if labels and label:
            body += T(cx, 1000, label, 22, "#a9a6bf", anchor="middle", font="Inter", weight="600", ls=3)
    return svg(f"0 {top} {W} {bottom - top}", body, "stage")


def fig_entry(key, fkey, label, expr=None, rim="#9a7bff", s=1.0):
    g, sc = figure(key, fkey, expr=expr, rim=rim)
    return (g, sc * s, label)


def bust(key, expr=None, lit=None, glow="#8a5cff"):
    body = rglow(0, 0, 220, glow, .35) + head(key, expr, lit)
    return svg("-170 -150 340 330", body, "bust")


def expr_card(key, label, expr=None, lit=None):
    body = rglow(0, 0, 140, "#2a2440", .9) + head(key, expr, lit)
    return f'<figure class="ex">{svg("-95 -125 190 205", body)}<figcaption>{esc(label)}</figcaption></figure>'


def palette(cols):
    return '<div class="pal">' + "".join(f'<span style="--s:{c}"><i></i>{esc(n)}</span>' for n, c in cols) + "</div>"


def sheet(no, name, alias, role, color, stage_svg, bust_svg, exprs, pal, notes, quote=None, wide=False):
    ex = "".join(exprs)
    nt = "".join(f"<li>{n}</li>" for n in notes)
    q = f'<blockquote>{esc(quote)}</blockquote>' if quote else ""
    return f'''<article class="sheet{' wide' if wide else ''}" style="--c:{color}" id="cs-{no}">
<header class="sh-h"><span class="sh-no">{no:02d}</span><div><h3>{esc(name)}{f" <small>{esc(alias)}</small>" if alias else ""}</h3><p class="sh-role">{role}</p></div></header>
<div class="sh-grid"><div class="sh-stage">{stage_svg}</div>
<div class="sh-side"><div class="sh-bust">{bust_svg}</div><div class="sh-info"><div class="sh-ex">{ex}</div>{pal}<ul class="sh-notes">{nt}</ul>{q}</div></div></div></article>'''


def cast():
    S = []
    S.append(sheet(1, "JONAH REED", 'as "WREN CALLOWAY"', "Protagonist · soul 24 (Earth) · body 16 (Orison) · Silt Wretch, Lv 1", "#9d8cff",
                   stage([fig_entry("jonah", "jonah", "EARTH · 24", rim="#6fb8ff"),
                          fig_entry("wren_tunic", "wren_exile", "OUTSIDE THE PALE", expr=dict(cracks=True, hl=False)),
                          fig_entry("wren", "wren", "LANTERNHALL")]),
                   bust("wren", dict(hl=False)),
                   [expr_card("wren", "Default: nothing", dict(hl=False)), expr_card("wren_tunic", "The chime (Ch 1)", dict(eyes="wide", glow="#b48cff", cracks=True)),
                    expr_card("jonah", "Stillwater, live", dict(sweat=True, headset=True), panels.MON)],
                   palette([("skin", "#e9e3ec"), ("hair", "#1e1f28"), ("streak", "#f4f6fb"), ("eyes", "#8d93a6"), ("undertow", "#a673ff"), ("coat", "#1e2538"), ("brass", "#c8963c")]),
                   ["Messy ash-black hair over the eyes, with <b>one white streak at his left temple</b>.",
                    "Sleepy gray eyes that glow violet as Undertow rises. The face <b>never moves</b>; that's the joke and the tragedy.",
                    "A thin black vein-scar from behind his right ear down his neck.",
                    "Outside the Pale: a tattered exile tunic, the iron tag WREN CALLOWAY · UNLIT, and mud-cracked skin leaking violet light.",
                    "Earth: short black hair, brown eyes, dark circles, gray hoodie and over-ear headset.",
                    "Lanternhall: charcoal-navy high-collar coat, brass lantern buttons, gray Null patch on the left shoulder. Usually holding bread."],
                   "Somebody had to be still. So I was.", wide=True))
    S.append(sheet(2, "THE HUSH", "Riptide Stalker form", "Jonah's monster self · 3 m · first seen in public in Ch 9 · class: Silent", "#b48cff",
                   stage([(hush(), 1.0, "3 m"), (G(human_silhouette(560, "#2a2440"), 0, 965), 1.0, "WREN · 1.7 m")], w_each=440),
                   svg("-120 -110 240 240", rglow(0, 0, 150, "#8a5cff", .55) + P("M -96,120 C -110,0 -70,-96 0,-100 C 70,-96 110,0 96,120 Z", "#07050c") + hush_mask(0, 10, 1.4), "bust"),
                   [f'<figure class="ex">{svg("-80 -80 160 160", rglow(0, 0, 90, "#8a5cff", .5) + hush_mask(0, 0, 1.1, crack=True))}<figcaption>Mask (cracked: Capsize)</figcaption></figure>',
                    f'<figure class="ex">{svg("-120 -150 240 240", rglow(0, 0, 120, "#8a5cff", .4) + G(hush(with_mist=False), 0, -150, .22))}<figcaption>Silhouette read</figcaption></figure>'],
                   palette([("plate", "#0c0a12"), ("seam", "#a673ff"), ("mask", "#f1eee8"), ("slits", "#e6d4ff"), ("mantle", "#07050c")]),
                   ["Glossy black plating like wet obsidian, with glowing violet seams.",
                    "A smooth white bone mask with <b>no mouth</b> and two vertical violet eye-slits.",
                    "A tattered mantle of shadow-tendrils, like a drowned cloak. Long four-clawed hands.",
                    "The mist goes perfectly still around him. <b>He never makes a sound</b>, so letter his fights with silence: no SFX."], wide=True))
    S.append(sheet(3, "JUNIPER “JUNE” CALLOWAY", None, "13 · Kindle, Lv 14 · Wren's little sister · engineer · first to see through him", "#ff9a3a",
                   stage([fig_entry("june", "june", "13", rim="#ffb35a")], w_each=420, glow="#ff8a3a"),
                   bust("june", dict(), dict(rim="#ffb35a"), "#ff8a3a"),
                   [expr_card("june", "Grin", dict(mouth="smile", blush=True)), expr_card("june", "Sobbing hug (Ch 4)", dict(tears=True, mouth="sob", brow="worried", eyes="half")),
                    expr_card("june", "Studying his face", dict(brow="sharp", look=(4, 0), mouth="flat"))],
                   palette([("hair", "#c4612b"), ("eyes", "#d08a2a"), ("jacket", "#5e6a3a"), ("goggles", "#8a6a3a"), ("skin", "#f2d8c4")]),
                   ["A short, messy copper-red bob with brass welding goggles pushed up on her forehead.",
                    "Freckles, amber eyes, bandaged fingertips.",
                    "An oversized, grease-stained olive work jacket with rolled sleeves, plus a tool belt.",
                    "Her brother cried at everything. This one doesn't. <b>She knows from the first hug.</b>"]))
    S.append(sheet(4, "OTTO WEXLEY", None, "16 · Tinder, Lv 6 · roommate · future founder of the Order of the Hush", "#7ee08a",
                   stage([fig_entry("otto", "otto", "16", rim="#7ee08a")], w_each=420, glow="#3a8a5a"),
                   bust("otto", dict(mouth="smile"), dict(rim="#7ee08a"), "#3a8a5a"),
                   [expr_card("otto", "Fourteen panels of talking", dict(mouth="open", eyes="wide")), expr_card("otto", "Fainting", dict(eyes="closed", mouth="o")),
                    expr_card("otto", "THE HUSH!!", dict(eyes="wide", mouth="smile", blush=True))],
                   palette([("hair", "#6e4426"), ("eyes", "#5e7a4a"), ("coat", "#1e2538"), ("satchel", "#7a4e2a"), ("blush", "#ff6a7a")]),
                   ["Tall and broad, with a round face, curly chestnut hair, thick round glasses and permanently flushed cheeks.",
                    "His Lanternhall collar is always unbuttoned. His satchel is stuffed with notebooks and sketches of the Hush.",
                    "A handmade pin: a black circle with a white finger over the lips.",
                    "Yield 9%: he feels everything, <b>loudly</b>."]))
    S.append(sheet(5, "SOLENNE HOLLOWAY", '"the Ice Lantern"', "16 · Beacon, Lv 63 · rival → investigator → partner", "#8fd0ff",
                   stage([fig_entry("solenne", "solenne", "16", rim="#bfe6ff")], w_each=420, glow="#4aa3ff"),
                   bust("solenne", dict(), dict(rim="#bfe6ff", shade="#2a3a6a"), "#4aa3ff"),
                   [expr_card("solenne", "Looking through you", dict(eyes="half", mouth="tiny")), expr_card("solenne", '"Nobody gets exactly sixty."', dict(brow="sharp", look=(3, 0))),
                    expr_card("solenne", '"...It tripped."', dict(eyes="normal", hl=False, mouth="flat"))],
                   palette([("hair", "#e7ebf3"), ("eyes", "#8fd0ff"), ("uniform", "#f3f1ec"), ("gold", "#d4a640"), ("ribbon", "#0d0d10")]),
                   ["Long, straight silver-white hair in a high ponytail tied with a black ribbon.",
                    "Pale ice-blue eyes and a small beauty mark under her left eye.",
                    "White-and-gold Beacon honors uniform with a short white shoulder cape.",
                    "<b>Matins</b>: a slender white-gold rapier with a lantern-shaped guard. She fights with blades and lances of hard white light."]))
    S.append(sheet(6, "DORIAN ASHGRAVE", None, "17 · Lantern, Lv 44 · enemy #1 (for now)", "#ff5a4a",
                   stage([fig_entry("dorian", "dorian", "17", rim="#ff8a4a")], w_each=480, glow="#c03a2a"),
                   bust("dorian", dict(mouth="smirk"), dict(rim="#ff8a4a", shade="#4a1a1a"), "#c03a2a"),
                   [expr_card("dorian", "Picking a target", dict(mouth="smirk", eyes="half")), expr_card("dorian", "Losing the Stakefire", dict(mouth="grit", brow="angry")),
                    expr_card("dorian", "Lunch with Otto", dict(eyes="pin", mouth="o"))],
                   palette([("hair", "#e0b648"), ("eyes", "#e2a12a"), ("uniform", "#16121a"), ("crimson", "#8a1e22"), ("flame", "#ff7a1a")]),
                   ["Tall and sharp-jawed, with slicked-back golden-blond hair, amber-gold eyes and a gold hoop in his left ear.",
                    "Black-and-crimson Lantern uniform with a fur-lined half-cape.",
                    "<b>Cinderbrand</b>: a greatsword wreathed in orange flame, carried across his back.",
                    "From Ch 27: loose hair, a scar through his left brow, and dented plain steel armor."]))
    S.append(sheet(7, "COMMANDER IONA STRAND", None, "46 · Beacon, Lv 79 (capped by choice) · signed Wren's exile", "#5ac08a",
                   stage([fig_entry("iona", "iona", "46", rim="#ffd27a")], w_each=420, glow="#2a6a4a"),
                   bust("iona", dict(), dict(rim="#ffd27a", shade="#1a2a2a"), "#2a6a4a"),
                   [expr_card("iona", "On duty", dict(mouth="flat")), expr_card("iona", "Seeing Wren alive", dict(eyes="wide", mouth="o")),
                    expr_card("iona", '"The price was too high."', dict(eyes="half", mouth="frown"))],
                   palette([("skin", "#6e4630"), ("hair", "#8f9198"), ("coat", "#243a2c"), ("brass", "#a87a34"), ("lantern", "#ffd27a")]),
                   ["Tall and muscular, with dark brown skin, close-cropped iron-gray hair and a long scar along her jaw.",
                    "Her left arm is brass and mechanical, with glowing lantern-glass joints.",
                    "A deep green Vigil longcoat with silver lantern insignia.",
                    "<b>Last Watch</b>: a lantern-headed glaive."]))
    S.append(sheet(8, "HIGH TALLIER SEVERIN ASHGRAVE", None, "300+ · Pyre, Lv 99 · the main antagonist (a white glove in Ch 5)", "#ffd56b",
                   stage([fig_entry("severin", "severin", "300+", rim="#ffe9a8")], w_each=460, glow="#a8802a"),
                   bust("severin", dict(mouth="flat"), dict(rim="#ffe9a8", shade="#4a4a5a"), "#a8802a"),
                   [expr_card("severin", "Yield 100%", dict(mouth="flat", hl=False)), expr_card("severin", '"NULL RETURNED."', dict(eyes="normal", brow="sharp", hl=False)),
                    expr_card("severin", "Almost a smile", dict(mouth="smirk", hl=False))],
                   palette([("hair", "#eeeef2"), ("eyes", "#d0d6dd"), ("robes", "#f2f0ec"), ("gold", "#d2a644"), ("gloves", "#ffffff")]),
                   ["Tall and gaunt, appearing about 60. Long straight white hair tied at the nape.",
                    "Colorless pale-gray eyes and a thin gold circlet.",
                    "Immaculate white high-collared robes embroidered with gold Tally sigils.",
                    "<b>White gloves that never come off.</b> Arc 1 shows only the gloved hand."]))
    S.append(sheet(9, "MIRIAM & LILY REED", None, "Jonah's mother (the game designer) · Jonah's little sister (4 at the funeral, 17 now)", "#f2c230",
                   stage([fig_entry("miriam", "miriam", "MIRIAM · late 30s", rim="#ffd56b"), fig_entry("lily4", "lily4", "LILY · 4")], w_each=400, glow="#a8802a"),
                   bust("miriam", dict(mouth="smile"), dict(rim="#ffd56b", shade="#4a3a2a"), "#a8802a"),
                   [expr_card("lily4", '"Are you crying?"', dict(welling=True, mouth="o", brow="worried"), panels.RAIN),
                    expr_card("lily17", "Lily · 17 (Earth)", dict(mouth="flat", brow="worried")),
                    expr_card("miriam", '"Bugs are secret doors."', dict(mouth="smile", eyes="half"))],
                   palette([("Miriam hair", "#3b2a21"), ("cardigan", "#d9ccb2"), ("pencil", "#e7b84a"), ("Lily hair", "#a77a52"), ("raincoat", "#f2c230")]),
                   ["Miriam: warm brown eyes, dark hair in a loose bun with a pencil stuck through it, an oversized oatmeal cardigan and an ink smudge on one cheek.",
                    "In the game's pixel art she's a 12×11 sprite, and <b>the pencil is in that sprite too</b>.",
                    "Lily at 4: light-brown pigtails with red ties and a yellow raincoat, the only warm color at the funeral.",
                    "Lily at 17: on Earth, holding an unread text."], wide=True))
    beasts = [(G(human_silhouette(400, "#2a2440"), 0, 965), 1.0, "HUMAN · 1.7 m"), (G(murmur(1.0), 0, 965), 1.2, "MURMUR"), (G(wail(1.0), 0, 965), 1.1, "WAIL"),
              (G(dirge(1.0), 0, 965), 1.35, "DIRGE"), (G(lament(1.0), 0, 965), 1.0, "LAMENT")]
    S.append(sheet(10, "WRACKS & CRUMB", "bestiary", "Monsters of the Spill: they hunt feeling, not sight · plus one very small friend", "#c9a5ff",
                   stage(beasts, w_each=330, top=-60, glow="#6a3ab0"),
                   svg("-80 -96 160 110", rglow(0, -26, 90, "#8a5cff", .4) + crumb(1.7), "bust"),
                   [f'<figure class="ex">{svg("-60 -80 120 100", rglow(0, -26, 70, "#8a5cff", .3) + crumb(1.6, True))}<figcaption>Crumb, scared ("mip")</figcaption></figure>',
                    expr_card("maren", "Maren Adair (Ch 10)", dict(mouth="smile")),
                    f'<figure class="ex">{svg("-60 -60 120 120", rglow(0, 0, 60, "#8a5cff", .5) + knot(0, 0, 26, seed=3))}<figcaption>A Knot</figcaption></figure>'],
                   palette([("smoke", "#100a18"), ("core", "#a673ff"), ("mask", "#ece8e2"), ("bone", "#d8cfe0"), ("Crumb eyes", "#ffffff")]),
                   ["<b>Murmur</b> (about Tinder): dog-sized, made of smoke and oily flesh, with no eyes. A row of whispering mouths runs along its flanks.",
                    "<b>Wail</b> (about Kindle): a heron-necked pack hunter with a white screaming mask.",
                    "<b>Dirge</b> (about Taper to Lantern): a sludge giant with a cage-ribcage and dangling hands. It kills whole squads.",
                    "<b>Lament</b> (about Beacon): a veiled weeping tower of black water with a faded red thread at its throat. Hint for Ch 10.",
                    "<b>Crumb</b>: a palm-sized puff of black mist with two white dot eyes and four stubby legs. Afraid of everything."], wide=True))
    return '<section id="cast" class="cast"><h2 class="sec-h">CHARACTER DESIGN · ARC 1 CAST</h2><p class="sec-sub">Every character, creature and prop below is drawn in code as vector art. Colors and features match the series bible.</p>' + "".join(S) + "</section>"

# ------------------------------------------------------------------ chapter

def letter(l):
    t = l["t"]
    pos = f'left:{l.get("x", 0)}%;top:{l.get("y", 0)}%;width:{l.get("w", 30)}%'
    if t == "cap":
        return f'<div class="lt cap {l.get("style", "")}" style="{pos}">{esc(l["text"])}</div>'
    if t == "bub":
        tail = l.get("tail")
        tc = f" tail-{tail}" if tail else ""
        return f'<div class="lt bub {l.get("style", "")}{tc}" style="{pos};--tx:{l.get("tx", 30)}%"><span>{esc(l["text"])}</span></div>'
    if t == "chat":
        rows = "".join(f'<p><b style="color:{c}">{esc(n)}</b> {esc(m)}</p>' for n, m, c in l["rows"])
        return f'<div class="lt chat {l.get("style", "")}" style="{pos}">{rows}</div>'
    if t == "burst":
        return "".join(f'<div class="lt burst" style="left:{x}%;top:{y}%;--fs:{fs / 8:.2f}cqw;color:{c}">{esc(txt)}</div>' for txt, x, y, fs, c in l["items"])
    if t == "monster":
        return f'<div class="lt monster" style="{pos}">{esc(l["text"])}</div>'
    if t == "whisper":
        return f'<div class="lt whisper" style="{pos}">{esc(l["text"])}</div>'
    if t == "pix":
        return f'<div class="lt pix" style="{pos}">{esc(l["text"])}</div>'
    return ""


def chapter():
    out = ['<section id="ch1" class="chapter"><div class="ch-card"><div class="ch-arc">ARC 1 · UNLIT</div><div class="ch-no">CHAPTER 1</div><h2>THE ANNIVERSARY RUN</h2><div class="ch-rule"></div></div>']
    n = 0
    for p in panels.build():
        if "gutter" in p:
            out.append(f'<div class="gut{" fade" if p.get("fade") else ""}" style="aspect-ratio:800/{p["gutter"]}"></div>')
            continue
        n += 1
        lts = "".join(letter(l) for l in p["L"])
        out.append(f'<figure class="pn {p.get("cls", "")}" id="p{n}" style="aspect-ratio:800/{p["h"]}">{svg(f"0 0 800 {p["h"]}", p["svg"])}{lts}<span class="pno">P{n}</span></figure>')
    out.append('''<div class="ch-end"><div class="ch-rule"></div><p class="end1">END OF CHAPTER 1</p><p class="end2">Next: <b>Chapter 2 · Silt</b><br>Wracks hunt emotion. One moment of panic will nearly kill him.</p></div></section>''')
    return "".join(out)


CSS = open("comic.css").read()
FONTS = open("fonts/fonts.css").read()
parts = []
if ONLY in (None, "cover"):
    parts.append(cover())
if ONLY in (None, "cast"):
    parts.append(cast())
if ONLY in (None, "ch1"):
    parts.append(chapter())
page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>UNWEPT · Arc 1 · Chapter 1</title><style>{FONTS}</style><style>{CSS}</style></head>
<body><div class="topbar"><a class="logo" href="#cover">UNWEPT</a><nav><a href="#cast">Cast</a><a href="#ch1">Ch 1</a></nav><div class="prog"><i id="bar"></i></div></div>
{SHARED_DEFS}
<main>{"".join(parts)}</main>
<footer class="foot">UNWEPT · original series · all art hand-coded as vector illustration · Arc 1, Unit 1</footer>
<script>(function(){{var b=document.getElementById('bar');function f(){{var h=document.documentElement,m=h.scrollHeight-h.clientHeight;b.style.width=(m>0?h.scrollTop/m*100:0)+'%';}}addEventListener('scroll',f,{{passive:true}});f();}})();</script>
</body></html>'''
open(OUT, "w").write(page)
print("wrote", OUT, len(page))
