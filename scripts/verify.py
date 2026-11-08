"""Recomputes the reference value of every table-derived question from the published corpus
files only (CSV, XLSX, nothing from the generator), and checks it against dataset/questions.jsonl.
Run: .venv/bin/python scripts/verify.py"""

import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "corpus"
Q = {json.loads(l)["id"]: json.loads(l) for l in (ROOT / "dataset/questions.jsonl").open(encoding="utf-8")}

class _ByText(dict):
    """Questions looked up by the start of their text, so renumbering cannot silently break a check."""
    def __getitem__(self, prefix):
        hits = [q for q in Q.values() if q["question"].startswith(prefix)]
        assert len(hits) == 1, prefix
        return hits[0]["id"]


Q_ = _ByText()
orders = list(csv.DictReader((CORPUS / "sales/orders_2025.csv").open(encoding="utf-8")))
claims = list(csv.DictReader((CORPUS / "operations/warranty_claims_2025.csv").open(encoding="utf-8")))


def sheet(path, name, header_row=1):
    ws = openpyxl.load_workbook(CORPUS / path, data_only=True)[name]
    rows = list(ws.iter_rows(values_only=True))
    hdr = rows[header_row - 1]
    return [dict(zip(hdr, r)) for r in rows[header_row:] if any(v is not None for v in r)]


dealers = {r["dealer_id"]: r for r in sheet("sales/dealers_2025.xlsx", "Dealers")}
targets = {r["dealer_id"]: r["target_units_2025"] for r in sheet("sales/dealers_2025.xlsx", "Targets 2025")}
tiers = {r["tier"]: r for r in sheet("sales/dealers_2025.xlsx", "Tier terms")}
batches = sheet("operations/production_batches_2025.xlsx", "Batches")
assump = {r["Item"]: r["Value"] for r in sheet("finance/budget_2025.xlsx", "Assumptions")}
budget = {r["Department"]: r for r in sheet("finance/budget_2025.xlsx", "Opex by department", header_row=2)}
headcount = sheet("finance/budget_2025.xlsx", "Headcount plan")
FX = {"EUR": 1.0, "CHF": assump["FX EUR→CHF"], "GBP": assump["FX EUR→GBP"]}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

for r in orders:
    r["d"] = date.fromisoformat(r["order_date"])
    r["q"], r["p"], r["disc"] = int(r["quantity"]), float(r["unit_price"]), float(r["discount_pct"])
    r["net_local"] = r["q"] * r["p"] * (1 - r["disc"] / 100)
    r["eur"] = r["net_local"] / FX[r["currency"]] if r["status"] == "Delivered" else 0.0
for b in batches:
    b["lo"], b["hi"] = int(b["serial_from"].split("-")[1]), int(b["serial_to"].split("-")[1])
    b["start"] = b["start_date"].date() if isinstance(b["start_date"], datetime) else b["start_date"]
for c in claims:
    n = int(c["serial_number"].split("-")[1])
    c["batch"] = next(b for b in batches if b["lo"] <= n <= b["hi"])
    c["cost"] = float(c["cost_eur"])


def dl(rows):
    return [r for r in rows if r["status"] == "Delivered"]


def rev(rows):
    return sum(r["eur"] for r in rows)


def qtr(d):
    return (d.month - 1) // 3 + 1


dealer_units = Counter()
for r in dl(orders):
    if r["channel"] == "Dealer":
        dealer_units[r["dealer_id"]] += r["q"]
lot_units = Counter()
for b in batches:
    lot_units[b["battery_lot"]] += b["units"]
BAD = "VL-2507-B"
bad_conn = [c for c in claims if c["batch"]["battery_lot"] == BAD and c["component"] == "Battery connector"]
bad_appr = [c for c in claims if c["batch"]["battery_lot"] == BAD and c["component"] in ("Battery connector", "Battery cell") and c["status"] == "Approved"]
direct = [r for r in orders if r["channel"] == "Direct"]
fleet = [r for r in orders if r["channel"] == "Fleet"]
mule_after = [r for r in dl(orders) if r["model"] == "Mule" and r["d"] >= date(2025, 7, 1)]
OLD = {"EUR": round(4290 / 1.2, 2), "CHF": 3590, "GBP": 3050}  # minutes (FR RRP) and pre-July export list
fl = lambda q: rev([r for r in orders if qtr(r["d"]) == q and r["model"] in ("Barge", "Barge 2")])
am = defaultdict(float)
for r in orders:
    if r["channel"] == "Dealer":
        am[dealers[r["dealer_id"]]["account_manager"]] += r["eur"]
b2 = Counter()
for r in dl(orders):
    if r["model"] == "Barge 2" and r["channel"] == "Dealer":
        b2[r["dealer_id"]] += r["q"]
