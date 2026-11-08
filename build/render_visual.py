"""Writes the documents that need eyes: a born-digital catalogue whose key facts sit in figures,
a contract PDF, and scans and photos of handwriting and print (OCR or vision required)."""

import io
import math
import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager
from matplotlib.patches import FancyBboxPatch
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image as RLImage, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import calc as C
from world import *  # noqa: F403

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "corpus"
TMP = HERE / "_tmp"
TMP.mkdir(exist_ok=True)
FONTS = HERE / "fonts"
MPL = Path(matplotlib.get_data_path()) / "fonts/ttf"
SANS, SANS_B, MONO = MPL / "DejaVuSans.ttf", MPL / "DejaVuSans-Bold.ttf", MPL / "DejaVuSansMono.ttf"
rng = random.Random(11)
nrng = np.random.default_rng(11)


def font(path, size):
    return ImageFont.truetype(str(path), size)


# ------------------------------------------------------------------ image helpers
def hand_lines(img, lines, x, y, fnt_path, size, line_h, ink=(25, 35, 90), jitter=2.5, slant=0.0, strike=None):
    """Draws handwriting word by word, each word slightly offset, scaled and rotated."""
    strike = strike or {}
    for li, line in enumerate(lines):
        cx = x + rng.uniform(-6, 6)
        cy = y + li * line_h + rng.uniform(-2, 2)
        for wi, word in enumerate(line.split(" ")):
            if not word:
                cx += size * .35
                continue
            fsz = int(size * rng.uniform(.93, 1.07))
            f = font(fnt_path, fsz)
            bbox = f.getbbox(word)
            wimg = Image.new("RGBA", (bbox[2] + 20, int(fsz * 1.8)), (0, 0, 0, 0))
            ImageDraw.Draw(wimg).text((10, int(fsz * .2)), word, font=f, fill=ink + (235,))
            if (li, wi) in strike:
                dw = ImageDraw.Draw(wimg)
                for k in range(2):
                    yy = int(fsz * .2 + fsz * .55) + k * 3
                    dw.line((6, yy + rng.randint(-2, 2), bbox[2] + 14, yy + rng.randint(-2, 2)), fill=ink + (255,), width=3)
            wimg = wimg.rotate(rng.uniform(-jitter, jitter) + slant, resample=Image.BICUBIC, expand=True)
            img.alpha_composite(wimg, (int(cx), int(cy + rng.uniform(-jitter, jitter))))
            cx += bbox[2] + size * rng.uniform(.28, .42)


