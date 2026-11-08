"""Writes the born-digital documents: Markdown, text, JSON, HTML, CSV, XLSX, DOCX, PPTX."""

import csv
import json
from datetime import date
from pathlib import Path

import openpyxl
from docx import Document
from docx.shared import Pt
from openpyxl.styles import Font, PatternFill
from pptx import Presentation
from pptx.util import Inches, Pt as PPt

import calc as C
import data as D
from world import *  # noqa: F403

OUT = Path(__file__).resolve().parent.parent / "corpus"
TMP = Path(__file__).resolve().parent / "_tmp"


def w(path, text):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.strip() + "\n", encoding="utf-8")


def eur(x, dec=0):
    return f"€{x:,.{dec}f}"


# ---------------------------------------------------------------- sales
def sales():
    w("sales/README.md", f"""
# Sales data, 2025

Exported from the order system on 5 January 2026 by Hugo Lambert (Financial Controller).

## orders_2025.csv

One row per order line placed between 1 January and 31 December 2025.

| Column | Meaning |
| --- | --- |
| `order_id` | Unique order reference, `SO-25-nnnnn`. |
| `order_date` | Date the order was placed (not the delivery date). |
| `channel` | `Dealer` (sold through an authorised dealer), `Direct` (arvenne.com webshop) or `Fleet` (B2B contract). |
| `country` | Delivery country, ISO code (`UK` is used for the United Kingdom). |
| `dealer_id` | Dealer reference for `Dealer` orders, see `dealers_2025.xlsx`. Empty otherwise. |
| `customer` | Fleet customer name. Empty for other channels. |
| `model` | Model ordered. |
| `quantity` | Bikes on the line. |
| `unit_price` | List price per bike **excluding VAT**, in the order currency, on the order date. |
| `currency` | `EUR`, `CHF` (Switzerland) or `GBP` (United Kingdom). |
| `discount_pct` | Discount off the list price: the dealer's tier discount for dealer orders, the negotiated rebate for fleet orders, promotions for direct orders. |
| `status` | `Delivered`, `Cancelled` (never shipped) or `Returned` (refunded in full). |

## Definitions used in every report

- **Net revenue** of a line = `quantity × unit_price × (1 − discount_pct / 100)`, in the order currency.
- Revenue and unit figures count **Delivered** lines only. Cancelled and Returned lines count as zero.
- Amounts in CHF and GBP are converted to euros with the budget exchange rates (Finance, `budget_2025.xlsx`, sheet *Assumptions*), dividing the local amount by the rate.
- The webshop sells only to France, Germany, the Netherlands and Belgium. Switzerland, the United Kingdom and Austria are served by dealers and fleet contracts.
- Fleet contracts are managed by Ben Whitaker.
""")
    cols = ["order_id", "order_date", "channel", "country", "dealer_id", "customer", "model", "quantity",
            "unit_price", "currency", "discount_pct", "status"]
    p = OUT / "sales/orders_2025.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(cols)
        for r in C.ORDERS:
            wr.writerow([r["order_id"], r["order_date"].isoformat(), r["channel"], r["country"], r["dealer_id"],
                         r["customer"], r["model"], r["quantity"], f"{r['unit_price']:.2f}", r["currency"],
                         r["discount_pct"], r["status"]])

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Dealers"
    hdr(ws, ["dealer_id", "name", "city", "country", "tier", "onboarded", "status", "account_manager"])
    for did, name, city, c, tier, onb, status in DEALERS:
        ws.append([did, name, city, c, tier, date.fromisoformat(onb), status, ACCOUNT_MANAGER[c]])
    for row in ws.iter_rows(min_row=2, min_col=6, max_col=6):
        row[0].number_format = "yyyy-mm-dd"
    ws2 = wb.create_sheet("Targets 2025")
    hdr(ws2, ["dealer_id", "target_units_2025", "note"])
    for did, *_ in DEALERS:
        note = "Pro-rated, onboarded in Q4" if C.TARGETS[did] == 10 else ""
        ws2.append([did, C.TARGETS[did], note])
    ws3 = wb.create_sheet("Tier terms")
    hdr(ws3, ["tier", "discount_pct", "payment_terms_days", "coop_marketing_budget_eur", "demo_fleet_bikes"])
    ws3.append(["Gold", 30, 60, 4000, 4])
    ws3.append(["Silver", 27, 45, 2000, 2])
    ws3.append(["Bronze", 25, 30, 750, 1])
    autosize(wb)
    wb.save(OUT / "sales/dealers_2025.xlsx")