gold_nonfr = [d for d, v in dealers.items() if v["tier"] == "Gold" and v["country"] != "FR"]
fleet_ok = Counter()
for r in dl(fleet):
    fleet_ok[r["customer"]] += r["q"]
built = Counter()
for b in batches:
    built[b["model"]] += b["units"]
other_lots = [l for l in lot_units if l.startswith("VL-") and l != BAD]

EXPECT = {
    Q_["How many Gold-tier dealers does Arvenne have?"]: sum(1 for v in dealers.values() if v["tier"] == "Gold"),
    Q_["How many order lines were cancelled in 2025?"]: sum(1 for r in orders if r["status"] == "Cancelled"),
    Q_["How many bikes were delivered in 2025 (all channels, deliver"]: sum(r["q"] for r in dl(orders)),
    Q_["How many warranty claims were still pending at the end of 20"]: sum(1 for c in claims if c["status"] == "Pending"),
    Q_["Which component has the most warranty claims in 2025, and ho"]: Counter(c["component"] for c in claims).most_common(1)[0][1],
    Q_["How many production batches were built on Line B in 2025?"]: sum(1 for b in batches if b["line"] == "B"),
    Q_["Which department has the largest opex budget for 2025?"]: max(sum(v[m] for m in MONTHS) for v in budget.values()),
    Q_["What is Marketing's opex budget for the fourth quarter of 20"]: sum(budget["Marketing"][m] for m in ["Oct", "Nov", "Dec"]),
    Q_["What headcount does the 2025 plan foresee at the end of the "]: sum(r["End Q4"] for r in headcount),
    Q_["How many fleet orders were placed in 2025, including cancell"]: len(fleet),
    Q_["How many Barge 2 bikes were delivered from 2025 orders?"]: sum(r["q"] for r in dl(orders) if r["model"] == "Barge 2"),
    Q_["What was Arvenne's total net revenue in 2025, in euros?"]: rev(orders),
    Q_["Did Arvenne reach its 2025 net revenue target? By how much d"]: rev(orders) - assump["Net revenue target FY2025 (EUR)"],
    Q_["What share of 2025 net revenue came through the webshop?"]: rev(direct) / rev(orders) * 100,
    Q_["Which model brought in the most net revenue in 2025, and how"]: max(rev([r for r in orders if r["model"] == m]) for m in {r["model"] for r in orders}),
    Q_["How many dealers met or beat their 2025 unit target?"]: sum(1 for d in dealers if dealer_units[d] >= targets[d]),
    Q_["How many Mules were delivered from orders placed before the "]: sum(r["q"] for r in mule_after),
    Q_["How many bikes were built with battery lot VL-2507-B?"]: lot_units[BAD],
    Q_["How many battery connector claims were logged by the end of "]: len(bad_conn),
    Q_["How much net revenue did the webshop make during the Black F"]: rev([r for r in direct if date(2025, 11, 24) <= r["d"] <= date(2025, 12, 1)]),
    Q_["How much net revenue did Arvenne make in Switzerland in 2025"]: rev([r for r in orders if r["country"] == "CH"]),
    Q_["What was Arvenne's UK net revenue in 2025, in pounds and in "]: rev([r for r in orders if r["country"] == "UK"]),
    Q_["What was the average net value of a delivered webshop order "]: rev(direct) / len(dl(direct)),
    Q_["What share of webshop orders were returned in 2025?"]: sum(1 for r in direct if r["status"] == "Returned") / len(direct) * 100,
    Q_["How many bikes did Fietskoerier Utrecht receive in 2025?"]: sum(r["q"] for r in dl(fleet) if r["customer"] == "Fietskoerier Utrecht"),
    Q_["By how much is Operations' opex budget higher in the second "]: sum(budget["Operations"][m] for m in MONTHS[6:]) - sum(budget["Operations"][m] for m in MONTHS[:6]),
    Q_["Does lot VL-2507-B trigger the field-failure clause of the V"]: len(bad_appr) / lot_units[BAD] * 100,
    Q_["How much should Voltaris reimburse Arvenne under clause 9.4 "]: sum(c["cost"] for c in bad_appr) + 40 * len(bad_appr),
    Q_["How does the battery connector claim rate of lot VL-2507-B c"]: len(bad_conn) / lot_units[BAD] * 100,
    Q_["How did front-loader net revenue (Barge and Barge 2 together"]: fl(4),
    Q_["Which account manager's dealers generated the most net reven"]: max(am.values()),
    Q_["How much extra net revenue did the July 2025 Mule price incr"]: sum(r["q"] * (r["p"] - OLD[r["currency"]]) * (1 - r["disc"] / 100) / FX[r["currency"]] for r in mule_after),
    Q_["How much revenue did Arvenne give up through fleet discounts"]: sum(r["q"] * r["p"] * r["disc"] / 100 / FX[r["currency"]] for r in dl(fleet)),
    Q_["Which fleet customer took delivery of the most bikes in 2025"]: fleet_ok.most_common(1)[0][1],
    Q_["Which dealer delivered the most Barge 2 bikes in 2025, and w"]: b2.most_common(1)[0][1],
    Q_["What did approved warranty claims on the Pup cost in 2025, a"]: sum(c["cost"] for c in claims if c["model"] == "Pup" and c["status"] == "Approved"),
    Q_["The September board minutes give a number of connector claim"]: len(bad_conn) - sum(1 for c in bad_conn if date.fromisoformat(c["claim_date"]) <= date(2025, 9, 23)),
    Q_["If a Gold dealer in Zurich ordered two Barge 2 at list price"]: 4760 * 2 * (1 - tiers["Gold"]["discount_pct"] / 100) / FX["CHF"],
}
NAMES = {
    Q_["Which Gold-tier dealer fell furthest short of its 2025 unit "]: min((d for d, v in dealers.items() if v["tier"] == "Gold"), key=lambda d: dealer_units[d] - targets[d]),
    Q_["Among Gold-tier dealers outside France, which one achieved t"]: dealers[max(gold_nonfr, key=lambda d: dealer_units[d] / targets[d])]["name"],
    Q_["Which dealer delivered the most Barge 2 bikes in 2025, and w"]: dealers[b2.most_common(1)[0][0]]["name"],
    Q_["Which fleet customer took delivery of the most bikes in 2025"]: fleet_ok.most_common(1)[0][0],
}