def scan(img, angle=0.8, noise=9, blur=.7, gray=True, vignette=.12, stains=0):
    img = img.convert("RGB")
    if stains:
        d = ImageDraw.Draw(img, "RGBA")
        for _ in range(stains):
            cx, cy, r = rng.randint(100, img.width - 100), rng.randint(100, img.height - 100), rng.randint(60, 140)
            for k in range(6):
                d.ellipse((cx - r + k * 3, cy - r + k * 2, cx + r - k * 2, cy + r - k * 3), outline=(150, 110, 60, 40), width=5)
    img = img.rotate(angle, resample=Image.BICUBIC, expand=True, fillcolor=(40, 40, 40))
    a = np.asarray(img).astype(np.float32)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    v = 1 - vignette * (((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2)
    a = a * v[..., None] + nrng.normal(0, noise, a.shape)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
    return img.convert("L") if gray else img


def paper(w, h, lined=False, tint=(250, 248, 240), margin=False):
    img = Image.new("RGBA", (w, h), tint + (255,))
    d = ImageDraw.Draw(img)
    if lined:
        for y in range(220, h - 60, 64):
            d.line((0, y, w, y), fill=(170, 195, 225, 255), width=2)
    if margin:
        d.line((150, 0, 150, h), fill=(225, 140, 140, 255), width=2)
    return img


def save_jpg(img, path, q=72):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p, "JPEG", quality=q)


def images_to_pdf(imgs, path):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    rgb = [i.convert("RGB") for i in imgs]
    rgb[0].save(p, "PDF", resolution=150, save_all=True, append_images=rgb[1:])


# ------------------------------------------------------------------ field notes (handwritten scan)
FIELD_PAGES = [
    ["BARGE 2 - proto P3 - field test log", "L. Ferrand", "Annecy / Bauges loops. Rider 62 kg + sandbags",
     "", "Day 1 - Tue 10 June - 18°C, dry", "42 km, flat lake road, total load 120 kg",
     "Battery 100 -> 61 %. No issues. Steering light,", "box stable even at 35 km/h.",
     "", "Day 2 - Wed 11 June - 24°C", "51 km. Two descents of the Semnoz. On the 2nd",
     "descent slight squeal from rear brake, no fade,", "braking OK. Battery 100 -> 38 %"],
    ["Day 3 - Thu 12 June - 27°C, storm in evening", "38 km, load 180 kg. Col de Leschaux descent:",
     "BRAKE FADE (1st) - front. Lever to the bar,", "stopped 10 min to cool. Pads glazed.",
     "Rest of the day very careful.", "", "Day 4 - Fri 13 June - workshop day, 0 km",
     "Jonas fitted 4-piston front caliper + 220 mm rotor", "(was 2-piston / 203 mm). New pads both ends.",
     "Rear unchanged (2-piston, 180 mm)."],
    ["Day 5 - Sat 14 June - 31°C (hottest)", "58 km, load 200 kg. Long climb Col du Frêne:",
     "motor thermal derate after 28 min, power ~60 %.", "Recovered after 6 min stop. Battery 100 -> 9 % (!)",
     "", "Sun 15 June - no ride", "", "Day 6 - Mon 16 June - 22°C, cloudy",
     "47 km, load 180 200 kg. Long descent to Faverges:", "fade again - REAR this time. Front 4-pot perfect.",
     "", "Day 7 - Tue 17 June - 19°C", "33 km easy, 120 kg. Summary for Jonas:",
     "- rear needs 203 mm rotor too", "- derate: check firmware temp limit",
     "- range at 200 kg in heat way below the 120 km claim"],
]


def field_notes():
    pages = []
    fonts = [FONTS / "HomemadeApple-Regular.ttf", FONTS / "ReenieBeanie.ttf", FONTS / "HomemadeApple-Regular.ttf"]
    sizes = [30, 46, 30]
    for i, lines in enumerate(FIELD_PAGES):
        img = paper(1240, 1754, lined=True, margin=True)
        strike = {(8, 3): True} if i == 2 else {}
        hand_lines(img, lines, 175, 150, fonts[i], sizes[i], 64 * 1.5 if i != 1 else 64 * 1.5, jitter=3, strike=strike)
        d = ImageDraw.Draw(img)
        d.text((1080, 1680), f"p.{i + 1}", font=font(FONTS / "Caveat.ttf", 34), fill=(60, 60, 60, 255))
        pages.append(scan(img, angle=rng.uniform(-1.6, 1.6), noise=11, blur=.9, stains=1 if i == 1 else 0))
    images_to_pdf(pages, "operations/field_test_notes_barge2_P3.pdf")


# ------------------------------------------------------------------ whiteboard photo
def whiteboard():
    W, H = 1800, 1200
    img = Image.new("RGBA", (W, H), (236, 238, 236, 255))
    d = ImageDraw.Draw(img)
    for i in range(H):  # glare gradient
        c = int(236 + 14 * math.exp(-((i - 300) / 260) ** 2))
        d.line((0, i, W, i), fill=(c, c, min(255, c + 2), 255))
    m = FONTS / "PermanentMarker-Regular.ttf"
    hand_lines(img, ["Q4 PRIORITIES  (ops + sales sync 6/10)"], 120, 70, m, 54, 70, ink=(30, 60, 160), jitter=1.5)
    items = ["1. Barge 2 ramp -> 150 / month by Dec  - MO",
             "2. Utrecht hub live 17/11  - KB",
             "3. VL-2507-B claims: get the € back from Voltaris  - CD + NK",
             "4. +6 dealers NL/BE  - CM",
             "5. Black Friday webshop -10 %  (24/11 -> 1/12)  - LF",
             "6. Trike: kill or keep?  -> Dec board  - IM"]
    inks = [(20, 20, 20), (20, 20, 20), (170, 30, 30), (20, 20, 20), (20, 110, 60), (20, 20, 20)]
    for k, (t, ink) in enumerate(zip(items, inks)):
        hand_lines(img, [t], 140, 210 + k * 140, m, 40, 70, ink=ink, jitter=2)
    d.ellipse((1500, 860, 1700, 1000), outline=(30, 60, 160, 255), width=6)
    hand_lines(img, ["no!"], 1550, 900, m, 38, 50, ink=(30, 60, 160))
    img = img.convert("RGB")
    # perspective-ish skew, frame, photo noise
    img = img.transform((W, H), Image.QUAD, (40, 10, 0, H - 30, W - 10, H, W - 60, 40), resample=Image.BICUBIC, fillcolor=(90, 85, 80))
    photo = scan(img, angle=-1.2, noise=6, blur=1.1, gray=False, vignette=.25)
    save_jpg(photo, "operations/whiteboard_q4_priorities.jpg", q=65)


# ------------------------------------------------------------------ customer letter (French, handwritten)
def customer_letter():
    img = paper(1240, 1754, tint=(252, 251, 247))
    f = FONTS / "Kalam-Regular.ttf"
    lines = [
        f"{LETTER_NAME}", "7 rue Lakanal", "38000 Grenoble", "", "                                  Grenoble, le 3 novembre 2025",
        "", "Arvenne Cycles - Service client", "", "Madame, Monsieur,", "",
        "J'ai acheté un vélo Arvenne Mule le 9 août 2025 chez",
        "Cycles du Dauphiné à Grenoble (numéro de série",
        f"{C.LETTER_SERIAL}, gravé sous le pédalier).",
        "Le 28 octobre, après une recharge, le connecteur de la",
        "batterie a fondu et il y avait une odeur de brûlé. Le vélo",
        "ne démarre plus. J'ai dû prendre un taxi pour aller chercher",
        f"mes enfants à l'école : {LETTER_TAXI} €, reçu joint.",
        "", "Je vous demande de remplacer le connecteur au plus vite",
        "et de me rembourser le taxi. Je précise que je recharge",
        "toujours avec le chargeur d'origine.", "",
        "Je vous prie d'agréer mes salutations distinguées.", "", "                                   M. Leclerc",
    ]
    hand_lines(img, lines, 120, 110, f, 34, 58, ink=(20, 30, 110), jitter=1.8)
    save_jpg(scan(img, angle=.9, noise=7, blur=.6, gray=False), "support/customer_letter_leclerc.jpg", q=70)


# ------------------------------------------------------------------ hotel receipt (photo)
def receipt():
    W, H = 760, 1120
    img = Image.new("RGBA", (W, H), (248, 246, 240, 255))
    d = ImageDraw.Draw(img)
    mono, mono_b = font(MONO, 24), font(MONO, 30)
    y = 40
    def line(t, f=mono, center=False):
        nonlocal y
        x = (W - d.textlength(t, font=f)) / 2 if center else 40
        d.text((x, y), t, font=f, fill=(40, 40, 40, 255))
        y += f.size + 12
    line("HOTEL LIMMATBLICK", mono_b, True)
    line("Limmatquai 112 · 8001 Zürich", center=True)
    line("MWST CHE-417.250.881", center=True)
    line("")
    line("Rechnung / Invoice  25-10-4471")
    line("Gast:  Hr. Felix Hartmann")
    line("Firma: Arvenne Cycles SAS, Lyon")
    line("Zimmer 312 · Einzel / single")
    line("Ankunft 14.10.2025  Abreise 16.10.2025")
    line("Frühstück inbegriffen")
    line("-" * 44)
    rows = [("14.10", "Zimmer / room", ZURICH_ROOM_CHF), ("14.10", "City Tax", ZURICH_TAX_CHF),
            ("15.10", "Zimmer / room", ZURICH_ROOM_CHF), ("15.10", "City Tax", ZURICH_TAX_CHF),
            ("15.10", "Minibar", 9.00)]
    for dte, lab, amt in rows:
        line(f"{dte}  {lab:<22}{amt:>10.2f}")
    line("-" * 44)
    total = 2 * ZURICH_ROOM_CHF + 2 * ZURICH_TAX_CHF + 9
    line(f"TOTAL CHF {total:>16.2f}", mono_b)
    line("")
    line("inkl. MWST 3.8 % Beherbergung     17.43")
    line("inkl. MWST 8.1 % Minibar           0.67")
    line("")
    line("Bezahlt VISA ****4417  16.10.2025 08:12")
    line("Vielen Dank für Ihren Besuch!", center=True)
    img = img.convert("RGB")
    canvas = Image.new("RGB", (W + 260, H + 200), (92, 74, 58))  # wooden desk
    canvas.paste(img, (130, 100))
    canvas = canvas.rotate(3.5, resample=Image.BICUBIC, fillcolor=(92, 74, 58))
    save_jpg(scan(canvas, angle=0, noise=8, blur=.8, gray=False, vignette=.3), "finance/expense_receipt_hartmann_zurich.jpg", q=68)


# ------------------------------------------------------------------ delivery note (scanned print)
def delivery_note():
    W, H = 1240, 1754
    img = Image.new("RGBA", (W, H), (253, 253, 251, 255))
    d = ImageDraw.Draw(img)
    s, b, big = font(SANS, 24), font(SANS_B, 26), font(SANS_B, 44)
    d.text((80, 80), "VOLTARIS", font=big, fill=(10, 60, 120, 255))
    d.text((80, 135), "Voltaris Energiesysteme GmbH · Annaberger Str. 240 · 09125 Chemnitz", font=s, fill=(60, 60, 60, 255))
    d.text((80, 240), "LIEFERSCHEIN / DELIVERY NOTE", font=b, fill=(0, 0, 0, 255))
    info = [("Nr.", "LS-25-08841"), ("Datum / Date", "27.08.2025"), ("Bestellung / PO", "4500-2291"),
            ("Charge / Lot", LATE_LOT), ("Empfänger", "Arvenne Cycles SAS, Werk Villefranche-sur-Saône")]
    for k, (a, v) in enumerate(info):
        d.text((80, 300 + k * 44), a, font=s, fill=(0, 0, 0, 255))
        d.text((420, 300 + k * 44), v, font=b if a == "Charge / Lot" else s, fill=(0, 0, 0, 255))
    y = 560
    d.rectangle((80, y, W - 80, y + 50), outline=(0, 0, 0, 255), width=2)
    for x, t in [(95, "Pos."), (190, "Artikel / Item"), (700, "Menge / Qty"), (900, "Paletten")]:
        d.text((x, y + 12), t, font=b, fill=(0, 0, 0, 255))
    rows = [("1", "VP-625  Akkupack 48 V 625 Wh", LATE_LOT_PACKS["VP-625"], 6),
            ("2", "VP-750  Akkupack 48 V 750 Wh", LATE_LOT_PACKS["VP-750"], 10)]
    for k, (p, it, q, pal) in enumerate(rows):
        yy = y + 50 + k * 50
        d.rectangle((80, yy, W - 80, yy + 50), outline=(0, 0, 0, 255), width=1)
        for x, t in [(95, p), (190, it), (700, str(q)), (900, str(pal))]:
            d.text((x, yy + 12), t, font=s, fill=(0, 0, 0, 255))
    d.text((80, y + 200), "Gefahrgut UN3480 · Lithium-Ionen-Batterien · Klasse 9", font=s, fill=(0, 0, 0, 255))
    d.text((80, 1350), "Ware erhalten / Goods received:", font=s, fill=(0, 0, 0, 255))
    # stamp
    st = Image.new("RGBA", (520, 220), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rounded_rectangle((6, 6, 514, 214), 18, outline=(190, 30, 40, 200), width=7)
    sd.text((40, 30), "ARVENNE · VILLEFRANCHE", font=font(SANS_B, 32), fill=(190, 30, 40, 200))
    sd.text((40, 85), "RECEIVED  27 AUG 2025", font=font(SANS_B, 38), fill=(190, 30, 40, 200))
    sd.text((40, 150), "Goods-in · Quai 2", font=font(SANS, 28), fill=(190, 30, 40, 200))
    img.alpha_composite(st.rotate(-7, expand=True, resample=Image.BICUBIC), (560, 1180))
    hand_lines(img, ["K. Benali", "4 x VP-750 dented -> quarantine"], 120, 1420, FONTS / "GochiHand-Regular.ttf", 40, 64,
               ink=(15, 25, 100), jitter=2)
    pg = scan(img, angle=-1.1, noise=10, blur=.8)
    images_to_pdf([pg], "suppliers/voltaris_delivery_note_VL-2508-C.pdf")


# ------------------------------------------------------------------ org chart
def org_chart():
    fig, ax = plt.subplots(figsize=(20, 9), dpi=110)
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 9)
    ax.axis("off")
    pos = {"Inès Marchetti": (10, 8)}
    heads = ["Tomasz Wielgosz", "Camille Dufresne", "Mathieu Okafor", "Ruth Achterberg", "Léa Fontaine"]
    hx = [2.2, 6.1, 10, 14.1, 18]
    for n, x in zip(heads, hx):
        pos[n] = (x, 6)
    reports = {h: [p for p, (t, m, dep) in PEOPLE.items() if m == h] for h in heads}
    for h, x in zip(heads, hx):
        for k, p in enumerate(reports[h]):
            pos[p] = (x, 4.4 - k * 1.05)
    pos["Lucie Ferrand"] = (pos["Jonas Eberhardt"][0] + .55, pos["Jonas Eberhardt"][1] - 1.05)
    # shift Lucie below Jonas: Jonas is 2nd report of Tomasz
    for p, (x, y) in pos.items():
        t, m, dep = PEOPLE[p]
        if not m:
            continue
        mx, my = pos[m]
        if m == "Inès Marchetti":
            ax.plot([mx, mx, x, x], [my - .35, (my + y) / 2 + .1, (my + y) / 2 + .1, y + .35], color="#777", lw=1.2)
        elif PEOPLE[m][1] != "Inès Marchetti":  # second level: indented, straight down from the manager
            ax.plot([mx - 3.3 / 2 + .3, mx - 3.3 / 2 + .3, x - 3.3 / 2], [my - .35, y, y], color="#777", lw=1.2)
        else:  # side rail on the left of the column, elbow into each box
            rail = mx - 3.3 / 2 - .18
            ax.plot([mx - 3.3 / 2 + .2, mx - 3.3 / 2 + .2, rail, rail, x - 3.3 / 2], [my - .35, my - .5, my - .5, y, y], color="#777", lw=1.2)
    for p, (x, y) in pos.items():
        t = PEOPLE[p][0]
        w = 3.3
        ax.add_patch(FancyBboxPatch((x - w / 2, y - .35), w, .7, boxstyle="round,pad=0.02",
                                    fc="#eef3f7" if PEOPLE[p][1] != "Inès Marchetti" else "#d8e6dd", ec="#4a5a68"))
        ax.text(x, y + .1, p, ha="center", va="center", fontsize=11, weight="bold")
        ax.text(x, y - .17, t, ha="center", va="center", fontsize=7.8, wrap=True)
    ax.text(.2, .3, "Arvenne Cycles · organisation at 1 October 2025 · HR", fontsize=9, color="#555")
    p = OUT / "hr/org_chart_2025.png"
    fig.savefig(p, bbox_inches="tight")
    plt.close(fig)


# ------------------------------------------------------------------ catalogue figures
def battery_diagram(path):
    fig, ax = plt.subplots(figsize=(11, 5.2), dpi=160)
    ax.set_xlim(0, 22)
    ax.set_ylim(0, 10)
    ax.axis("off")
    def box(x, y, w, h, title, sub, fc="#f4f1ea"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08", fc=fc, ec="#333", lw=1.4))
        ax.text(x + w / 2, y + h * .64, title, ha="center", va="center", fontsize=9.5, weight="bold")
        ax.text(x + w / 2, y + h * .3, sub, ha="center", va="center", fontsize=8.5)
    def arrow(x1, y1, x2, y2, label=""):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="-|>", lw=1.6, color="#333"))
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + .5, label, ha="center", fontsize=8.5, color="#a33")
    box(.4, 6.2, 4.6, 2.4, "Main pack", "13S4P · 21700 cells\n46.8 V nominal · 750 Wh")
    box(.2, 1.4, 5.0, 2.4, "Range Extender (option)", "13S3P · 21700 cells\n46.8 V · ~500 Wh", fc="#eaf1f4")
    box(6.6, 3.9, 3.2, 2.2, "Diode isolation", "module DM-2\n(prevents cross-charging)")
    box(11.2, 3.9, 2.6, 2.2, "BMS", "per pack,\ncell balancing")
    box(15.0, 3.9, 2.8, 2.2, "Controller", "48 V · 22 A peak")
    box(19.0, 3.9, 2.6, 2.2, "Motor", "mid-drive 90 Nm\n250 W rated")
    arrow(5.0, 7.4, 6.6, 5.6, "XT90-S")
    arrow(5.0, 2.6, 6.6, 4.4, "XT60")
    arrow(9.8, 5.0, 11.2, 5.0)
    arrow(13.8, 5.0, 15.0, 5.0, "fuse 30 A")
    arrow(17.8, 5.0, 19.0, 5.0)
    box(11.0, .6, 3.4, 1.8, "Charge port", "4 A charger\n(main pack only)", fc="#fff")
    arrow(11.6, 2.4, 3.6, 6.2)
    box(15.0, 7.6, 3.4, 1.6, "Display / HMI", "CAN bus", fc="#fff")
    ax.plot([16.5, 16.5], [7.6, 6.1], color="#333", lw=1.2, ls="--")
    ax.text(.4, 9.5, "Figure 3 · Barge 2 power architecture", fontsize=12, weight="bold")
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