def hdr(ws, cols):
    ws.append(cols)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.fill = PatternFill("solid", fgColor="DDE7F0")


def autosize(wb):
    for ws in wb.worksheets:
        for col in ws.columns:
            width = max(len(str(c.value)) if c.value is not None else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(48, max(10, width + 2))


# ---------------------------------------------------------------- operations
def operations():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Batches"
    hdr(ws, ["batch_id", "model", "line", "start_date", "units", "serial_from", "serial_to", "battery_supplier", "battery_lot"])
    for b in C.BATCHES:
        ws.append([b["batch_id"], b["model"], b["line"], b["start_date"], b["units"], D.sn(b["serial_from"]),
                   D.sn(b["serial_to"]), b["battery_supplier"], b["battery_lot"]])
    for row in ws.iter_rows(min_row=2, min_col=4, max_col=4):
        row[0].number_format = "yyyy-mm-dd"
    ws2 = wb.create_sheet("Lines")
    hdr(ws2, ["line", "models", "shifts", "takt_time_min", "notes"])
    ws2.append(["A", "Mule, Pup", 2, 14, "Longtails and compacts"])
    ws2.append(["B", "Barge, Barge 2, Trike", 2, 22, "Front-loaders and trikes; third shift from 2026"])
    ws2.append(["(plant)", "", "", "", "Summer closure 4-17 August 2025"])
    autosize(wb)
    wb.save(OUT / "operations/production_batches_2025.xlsx")

    with (OUT / "operations/warranty_claims_2025.csv").open("w", newline="", encoding="utf-8") as f:
        wr = csv.writer(f)
        wr.writerow(["claim_id", "claim_date", "serial_number", "model", "component", "description", "cost_eur", "status"])
        for c in C.CLAIMS:
            wr.writerow([c["claim_id"], c["claim_date"].isoformat(), c["serial_number"], c["model"], c["component"],
                         c["description"], f"{c['cost_eur']:.2f}", c["status"]])

    # incident report
    bad = [b for b in C.BATCHES if b["battery_lot"] == BAD_LOT]
    first = min(C.claims_where(lot=BAD_LOT, components=["Battery connector"]), key=lambda c: c["claim_date"])
    n_sep = len(C.claims_where(lot=BAD_LOT, components=["Battery connector"], until=date(2025, 9, 23)))
    doc = Document()
    doc.add_heading("Incident report IR-2025-014", 0)
    table(doc, [["Title", "Overheating battery connector on Voltaris packs"],
                ["Opened", f"{first['claim_date']:%d %B %Y}"], ["Closed", "28 November 2025"],
                ["Owner (corrective action)", "Priya Raman, Lead Engineer, Battery & Electronics"],
                ["Reported by", "Nadia Kowalczyk, Quality Manager"], ["Severity", "S2 (safety-relevant, no injury)"]])
    doc.add_heading("1. Description", 1)
    doc.add_paragraph(
        f"On {first['claim_date']:%d %B %Y} a dealer reported a {first['model']} ({first['serial_number']}) whose battery "
        "connector housing had discoloured after charging. Further claims with the same symptom followed: a hot "
        "or melted XT90 connector at the main pack, sometimes with an intermittent power cut while riding.")
    doc.add_heading("2. Containment", 1)
    doc.add_paragraph(
        f"All affected bikes were built with packs from Voltaris lot {BAD_LOT}. The {len(bad)} production batches "
        f"concerned ({', '.join(b['batch_id'] for b in bad)}) were identified from the batch register. "
        "Packs of the lot still in stock were quarantined on 24 September 2025. A voluntary inspection campaign "
        "was opened for every serial number built with the lot: the dealer replaces the connector pigtail free of charge.")
    doc.add_heading("3. Root cause (5 Whys)", 1)
    table(doc, [["Why?", "Because"],
                ["Why did the connector overheat?", "Contact resistance at the crimp was 4 to 6 times nominal."],
                ["Why was the resistance high?", "Crimp height was below the connector maker's specification."],
                ["Why was the crimp height out of spec?", "A crimping die at Voltaris was replaced in July and not re-qualified."],
                ["Why was it not caught at Voltaris?", "Pull tests were sampled once per shift instead of once per reel."],
                ["Why was it not caught at incoming inspection?", "Arvenne's incoming inspection checked voltage and capacity, not crimps."]])
    doc.add_heading("4. Corrective actions", 1)
    for t in ["Voltaris re-qualifies every die after replacement and pull-tests once per reel (confirmed 14 October 2025).",
              "Arvenne adds a crimp cross-section check on 5 packs per incoming lot (from lot VL-2510-A).",
              "Warranty costs for the lot are claimed from Voltaris under clause 9.4 of the supply agreement."]:
        doc.add_paragraph(t, style="List Number")
    doc.add_heading("5. Note on scope", 1)
    doc.add_paragraph(
        "Pup bikes use Kelda Energy packs and are not affected. Packs of lot VL-2507-A, built just before the die "
        "change, showed no abnormal claims.")
    save_doc(doc, "operations/incident_report_IR-2025-014.docx")


def table(doc, rows):
    t = doc.add_table(rows=len(rows), cols=len(rows[0]))
    t.style = "Table Grid"
    for i, r in enumerate(rows):
        for j, v in enumerate(r):
            t.cell(i, j).text = str(v)


def save_doc(doc, path):
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    doc.save(p)


# ---------------------------------------------------------------- suppliers
def suppliers():
    pv = LATE_LOT_PACKS
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Thread: Voltaris lot VL-2508-C</title>
<style>body{{font-family:Arial,sans-serif;max-width:820px;margin:24px auto;color:#222}}
.msg{{border-top:1px solid #ccc;padding:14px 0}} .meta{{color:#666;font-size:13px}} blockquote{{color:#777;border-left:3px solid #ddd;margin:8px 0;padding-left:10px}}</style></head>
<body>
<h1>Re: PO 4500-2291 / Charge VL-2508-C</h1>
<p class="meta">Exported from Outlook by Karim Benali on 5 September 2025. 8 messages.</p>

<div class="msg"><p class="meta"><b>From:</b> Karim Benali &lt;k.benali@arvenne-cycles.example&gt;<br><b>To:</b> Jürgen Stolz &lt;j.stolz@voltaris-energie.example&gt;<br><b>Date:</b> Wed, 2 Jul 2025 09:14</p>
<p>Hello Jürgen,</p>
<p>Please find attached purchase order 4500-2291 for lot VL-2508-C: {pv['VP-625']} packs VP-625 and {pv['VP-750']} packs VP-750, prices as per the supply agreement. We need the lot at Villefranche on Monday 4 August at the latest, Line B is planned on it right after the summer closure.</p>
<p>Can you confirm the date?</p><p>Best regards,<br>Karim Benali<br>Logistics Manager, Arvenne Cycles</p></div>

<div class="msg"><p class="meta"><b>From:</b> Jürgen Stolz<br><b>To:</b> Karim Benali<br><b>Date:</b> Thu, 3 Jul 2025 16:02</p>
<p>Hallo Herr Benali,</p>
<p>hiermit bestätige ich die Bestellung 4500-2291: Charge VL-2508-C, {pv['VP-625']} × VP-625 und {pv['VP-750']} × VP-750, Lieferung frei Werk Villefranche zum 04.08.2025. Der Rechnungswert beträgt {LATE_LOT_VALUE:,.2f} EUR netto.</p>
<p>Mit freundlichen Grüßen<br>Jürgen Stolz<br>Key Account Manager, Voltaris Energiesysteme GmbH, Chemnitz</p></div>

<div class="msg"><p class="meta"><b>From:</b> Karim Benali<br><b>To:</b> Jürgen Stolz<br><b>Cc:</b> Mathieu Okafor<br><b>Date:</b> Tue, 5 Aug 2025 08:37</p>
<p>Jürgen, the lot did not arrive yesterday and the carrier has no tracking update. The plant is closed until the 17th, but if we do not have the packs for the restart Line B will have to stop. Please give me a firm date today.</p><p>Karim</p></div>

<div class="msg"><p class="meta"><b>From:</b> Jürgen Stolz<br><b>To:</b> Karim Benali<br><b>Cc:</b> Camille Dufresne<br><b>Date:</b> Mon, 18 Aug 2025 11:45</p>
<p>Sehr geehrter Herr Benali,</p>
<p>aufgrund des Streiks im Hamburger Hafen, der am 30.07.2025 begonnen hat, steht der Container mit den Zellen noch im Terminal. Wir berufen uns hiermit auf höhere Gewalt gemäß Ziffer 7.4 des Liefervertrags. Die voraussichtliche Ankunft in Villefranche ist der 26.08.2025.</p>
<p>Wir bedauern die Unannehmlichkeiten.<br>Jürgen Stolz</p></div>

<div class="msg"><p class="meta"><b>From:</b> Camille Dufresne &lt;c.dufresne@arvenne-cycles.example&gt;<br><b>To:</b> Jürgen Stolz<br><b>Cc:</b> Karim Benali, Inès Marchetti<br><b>Date:</b> Tue, 19 Aug 2025 10:20</p>
<p>Dear Mr Stolz,</p>
<p>We do not accept the force majeure notice. Clause 7.4 requires written notice within five business days of the start of the event; the strike started on 30 July and your notice is dated 18 August. We reserve our rights under clause 7.2 and will apply the late-delivery penalty from the confirmed date of 4 August until the actual delivery date.</p>
<p>Kind regards,<br>Camille Dufresne, CFO</p></div>

<div class="msg"><p class="meta"><b>From:</b> Karim Benali<br><b>To:</b> Jürgen Stolz<br><b>Date:</b> Thu, 28 Aug 2025 07:58</p>
<p>Jürgen, the lot was received yesterday, signed delivery note attached. 4 VP-750 packs arrived with dented casings and are quarantined: please send replacements. The other packs are going to Line B today.</p><p>Karim</p></div>

<div class="msg"><p class="meta"><b>From:</b> Jürgen Stolz<br><b>To:</b> Karim Benali<br><b>Cc:</b> Camille Dufresne<br><b>Date:</b> Tue, 2 Sep 2025 14:10</p>
<p>Hallo Herr Benali,</p>
<p>der Ersatz für die 4 beschädigten Packs geht diese Woche raus, kostenlos. Zur Vertragsstrafe: Wir schlagen eine Pauschale von 2 % des Rechnungswerts vor, um die Sache abzuschließen.</p>
<p>Grüße, J. Stolz</p></div>

<div class="msg"><p class="meta"><b>From:</b> Camille Dufresne<br><b>To:</b> Jürgen Stolz<br><b>Date:</b> Thu, 4 Sep 2025 09:03</p>
<p>Dear Mr Stolz, thank you for the replacement packs. We will apply clause 7.2 as written, without a flat rate. Our credit note request will follow.</p>
<blockquote>Zur Vertragsstrafe: Wir schlagen eine Pauschale von 2 % des Rechnungswerts vor…</blockquote>
<p>Camille Dufresne</p></div>
</body></html>"""
    w("suppliers/voltaris_email_thread_VL-2508-C.html", html)


# ---------------------------------------------------------------- finance
def finance():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Opex by department"
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ws.append(["Opex budget 2025, in thousands of euros (kEUR). Approved by the board on 10 December 2024."])
    ws.append(["Department"] + months)
    for c in ws[2]:
        c.font = Font(bold=True)
    for dep, vals in C.BUDGET.items():
        ws.append([dep] + vals)
    ws2 = wb.create_sheet("Headcount plan")
    hdr(ws2, ["Department", "End Q1", "End Q2", "End Q3", "End Q4"])
    for dep, vals in D.HEADCOUNT_PLAN.items():
        ws2.append([dep] + vals)
    ws3 = wb.create_sheet("Assumptions")
    hdr(ws3, ["Item", "Value", "Comment"])
    ws3.append(["FX EUR→CHF", FX["CHF"], "1 EUR = 0.94 CHF. Divide a CHF amount by this rate to get EUR."])
    ws3.append(["FX EUR→GBP", FX["GBP"], "1 EUR = 0.85 GBP. Divide a GBP amount by this rate to get EUR."])
    ws3.append(["Net revenue target FY2025 (EUR)", REVENUE_TARGET_EUR, "Delivered orders, net of discounts, excl. VAT"])
    for k, v in VAT.items():
        ws3.append([f"VAT rate {k} (%)", v, ""])
    ws3.append(["Mule price increase from 1 July (%)", 4, "All markets"])
    ws3.append(["Utrecht hub rent (EUR/month)", 11800, "From go-live"])
    autosize(wb)
    ws.column_dimensions["A"].width = 18
    wb.save(OUT / "finance/budget_2025.xlsx")


def investor_deck():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    h = C.headline()
    mu = C.monthly_units_delivered(range(1, 10))
    TMP.mkdir(exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    bars = ax.bar(labels, [mu[m] for m in range(1, 10)], color="#2f6f5e")
    for b, m in zip(bars, range(1, 10)):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 4, str(mu[m]), ha="center", fontsize=9)
    ax.set_title("Bikes delivered per month, 2025 (by order month)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(TMP / "deck_chart.png")
    plt.close(fig)

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    def slide(title, bullets=None):
        s = prs.slides.add_slide(prs.slide_layouts[5])
        s.shapes.title.text = title
        if bullets:
            tb = s.shapes.add_textbox(Inches(0.8), Inches(1.6), Inches(11.5), Inches(5))
            tf = tb.text_frame
            tf.word_wrap = True
            for i, b in enumerate(bullets):
                p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
                p.text = b
                p.font.size = PPt(22)
        return s

    s = prs.slides.add_slide(prs.slide_layouts[0])
    s.shapes.title.text = "Arvenne Cycles: Q3 2025 investor update"
    s.placeholders[1].text = "Prepared for Northbeam Ventures and the board · 10 October 2025 · Confidential"
    chg = (h["q3_rev"] / h["q2_rev"] - 1) * 100
    slide("Q3 at a glance", [
        f"Net revenue Q3: €{h['q3_rev']/1e6:.2f}M ({chg:+.0f}% vs Q2, summer closure in August)",
        f"Bikes delivered in Q3: {h['q3_units']:,}",
        f"Barge 2 launched on 15 September; up to {BARGE2_RANGE_WITH_EXTENDER} km with the Range Extender",
        f"Active dealers at 30 September: {h['active_dealers_sep30']}",
        f"Headcount at 30 September: {HEADCOUNT_Q3_DECK}",
    ])
    s = slide("Volumes")
    s.shapes.add_picture(str(TMP / "deck_chart.png"), Inches(1.5), Inches(1.5), width=Inches(10))
    slide("Risks we are managing", [
        f"Battery quality: abnormal connector claims on one Voltaris lot ({BAD_LOT}); inspection campaign under way, costs to be recovered from the supplier",
        "Supply: lot VL-2508-C arrived 23 days late; penalty claimed under the supply agreement",
        "Product transition: first-generation Barge reached end of sale on 30 September",
    ])
    slide("Cash", ["Cash at 30 September: €6.2M", "Average monthly net burn Q3: €0.28M", "No new debt in Q3"])
    slide("Next quarter", ["Utrecht distribution hub opens in November", "Barge 2 ramp-up on Line B",
                           "2026 price list to the board in December"])
    p = OUT / "finance/investor_update_q3_2025.pptx"
    prs.save(p)


# ---------------------------------------------------------------- HR
def hr():
    w("hr/employee_handbook_v3.2.md", f"""
# Arvenne Cycles employee handbook

Version 3.2 · effective 1 March 2025 · owner: Aurélie Moreau, HR Manager

This handbook applies to every employee of {COMPANY}, at the Lyon head office ({HQ}) and at the {PLANT} plant. Where a collective agreement or the law is more favourable, it prevails.

## 1. Working time

The standard working week is 35 hours. Office staff work flexible hours with core hours from 10:00 to 16:00. Plant staff work in two shifts (06:00-13:30 and 13:30-21:00) on Lines A and B.

## 2. Remote work

Employees in eligible roles may work remotely up to **2 days per week**, agreed with their line manager. Roles at the plant (production, logistics, quality) are not eligible. Remote days cannot be carried over from one week to the next.

## 3. Leave

- 25 days of paid leave per year, plus 8 "Arvenne days" (reduced working time days).
- The plant closes for two weeks in August; the dates are announced before 31 January.
- Parental leave follows the law, with full salary maintained for the first 4 weeks of the second parent's leave.

## 4. Expenses

### 4.1 Approval

| Amount of a single claim | Approval needed |
| --- | --- |
| Up to €500 | Line manager |
| €500.01 to €2,500 | Head of department |
| Above €2,500 | Head of department **and** the CFO |

Claims are submitted within 30 days with an itemised receipt. Alcohol, minibar items and fines are never reimbursed.

### 4.2 Travel

- Train is the default for any trip under 4h30 door to door. Flights are economy class.
- Hotels: up to **€150 per night**, breakfast included, city taxes reimbursed on top.
- Per diem for meals on travel days: **€45**.
- Private car: €0.38 per km, only when no train or company car is available.

### 4.3 Sustainable mobility

Employees who commute by bike receive a mobility allowance of €40 per month.

## 5. Equipment and discounts

- Laptops are renewed every 4 years.
- Employees may buy one Arvenne bike per calendar year at 30% off the recommended retail price, and keep it at least 12 months before reselling it.

## 6. Probation

| Category | Probation |
| --- | --- |
| Operators and technicians | 2 months |
| Supervisors | 3 months |
| Managers and engineers | 4 months |

## 7. Security

Use the company password manager for every work account. Report a lost laptop or phone to IT within 24 hours.
""")

    doc = Document()
    doc.add_heading("Travel policy update", 0)
    doc.add_paragraph("Reference HR-POL-07 rev. B · Issued 25 August 2025 by Aurélie Moreau (HR) and Camille Dufresne (CFO)")
    doc.add_paragraph(
        "This update replaces section 4.2 (Travel) of the employee handbook v3.2. It applies to trips "
        f"starting on or after {TRAVEL_UPDATE_DATE:%d %B %Y}. Trips that started earlier follow the previous rules. "
        "All other sections of the handbook are unchanged.")
    doc.add_heading("1. Transport", 1)
    doc.add_paragraph("Train is the default for any trip under 5 hours door to door (previously 4h30). First class "
                      "is allowed for train journeys over 3 hours when the employee works on board.")
    doc.add_heading("2. Hotel caps per night", 1)
    doc.add_paragraph("Caps are per night, room only, excluding city taxes, which are reimbursed on top. "
                      "A room above the cap is reimbursed only up to the cap unless the line manager approved the "
                      "excess in writing before the trip.")
    table(doc, [["Country", "Cap per night"]] + [[k, v] for k, v in HOTEL_CAPS_NEW.items()])
    doc.add_heading("3. Per diem", 1)
    doc.add_paragraph(f"€{PER_DIEM_NEW} per travel day (CHF {PER_DIEM_NEW_CH} in Switzerland, £48 in the United Kingdom).")
    doc.add_heading("4. Unchanged", 1)
    doc.add_paragraph("Mileage (€0.38 per km), the 30-day submission rule and the approval thresholds of section 4.1.")
    save_doc(doc, "hr/travel_policy_update_2025-09.docx")

    doc = Document()
    doc.add_heading("Compte rendu de la réunion du CSE du 13 novembre 2025", 0)
    doc.add_paragraph("Présents : Inès Marchetti (présidente), Aurélie Moreau (RH), 6 élus titulaires. "
                      "Secrétaire de séance : Thomas Guérin (élu, ligne B).")
    doc.add_heading("1. Accord sur le télétravail", 1)
    doc.add_paragraph("La direction et les élus signent l'avenant n°2 à l'accord télétravail. À compter du "
                      "1er janvier 2026, les salariés occupant un poste éligible pourront télétravailler jusqu'à "
                      "3 jours par semaine. Les postes de production, de logistique et de qualité restent non éligibles. "
                      "Une indemnité de 2,50 € par jour télétravaillé est versée, plafonnée à 30 € par mois.")
    doc.add_heading("2. Prime de partage de la valeur", 1)
    doc.add_paragraph("Une prime de 600 € brut sera versée à chaque salarié présent au 30 novembre 2025, avec la paie "
                      "de décembre. Les salariés à temps partiel la perçoivent au prorata de leur temps de travail.")
    doc.add_heading("3. Titres-restaurant", 1)
    doc.add_paragraph("À partir de janvier 2026, la valeur faciale du titre-restaurant passe de 9 € à 10 €. "
                      "La part employeur reste fixée à 60 %.")
    doc.add_heading("4. Sécurité au poste", 1)
    doc.add_paragraph("Suite à l'incident des connecteurs de batterie, les élus demandent une formation au risque "
                      "électrique pour les opérateurs de la ligne B. La direction s'engage à la planifier au premier "
                      "trimestre 2026.")
    doc.add_heading("5. Prochaine réunion", 1)
    doc.add_paragraph("Le 15 janvier 2026 à 14 h, salle Saône, site de Villefranche.")
    save_doc(doc, "hr/cse_compte_rendu_2025-11-13.docx")


# ---------------------------------------------------------------- meetings
def meetings():
    w("meetings/board_minutes_2025-06-24.md", f"""
# Board meeting minutes · 24 June 2025

**Present:** Inès Marchetti (CEO, chair), Camille Dufresne (CFO), Tomasz Wielgosz (CTO), Daan Visser (Northbeam Ventures), Sabine Roux (independent director).
**Attending:** Mathieu Okafor (Head of Operations), Ruth Achterberg (Head of Sales).
**Secretary:** Hugo Lambert.

## 1. Trading update

Camille presented the figures to the end of May. Spring demand was strong on the Mule and the Pup. The Trike remains a small volume, mostly for fleets.

## 2. Pricing

The cost of Mule frames rose 9% with the new aluminium contract. Ruth proposed a price increase on the Mule only.

**Decision:** the Mule's price rises by 4% in every market from 1 July 2025, rounded to the nearest 10 in local currency. In France the recommended retail price moves from €4,290 to €4,460 including VAT.

## 3. Product transition

**Decision:** the first-generation Barge reaches end of sale on 30 September 2025. Remaining stock is offered to fleet customers first.

**Decision:** the Barge 2 recommended retail price is set at €5,690 including VAT. The optional Range Extender battery will sell at €{RANGE_EXTENDER_PRICE}.

## 4. Utrecht distribution hub

Mathieu presented the lease for a 1,400 m² warehouse in Utrecht to serve the Benelux and Germany.

**Decision:** the lease is approved at €11,800 per month. Target go-live: 3 November 2025.

## 5. Targets and hiring

The net revenue target for 2025 is maintained at €{REVENUE_TARGET_EUR/1e6:.1f}M. The board approves 12 operator hires for Line B ahead of the Barge 2 ramp-up.

## Actions

| Action | Owner | Due |
| --- | --- | --- |
| Update price lists and the webshop for the Mule | Ruth Achterberg | 30 June |
| Sign Utrecht lease | Mathieu Okafor | 15 July |
| Barge 2 launch plan | Léa Fontaine | 1 September |
""")

    n_sep = len(C.claims_where(lot=BAD_LOT, components=["Battery connector"], until=date(2025, 9, 23)))
    lot_n = C.lot_units(BAD_LOT)
    doc = Document()
    doc.add_heading("Board meeting minutes, 23 September 2025", 0)
    doc.add_paragraph("Present: Inès Marchetti (chair), Camille Dufresne, Tomasz Wielgosz, Daan Visser, Sabine Roux. "
                      "Attending: Mathieu Okafor, Nadia Kowalczyk (item 2). Secretary: Hugo Lambert.")
    doc.add_heading("1. Barge 2", 1)
    doc.add_paragraph(
        "Léa Fontaine's team held the Barge 2 launch event in Lyon on 15 September for press and dealers. Dealers "
        "have been taking pre-orders since 22 September. Customer deliveries start on 1 October, the date used in the "
        "catalogue and the press release. The first-generation Barge stops being sold on 30 September as decided in June.")
    doc.add_heading("2. Battery connector claims", 1)
    doc.add_paragraph(
        f"Nadia Kowalczyk reported {n_sep} warranty claims for overheating battery connectors, all on bikes built "
        f"with Voltaris lot {BAD_LOT}. The lot equipped {lot_n} bikes. The usual rate for this failure is below 0.5%.")
    doc.add_paragraph(
        "Decision: open a voluntary inspection campaign for every serial number built with the lot, and quarantine "
        "the packs of the lot still in stock. Camille Dufresne will prepare the claim against Voltaris under the "
        "supply agreement.")
    doc.add_heading("3. Supply", 1)
    doc.add_paragraph("Lot VL-2508-C arrived on 27 August instead of 4 August. Voltaris's force majeure notice was "
                      "rejected; the late-delivery penalty will be applied as per the contract.")
    doc.add_heading("4. Utrecht", 1)
    doc.add_paragraph("The lease is signed. Racking installation slipped by two weeks; go-live is now planned for 17 November.")
    save_doc(doc, "meetings/board_minutes_2025-09-23.docx")

    h = C.headline()
    w("meetings/board_minutes_2025-12-16.txt", f"""
ARVENNE CYCLES SAS - BOARD MEETING - 16 DECEMBER 2025 - MINUTES

Present: I. Marchetti (chair), C. Dufresne, T. Wielgosz, D. Visser, S. Roux
Secretary: H. Lambert

1. YEAR-END OUTLOOK
CD presented the expected year-end position. Orders for the full year will be closed on 31 December; final
revenue figures will come from the order export in January. The board noted that Q3 was weaker than Q2
because of the August closure.

2. PEOPLE
Headcount at 30 September was {HEADCOUNT_Q3_MINUTES_Q4}; it is 84 today. AM's report on the CSE agreement (remote work, value-sharing bonus) was noted.

3. OPERATIONS
The Utrecht hub went live on 17 November as re-planned in September. Barge 2 production on Line B reached its
planned rate in November.

4. VOLTARIS
Voltaris accepted in principle our claim under clause 9.4 for lot {BAD_LOT}. Finance will compute the amount
from the warranty claims register at year end, counting approved claims only. The late-delivery penalty for
lot {LATE_LOT} was accepted at the contractual rate.

5. 2026 PRICES AND BUDGET
DECISION: all models +3% from 1 February 2026, rounded to the nearest 10 in local currency.
DECISION: no Range Extender for the Pup in 2026; engineering capacity goes to the Barge 2 cargo box variants.
DECISION: the Trike stays in the 2026 range (question raised at the October ops and sales sync); fleet demand
justifies it, but no new Trike development before 2027.
DECISION: the 2026 budget is approved.

Next meeting: 17 March 2026.
""")


# ---------------------------------------------------------------- products & support
def products_support():
    w("products/press_release_barge2.md", f"""
# Arvenne unveils Barge 2, its new front-loader cargo bike

*Lyon, 15 September 2025. For immediate release.*

Arvenne Cycles today unveiled Barge 2, the successor of its best-selling front-loader. Barge 2 is lighter than the first generation (39.5 kg instead of 41 kg), carries up to 260 kg in total, and comes with a 750 Wh battery as standard.

"Families told us the Barge was perfect except for one thing: range on hilly school runs," said Inès Marchetti, CEO and co-founder. "Barge 2 answers that, and it rides like a much smaller bike."

**Key facts**

- Mid-drive motor, 90 Nm
- 750 Wh battery, 60 to 120 km of range depending on load and terrain
- Optional {RANGE_EXTENDER_WH} Wh Range Extender (€{RANGE_EXTENDER_PRICE}), adding up to 60 km of range
- Hydraulic disc brakes, 4-piston at the front with a 220 mm rotor
- Recommended retail price: €5,690 including VAT in France

**Availability:** at Arvenne dealers and on arvenne.com from 1 October 2025.

Press contact: Léa Fontaine, Head of Marketing.
""")

    faq = [
        {"q": "How long does it take to charge the battery?", "a": "With the standard 4 A charger: about 3.5 hours for the Pup, 4 to 4.5 hours for the Mule and the Trike, 5 hours for the Barge 2's 750 Wh battery. The Range Extender charges separately in about 3 hours."},
        {"q": "What does the warranty cover?", "a": "Frames are guaranteed for 10 years. Motors, batteries and electronics for 2 years, or 800 full charge cycles for batteries, whichever comes first. Wear parts (tyres, brake pads, chains and belts) are not covered."},
        {"q": "How much weight can the Trike carry?", "a": "The Trike is approved for a total of 250 kg, rider and cargo included."},
        {"q": "Can I fit the Range Extender to my bike?", "a": "The Range Extender works with the Barge 2 only. It is not compatible with the Mule, the Pup, the Trike or the first-generation Barge."},
        {"q": "Where is my serial number?", "a": "It is engraved under the bottom bracket and starts with ARV25- for bikes built in 2025. It is also on your invoice."},
        {"q": "When is the first service due?", "a": "After 300 km or 3 months, whichever comes first, then every 2,000 km or once a year."},
        {"q": "How many children can I carry?", "a": "Barge 2: up to 3 children in the box with the bench and harnesses. Mule: 2 children on the rear rack with approved seats. Pup: 1 child seat. Trike: 2 children with the bench kit."},
        {"q": "Is there a recall on my battery?", "a": "There is no recall. A free voluntary inspection campaign is running for some bikes built in July and August 2025. Your dealer can check your serial number in a few seconds."},
        {"q": "Do you deliver to Spain or Italy?", "a": "Not yet. We currently sell in France, Germany, the Netherlands, Belgium, Switzerland, Austria and the United Kingdom."},
        {"q": "Can I return a bike bought online?", "a": "Yes, within 14 days of delivery, in its original condition. We refund the full price including delivery."},
        {"q": "Which tyre pressure should I use?", "a": "Front-loaders: 2.5 to 3.0 bar front, 3.0 to 3.5 bar rear when loaded. Follow the range printed on the tyre sidewall."},
    ]
    p = OUT / "support/support_faq.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"updated": "2025-10-02", "owner": "Marco Bellini, Customer Care Lead", "entries": faq},
                            ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    sales()
    operations()
    suppliers()
    finance()
    investor_deck()
    hr()
    meetings()
    products_support()


if __name__ == "__main__":
    main()