bad = 0
for qid, got in EXPECT.items():
    q = Q[qid]
    ref, tol = q["value"], q["tolerance"] or 0
    ok = abs(got - ref) <= tol + 0.51  # tolerance is absolute, in the answer unit; values are rounded
    print(("OK  " if ok else "FAIL"), q["id"], f"ref={ref}", f"recomputed={got:.2f}")
    bad += not ok
for qid, name in NAMES.items():
    ok = name in Q[qid]["answer"]
    print(("OK  " if ok else "FAIL"), qid, "name", name)
    bad += not ok
# a naive reading of the fleet trap must give a different customer
naive = Counter()
for r in fleet:
    naive[r["customer"]] += r["q"]
trap_ok = naive.most_common(1)[0][0] != fleet_ok.most_common(1)[0][0]
print(("OK  " if trap_ok else "FAIL"), "ARB-136 trap: naive count picks", naive.most_common(1)[0])
bad += not trap_ok

# ---------------------------------------------------------------- documents: what text extraction sees
import pymupdf
from docx import Document
from pptx import Presentation


def pdf_text(p):
    return " ".join(pg.get_text() for pg in pymupdf.open(CORPUS / p))


def docx_text(p):
    d = Document(CORPUS / p)
    return " ".join([x.text for x in d.paragraphs] + [c.text for t in d.tables for row in t.rows for c in row.cells])


def pptx_text(p):
    return " ".join(sh.text_frame.text for s in Presentation(CORPUS / p).slides for sh in s.shapes if sh.has_text_frame)


cat = pdf_text("products/arvenne_catalogue_2025_autumn.pdf")
DOC_CHECKS = [
    ("catalogue: diagram facts only in the figure", not any(s in cat for s in ["13S4P", "30 A", "CAN bus", "DM-2"])),
    ("catalogue: chart values only in the figure", "88 km" not in cat),
    ("catalogue: Trike 280 kg in the text", "280 kg" in cat),
    ("scans carry no text layer", all(not pdf_text(p).strip() for p in ["operations/field_test_notes_barge2_P3.pdf", "suppliers/voltaris_delivery_note_VL-2508-C.pdf"])),
    ("contract: 7.4 five business days", "within 5 Business Days" in pdf_text("suppliers/voltaris_supply_agreement.pdf")),
    ("deck: 15 September and headcount 81", "15 September" in pptx_text("finance/investor_update_q3_2025.pptx") and "81" in pptx_text("finance/investor_update_q3_2025.pptx")),
    ("deck: monthly units only in the chart image", "404" not in pptx_text("finance/investor_update_q3_2025.pptx")),
    ("Q3 minutes: connector count matches the register at 23 Sept", f"reported {len(bad_conn) - EXPECT[Q_['The September board minutes give a number of connector claims']]} warranty claims" in docx_text("meetings/board_minutes_2025-09-23.docx")),
    ("CSE minutes in French: 3 jours", "3 jours par semaine" in docx_text("hr/cse_compte_rendu_2025-11-13.docx")),
    ("FAQ: Trike 250 kg", "250 kg" in (CORPUS / "support/support_faq.json").read_text(encoding="utf-8")),
]
for name, ok in DOC_CHECKS:
    print(("OK  " if ok else "FAIL"), name)
    bad += not ok
print(f"\n{len(EXPECT) + len(NAMES) + 1 + len(DOC_CHECKS) - bad} passed, {bad} failed")
sys.exit(1 if bad else 0)