RANGE_POINTS = {"Eco": [(100, 120), (150, 104), (200, 88), (260, 71)],
                "Tour": [(100, 92), (150, 76), (200, 60), (260, 48)],
                "Boost": [(100, 68), (150, 56), (200, 45), (260, 36)]}


def range_chart(path):
    fig, ax = plt.subplots(figsize=(8, 4.6), dpi=160)
    styles = {"Eco": ("#2f6f5e", "-"), "Tour": ("#c27b1a", "--"), "Boost": ("#9b2d30", ":")}
    for mode, pts in RANGE_POINTS.items():
        xs, ys = zip(*pts)
        ax.plot(xs, ys, styles[mode][1], marker="o", color=styles[mode][0], label=mode, lw=2)
        for x, y in pts:
            ax.annotate(f"{y}", (x, y), textcoords="offset points", xytext=(0, 7), ha="center", fontsize=8)
    ax.set_xlabel("Total load, rider + cargo (kg)")
    ax.set_ylabel("Range (km), 750 Wh main pack")
    ax.set_title("Figure 4 · Barge 2 range by load and assistance mode (flat route, 20°C)")
    ax.set_xticks([100, 150, 200, 260])
    ax.legend(frameon=False)
    ax.grid(alpha=.3)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def catalogue():
    battery_diagram(TMP / "battery.png")
    range_chart(TMP / "range.png")
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=10, leading=14)
    h1, h2 = ss["Title"], ss["Heading2"]
    ts = TableStyle([("FONT", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                     ("GRID", (0, 0), (-1, -1), .4, colors.grey), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e5ece8")),
                     ("VALIGN", (0, 0), (-1, -1), "MIDDLE")])
    st = []
    st += [Spacer(1, 6 * cm), Paragraph("ARVENNE", h1), Paragraph("Cargo bikes · Catalogue 2025, autumn edition", h2),
           Paragraph("Published September 2025. Prices valid from 1 October 2025 until further notice.", body), PageBreak()]
    st += [Paragraph("The range", h2)]
    rows = [["Model", "Type", "Motor", "Battery", "Range", "Max total load", "Bike weight", "RRP incl. VAT (FR)"]]
    for m, p in PRODUCTS.items():
        price = f"€{p.get('rrp_after', p['rrp']):,}"
        if m == "Barge":
            price += "*"
        if m == "Barge 2":
            price += "**"
        rows.append([m, Paragraph(p["kind"], body), p["motor"], f"{p['battery_wh']} Wh",
                     f"{p['range_km'][0]}-{p['range_km'][1]} km", f"{p['max_load']} kg", f"{p['weight']} kg", price])
    st += [Table(rows, colWidths=[1.6 * cm, 3.2 * cm, 2.8 * cm, 1.6 * cm, 1.9 * cm, 2.1 * cm, 1.8 * cm, 2.6 * cm], style=ts),
           Spacer(1, .3 * cm),
           Paragraph("* First-generation Barge: end of sale 30 September 2025, remaining stock at dealers while it lasts. "
                     "** Barge 2: available from 1 October 2025.", body),
           Spacer(1, .4 * cm),
           Paragraph("Range is measured on a flat route at 20°C. The upper figure is in Eco mode with a total load of 100 kg, "
                     "the lower figure in Tour mode with a total load of 200 kg. Max total load includes the rider.", body),
           PageBreak()]
    st += [Paragraph("Barge 2 in depth", h2),
           Paragraph("A new aluminium frame, a lower box and a 750 Wh battery as standard. The optional Range Extender "
                     "adds a second pack under the box floor. The architecture below shows how the two packs are combined: "
                     "each pack keeps its own BMS, and the main pack is the only one charged through the charge port.", body),
           Spacer(1, .3 * cm), RLImage(str(TMP / "battery.png"), width=17 * cm, height=8.0 * cm), Spacer(1, .3 * cm),
           RLImage(str(TMP / "range.png"), width=15 * cm, height=8.6 * cm), PageBreak()]
    acc = [["Accessory", "Fits", "RRP incl. VAT"], ["Range Extender ~500 Wh", "Barge 2 only", f"€{RANGE_EXTENDER_PRICE}"],
           ["Child bench with 3 harnesses", "Barge 2", "€249"], ["Rain cover", "Barge, Barge 2", "€189"],
           ["Rear child seat", "Mule", "€139"], ["Pannier pair 2 x 25 l", "Mule, Pup", "€119"],
           ["Front basket", "Pup", "€89"], ["Trike bench kit (2 children)", "Trike", "€279"]]
    st += [Paragraph("Accessories", h2), Table(acc, colWidths=[6 * cm, 4 * cm, 3 * cm], style=ts), Spacer(1, .8 * cm)]
    exp = [["Model", "Switzerland (CHF, excl. VAT)", "United Kingdom (GBP, excl. VAT)"]]
    for m, p in PRODUCTS.items():
        exp.append([m, f"{p.get('chf_after', p['chf']):,}", f"{p.get('gbp_after', p['gbp']):,}"])
    st += [Paragraph("Export price list", h2), Paragraph("Dealer list prices before tier discount, valid from 1 July 2025.", body),
           Table(exp, colWidths=[3 * cm, 6 * cm, 6 * cm], style=ts), Spacer(1, .8 * cm)]
    st += [Paragraph("Warranty and service", h2),
           Paragraph("Frame: 10 years. Motor, battery and electronics: 2 years (battery: or 800 full cycles). "
                     "First service after 300 km or 3 months. Every bike is built at our plant in Villefranche-sur-Saône "
                     "and carries a serial number engraved under the bottom bracket.", body)]
    doc = SimpleDocTemplate(str(OUT / "products/arvenne_catalogue_2025_autumn.pdf"), pagesize=A4,
                            title="Arvenne catalogue 2025 autumn", author="Arvenne Cycles")
    doc.build(st)


# ------------------------------------------------------------------ supply agreement
def contract():
    ss = getSampleStyleSheet()
    body = ParagraphStyle("b", parent=ss["BodyText"], fontSize=9.6, leading=13.5, spaceAfter=5)
    h = ParagraphStyle("h", parent=ss["Heading3"], spaceBefore=8)
    c = CONTRACT
    st = [Paragraph("BATTERY PACK SUPPLY AGREEMENT", ss["Title"]),
          Paragraph("between <b>Arvenne Cycles SAS</b>, 14 rue des Tanneurs, 69007 Lyon, France (the \"Buyer\"), represented by "
                    "Inès Marchetti, CEO, and <b>Voltaris Energiesysteme GmbH</b>, Annaberger Str. 240, 09125 Chemnitz, Germany "
                    "(the \"Supplier\"), represented by Dr. Heike Brandner, Managing Director. Signed in Lyon on 15 November 2024.", body)]
    clauses = [
        ("1. Definitions", ["\"Business Day\" means Monday to Friday, excluding French public holidays.",
                            "\"Lot\" means all packs delivered under one purchase order and identified by one lot code (VL-YYMM-X).",
                            "\"Battery-related claim\" means a warranty claim on the cells, the BMS, the connectors or the harness of a pack."]),
        ("2. Term", ["This agreement runs from 1 January 2025 to 31 December 2027. It renews for one year at a time unless "
                     "either party gives notice at least six months before the end of the current term."]),
        ("3. Products and prices", ["3.1 Prices in euros, excluding VAT, delivered at the Buyer's plant in Villefranche-sur-Saône (DAP):"]),
        ("4. Volumes", ["4.1 The Buyer sends a rolling six-month forecast each month. 4.2 The Buyer commits to a minimum of 3,000 packs "
                        "per calendar year. Below that volume, prices of clause 3.1 rise by 4% for the following year."]),
        ("5. Orders", ["Purchase orders are placed at least eight weeks before the requested delivery date. The Supplier confirms "
                       "each order and its delivery date in writing within two Business Days. The confirmed date is binding."]),
        ("6. Delivery and acceptance", ["The Buyer inspects each Lot within ten Business Days of delivery. Packs damaged in transport "
                                        "are replaced free of charge within fifteen days."]),
        ("7. Late delivery", [
            f"7.1 The confirmed delivery date of each Lot is binding on the Supplier.",
            f"7.2 For each full week of delay between the confirmed delivery date and the actual delivery date, the Supplier owes a "
            f"penalty of {c['late_pct_per_week']}% of the invoice value of the Lot concerned, up to a maximum of {c['late_cap_pct']:.0f}% of that value.",
            "7.3 Penalties are settled by credit note on the next invoice.",
            f"7.4 Neither party is liable for a delay caused by force majeure (including strikes outside the party's control, natural "
            f"disasters, and decisions of public authorities), provided that the affected party notifies the other party in writing "
            f"within {c['fm_notice_business_days']} Business Days of the start of the event. A party that does not give this notice in time "
            f"cannot invoke force majeure for that event."]),
        ("8. Quality and traceability", ["Each pack carries its Lot code. The Supplier keeps production records for ten years and "
                                         "notifies the Buyer of any process change at least thirty days in advance."]),
        ("9. Warranty", [
            "9.1 Packs are guaranteed for 30 months from delivery.",
            "9.2 The Supplier replaces or credits any pack that fails within the warranty period.",
            "9.3 The Buyer reports field failures monthly with serial numbers and Lot codes.",
            f"9.4 Field failure of a Lot. If, for a given Lot, the number of approved Battery-related claims exceeds "
            f"{c['failure_threshold_pct']:.1f}% of the bikes built with that Lot within 12 months of its delivery, the Supplier reimburses "
            f"100% of the cost of all approved Battery-related claims of that Lot, plus a handling fee of €{c['handling_fee']} per approved claim."]),
        ("10. Payment", [f"Invoices are payable {c['payment_days']} days end of month."]),
        ("11. Liability", ["Except for clause 9.4 and in case of gross negligence, each party's liability is capped at the value of "
                           "purchases made in the previous twelve months."]),
        ("12. Termination", ["Either party may terminate for material breach not cured within thirty days of written notice."]),
        ("13. Law and courts", ["French law applies. Disputes go to the Commercial Court of Lyon."]),
    ]
    ts = TableStyle([("FONT", (0, 0), (-1, 0), "Helvetica-Bold"), ("GRID", (0, 0), (-1, -1), .4, colors.grey), ("FONTSIZE", (0, 0), (-1, -1), 9)])
    for title, paras in clauses:
        st.append(Paragraph(title, h))
        for p in paras:
            st.append(Paragraph(p, body))
        if title.startswith("3."):
            st.append(Table([["Reference", "Description", "Price per pack"]] +
                            [[k, {"VP-500": "48 V 500 Wh (Barge)", "VP-625": "48 V 625 Wh (Mule, Trike)",
                                  "VP-750": "48 V 750 Wh (Barge 2)", "VP-RX500": "48 V ~500 Wh Range Extender"}[k], f"€{v:,.2f}"]
                             for k, v in PACK_PRICES.items()], style=ts))
            st.append(Paragraph("3.2 If the lithium carbonate index moves by more than 15% over a calendar quarter, either party may "
                                "request a price review, which takes effect on the first day of the following quarter.", body))
    st += [Spacer(1, 1 * cm), Paragraph("For the Buyer: Inès Marchetti, CEO &nbsp;&nbsp;&nbsp;&nbsp; For the Supplier: Dr. Heike Brandner, Managing Director", body)]
    SimpleDocTemplate(str(OUT / "suppliers/voltaris_supply_agreement.pdf"), pagesize=A4, title="Battery pack supply agreement").build(st)


def main():
    field_notes()
    whiteboard()
    customer_letter()
    receipt()
    delivery_note()
    org_chart()
    catalogue()
    contract()


if __name__ == "__main__":
    main()
