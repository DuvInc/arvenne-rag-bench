"""The question set. Every number is computed from the same tables the corpus was written from,
so reference answers cannot drift from the documents. Text answers are written by hand from
world.py and the document sources."""

import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import calc as C
import data as D
from render_visual import FIELD_PAGES, RANGE_POINTS  # noqa: F401  (documents the source)
from world import *  # noqa: F403

ROOT = Path(__file__).resolve().parent.parent
Q = []

F = dict(
    orders="sales/orders_2025.csv", sreadme="sales/README.md", dealers="sales/dealers_2025.xlsx",
    cat="products/arvenne_catalogue_2025_autumn.pdf", press="products/press_release_barge2.md",
    faq="support/support_faq.json", letter="support/customer_letter_leclerc.jpg",
    batches="operations/production_batches_2025.xlsx", claims="operations/warranty_claims_2025.csv",
    ir="operations/incident_report_IR-2025-014.docx", field="operations/field_test_notes_barge2_P3.pdf",
    wb="operations/whiteboard_q4_priorities.jpg", contract="suppliers/voltaris_supply_agreement.pdf",
    mail="suppliers/voltaris_email_thread_VL-2508-C.html", dn="suppliers/voltaris_delivery_note_VL-2508-C.pdf",
    budget="finance/budget_2025.xlsx", deck="finance/investor_update_q3_2025.pptx",
    receipt="finance/expense_receipt_hartmann_zurich.jpg", hb="hr/employee_handbook_v3.2.md",
    travel="hr/travel_policy_update_2025-09.docx", org="hr/org_chart_2025.png",
    cse="hr/cse_compte_rendu_2025-11-13.docx", m06="meetings/board_minutes_2025-06-24.md",
    m09="meetings/board_minutes_2025-09-23.docx", m12="meetings/board_minutes_2025-12-16.txt",
)


def add(level, question, answer, kind, sources, skills, rubric=None, value=None, unit=None, tol=None, accept=None, note=None):
    if unit == "EUR" and tol and tol < 1:  # given as a share of the value, stored as an absolute amount
        tol = round(abs(value) * tol, 2)
    Q.append(dict(level=level, question=question, answer=answer, answer_type=kind,
                  value=value, unit=unit, tolerance=tol, accept=accept or [], rubric=rubric or [],
                  sources=[F[s] for s in sources], skills=skills, note=note))


def money(x, cur="€", dec=0):
    return f"{cur}{x:,.{dec}f}"


# ------------------------------------------------------------------ computed facts
O, B, CL, BUDGET = C.ORDERS, C.BATCHES, C.CLAIMS, C.BUDGET
dlv = C.delivered()
rev_total = C.rev(O)
rev_model = {m: C.rev(C.where(model=m)) for m in PRODUCTS}
rev_channel = {ch: C.rev(C.where(channel=ch)) for ch in ["Dealer", "Direct", "Fleet"]}
rev_q = {q: C.rev(C.where(quarter=q)) for q in range(1, 5)}
rev_m = {m: C.rev(C.where(month=m)) for m in range(1, 13)}
units_model = {m: C.units(C.delivered(C.where(model=m))) for m in PRODUCTS}
units_total = C.units(dlv)
cancelled_rows = [r for r in O if r["status"] == "Cancelled"]
direct_rows = C.where(channel="Direct")
returned_direct = [r for r in direct_rows if r["status"] == "Returned"]
du = C.dealer_units()
T = C.TARGETS
dealer_info = {d[0]: d for d in DEALERS}
gold = [d[0] for d in DEALERS if d[4] == "Gold"]
target_dealers = [d[0] for d in DEALERS]
met = [d for d in target_dealers if du[d] >= T[d]]
gold_short = min(gold, key=lambda d: du[d] - T[d])
mu = C.monthly_units_delivered(range(1, 10))
best_month = max(mu, key=mu.get)
# A tie is part of the answer: max() alone kept the first month and made "May" the reference while June has the same 404 (2026-11-08).
best_months = [m for m in mu if mu[m] == mu[best_month]]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
budget_tot = {k: sum(v) for k, v in BUDGET.items()}
top_dep = max(budget_tot, key=budget_tot.get)
mkt_q4 = sum(BUDGET["Marketing"][9:12])
ops_h1, ops_h2 = sum(BUDGET["Operations"][:6]), sum(BUDGET["Operations"][6:])
comp_count = Counter(c["component"] for c in CL)
top_comp = comp_count.most_common(1)[0]
pending = sum(1 for c in CL if c["status"] == "Pending")
lineB_batches = sum(1 for b in B if b["line"] == "B")
b2_first_batch = min((b for b in B if b["model"] == "Barge 2"), key=lambda b: b["start_date"])
b2_units = units_model["Barge 2"]
b2_dec_prod = sum(b["units"] for b in B if b["model"] == "Barge 2" and b["start_date"].month == 12)
b2_nov_prod = sum(b["units"] for b in B if b["model"] == "Barge 2" and b["start_date"].month == 11)

bad_batches = [b for b in B if b["battery_lot"] == BAD_LOT]
bad_units = C.lot_units(BAD_LOT)
bad_conn_all = C.claims_where(lot=BAD_LOT, components=["Battery connector"])
bad_conn_sep = C.claims_where(lot=BAD_LOT, components=["Battery connector"], until=date(2025, 9, 23))
bad_batt_appr = C.claims_where(lot=BAD_LOT, components=list(D.BATTERY_COMPONENTS), status=["Approved"])
bad_rate = len(bad_batt_appr) / bad_units * 100
reimb = sum(c["cost_eur"] for c in bad_batt_appr) + CONTRACT["handling_fee"] * len(bad_batt_appr)
other_v_lots = [l for l, *_ in VOLTARIS_LOTS if l != BAD_LOT]
other_v_units = sum(C.lot_units(l) for l in other_v_lots)
other_v_conn = sum(len(C.claims_where(lot=l, components=["Battery connector"])) for l in other_v_lots)
restart = date(2025, 8, 18)
bad_after_restart = sum(b["units"] for b in bad_batches if b["start_date"] >= restart)
bad_after_restart_batches = [b["batch_id"] for b in bad_batches if b["start_date"] >= restart]

letter_claim = next(c for c in CL if c["serial_number"] == C.LETTER_SERIAL)
LB = C.LETTER_BATCH

late_days = (LATE_LOT_DELIVERED - LATE_LOT_PROMISED).days
late_weeks = late_days // 7
penalty = LATE_LOT_VALUE * min(late_weeks * CONTRACT["late_pct_per_week"], CONTRACT["late_cap_pct"]) / 100
fm_deadline = C.business_days_after(STRIKE_START, CONTRACT["fm_notice_business_days"])

fleet = C.where(channel="Fleet")
fleet_units_ok = Counter()
fleet_units_all = Counter()
for r in fleet:
    fleet_units_all[r["customer"]] += r["quantity"]
    if r["status"] == "Delivered":
        fleet_units_ok[r["customer"]] += r["quantity"]
fleet_top = fleet_units_ok.most_common(2)
fleet_naive = fleet_units_all.most_common(1)[0]
fleet_forgone = sum(r["quantity"] * r["unit_price"] * r["discount_pct"] / 100 / FX[r["currency"]] for r in fleet if r["status"] == "Delivered")

bf = [r for r in direct_rows if BLACK_FRIDAY[0] <= r["order_date"] <= BLACK_FRIDAY[1]]
bf_rev = C.rev(bf)
direct_dlv = C.delivered(direct_rows)
direct_aov = C.rev(direct_rows) / len(direct_dlv)
ch_rev = C.rev(C.where(country="CH"))
uk_rows = C.where(country="UK")
uk_gbp = sum(D.net_local(r) for r in uk_rows if r["status"] == "Delivered")
uk_eur = C.rev(uk_rows)

mule_after = [r for r in C.where(model="Mule") if r["order_date"] >= PRICE_RISE_DATE and r["status"] == "Delivered"]
mule_after_units = C.units(mule_after)
OLD = {"EUR": round(PRODUCTS["Mule"]["rrp"] / 1.2, 2), "CHF": PRODUCTS["Mule"]["chf"], "GBP": PRODUCTS["Mule"]["gbp"]}
mule_uplift = sum(r["quantity"] * (r["unit_price"] - OLD[r["currency"]]) * (1 - r["discount_pct"] / 100) / FX[r["currency"]] for r in mule_after)

canc_rate = {ch: sum(1 for r in C.where(channel=ch) if r["status"] == "Cancelled") / len(C.where(channel=ch)) * 100 for ch in ["Dealer", "Direct", "Fleet"]}
am_rev = defaultdict(float)
for r in C.where(channel="Dealer"):
    am_rev[ACCOUNT_MANAGER[r["country"]]] += D.net_eur(r)
am_top = max(am_rev, key=am_rev.get)
gold_non_fr = [d for d in gold if dealer_info[d][3] != "FR"]
gold_non_fr_best = max(gold_non_fr, key=lambda d: du[d] / T[d])
b2_dealer = Counter()
for r in C.delivered(C.where(model="Barge 2", channel="Dealer")):
    b2_dealer[r["dealer_id"]] += r["quantity"]
b2_top, b2_top_u = b2_dealer.most_common(1)[0]
b2_dealer_total = sum(b2_dealer.values())
fl_q3 = C.rev(C.where(quarter=3, model="Barge")) + C.rev(C.where(quarter=3, model="Barge 2"))
fl_q4 = C.rev(C.where(quarter=4, model="Barge")) + C.rev(C.where(quarter=4, model="Barge 2"))
pup_built = sum(b["units"] for b in B if b["model"] == "Pup")
mule_built = sum(b["units"] for b in B if b["model"] == "Mule")
pup_claims = [c for c in CL if c["model"] == "Pup"]
mule_claims = [c for c in CL if c["model"] == "Mule"]
pup_appr_cost = sum(c["cost_eur"] for c in pup_claims if c["status"] == "Approved")
new_q4_nlbe = [d for d in DEALERS if d[5] >= "2025-10-01" and d[3] in ("NL", "BE")]
fietskoerier = sum(r["quantity"] for r in fleet if r["customer"] == "Fietskoerier Utrecht" and r["status"] == "Delivered")
mule_h1 = C.units(C.delivered([r for r in C.where(model="Mule") if r["order_date"] < PRICE_RISE_DATE]))
field_km = [42, 51, 38, 0, 58, 47, 33]

# ------------------------------------------------------------------ level 1: find one fact
L = 1
add(L, "Where is Arvenne Cycles' head office?", HQ, "short", ["hb"], ["lookup"], accept=["14 rue des Tanneurs, Lyon"])
add(L, "What is the battery capacity of the Pup?", "400 Wh", "number", ["cat"], ["lookup", "table"], value=400, unit="Wh", tol=0)
add(L, "How much does the Barge 2 weigh?", "39.5 kg", "number", ["cat", "press"], ["lookup"], value=39.5, unit="kg", tol=0)
add(L, "Who is Arvenne's Quality Manager?", "Nadia Kowalczyk", "short", ["org"], ["lookup", "vision-diagram"])
add(L, "How many days of paid leave do employees get per year?", "25 days of paid leave, plus 8 \"Arvenne days\" of reduced working time.", "short", ["hb"], ["lookup"], value=25, unit="days", tol=0)
add(L, "What mileage rate is paid for using a private car on business travel?", "€0.38 per km", "number", ["hb", "travel"], ["lookup"], value=0.38, unit="EUR/km", tol=0)
add(L, "How long is the frame warranty?", "10 years", "number", ["faq", "cat"], ["lookup"], value=10, unit="years", tol=0)
add(L, "What does the Barge 2 Range Extender cost?", "€690 including VAT", "number", ["cat", "press", "m06"], ["lookup"], value=690, unit="EUR", tol=0)
add(L, "On which date did the first-generation Barge reach end of sale?", "30 September 2025", "date", ["m06", "cat", "m09"], ["lookup"])
add(L, "What discount off list price does a Silver-tier dealer get?", "27%", "number", ["dealers"], ["lookup", "table"], value=27, unit="%", tol=0)
add(L, "How many hours is the standard working week at Arvenne?", "35 hours", "number", ["hb"], ["lookup"], value=35, unit="hours", tol=0)
add(L, "Who signed the battery supply agreement on behalf of Voltaris?", "Dr. Heike Brandner, Managing Director of Voltaris Energiesysteme GmbH", "short", ["contract"], ["lookup"])
add(L, "What are the payment terms in the Voltaris supply agreement?", "45 days end of month", "short", ["contract"], ["lookup"])
add(L, "In which city is dealer D017 located?", "Amsterdam (Bakfiets Centraal)", "short", ["dealers"], ["lookup", "table"], accept=["Amsterdam"])
add(L, "Which company supplies the batteries of the Pup?", "Kelda Energy", "short", ["batches", "ir", "contract"], ["lookup"], note="The supply agreement lists no pack for the Pup; the batch register and the incident report name Kelda Energy.")
add(L, "What is the monthly rent of the Utrecht distribution hub?", "€11,800 per month", "number", ["m06", "budget"], ["lookup"], value=11800, unit="EUR/month", tol=0)
add(L, "Who takes the minutes at Arvenne's board meetings?", "Hugo Lambert", "short", ["m06", "m09", "m12"], ["lookup"])
add(L, "How long is the probation period for managers and engineers?", "4 months", "number", ["hb"], ["lookup", "table"], value=4, unit="months", tol=0)
add(L, "Which countries can buy from the arvenne.com webshop?", "France, Germany, the Netherlands and Belgium", "list", ["sreadme"], ["lookup", "listing"], accept=["FR, DE, NL, BE"])
add(L, "What is the torque of the Trike's motor?", "65 Nm (front hub motor)", "number", ["cat"], ["lookup", "table"], value=65, unit="Nm", tol=0)
add(L, "When is a new bike's first service due?", "After 300 km or 3 months, whichever comes first", "short", ["faq", "cat"], ["lookup"])
add(L, "After how many full charge cycles does the battery warranty end, if that comes before two years?", "800 full cycles", "number", ["faq", "cat"], ["lookup"], value=800, unit="cycles", tol=0)
add(L, "What discount do employees get when they buy an Arvenne bike?", "30% off the recommended retail price, one bike per calendar year, to keep at least 12 months", "short", ["hb"], ["lookup"], value=30, unit="%", tol=0)
add(L, "How much is the monthly allowance for employees who commute by bike?", "€40 per month", "number", ["hb"], ["lookup"], value=40, unit="EUR/month", tol=0)
add(L, "Which room did Felix Hartmann stay in at the Zurich hotel?", "Room 312 (single)", "short", ["receipt"], ["lookup", "ocr-print"], accept=["312"])
add(L, "What is the number of the Voltaris delivery note for lot VL-2508-C?", "LS-25-08841", "short", ["dn"], ["lookup", "ocr-print"])
add(L, "What was the temperature on day 1 of the Barge 2 prototype field test?", "18°C (Tuesday 10 June, dry)", "number", ["field"], ["lookup", "ocr-handwriting"], value=18, unit="°C", tol=0)
add(L, "Whose initials are next to the Black Friday item on the Q4 whiteboard?", "LF", "short", ["wb"], ["lookup", "ocr-handwriting"])
add(L, "On what date was the customer letter from Margot Leclerc written?", "3 November 2025", "date", ["letter"], ["lookup", "ocr-handwriting", "cross-lingual"])
add(L, "Which court has jurisdiction over disputes under the Voltaris supply agreement?", "The Commercial Court of Lyon (French law applies)", "short", ["contract"], ["lookup"])
add(L, "What per diem applies on travel days in Switzerland under the updated travel policy?", f"CHF {PER_DIEM_NEW_CH} per travel day", "number", ["travel"], ["lookup"], value=60, unit="CHF", tol=0)
add(L, "Who manages Arvenne's fleet contracts?", "Ben Whitaker (UK & Fleet Sales Manager)", "short", ["sreadme", "org"], ["lookup"])
add(L, "What is the maximum total load of the Mule, rider included?", "210 kg", "number", ["cat"], ["lookup", "table"], value=210, unit="kg", tol=0)
add(L, "When is the next CSE meeting after 13 November 2025?", "15 January 2026 at 14:00, salle Saône, Villefranche site", "date", ["cse"], ["lookup", "cross-lingual"])
add(L, "What severity was incident IR-2025-014 given?", "S2 (safety-relevant, no injury)", "short", ["ir"], ["lookup"])
add(L, "What does Voltaris charge per VP-625 pack?", "€268 excluding VAT", "number", ["contract"], ["lookup", "table"], value=268, unit="EUR", tol=0)
add(L, "What is the Swiss export list price of the Pup?", "CHF 2,670 excluding VAT", "number", ["cat"], ["lookup", "table"], value=2670, unit="CHF", tol=0)
add(L, "How much cash did Arvenne have at 30 September 2025?", "€6.2M", "number", ["deck"], ["lookup"], value=6.2, unit="MEUR", tol=0)
add(L, "Who leads customer care at Arvenne?", "Marco Bellini, Customer Care Lead", "short", ["org", "faq"], ["lookup"])
add(L, "Which Barge 2 accessory lets three children ride in the box, and what does it cost?", "The child bench with 3 harnesses, €249", "short", ["cat"], ["lookup", "table"])

# ------------------------------------------------------------------ level 2: one document, some reasoning
L = 2
add(L, "How many Gold-tier dealers does Arvenne have?", f"{len(gold)}", "number", ["dealers"], ["counting", "table"], value=len(gold), tol=0)
add(L, "How many dealers joined Arvenne's network in 2025, and in which countries?", "4: Bakfietsenhuis Utrecht, Leidse Lastfiets and Zwolle Fietswerk (Netherlands) and Antwerp Cargo Bikes (Belgium)", "list", ["dealers"], ["counting", "filtering", "table"], value=4, tol=0)
add(L, "Which dealer left the network in 2025, and when?", "Velo Werk München (D014, Munich), terminated on 30 June 2025", "short", ["dealers"], ["lookup", "table"])
add(L, "In the Barge 2 power architecture, what fuse rating protects the line between the BMS and the controller?", "30 A", "number", ["cat"], ["vision-diagram"], value=30, unit="A", tol=0, note="Only in the figure, not in the catalogue text.")
add(L, "How many cells does the Barge 2's main battery pack contain?", "52 cells (13S4P: 13 in series × 4 in parallel, 21700 cells)", "number", ["cat"], ["vision-diagram", "calculation"], value=52, unit="cells", tol=0)
add(L, "According to the catalogue chart, what range does the Barge 2 reach in Eco mode with a total load of 200 kg?", "88 km", "number", ["cat"], ["vision-chart"], value=88, unit="km", tol=0)
add(L, "According to the chart in the Q3 investor update, which month had the most bikes delivered between January and September 2025?", (f"{' and '.join(MONTHS[m - 1] for m in best_months)}, tied at {mu[best_month]} bikes each" if len(best_months) > 1 else f"{MONTHS[best_month - 1]} ({mu[best_month]} bikes)"), "short", ["deck"], ["vision-chart", "comparison"], value=mu[best_month], note="By order month." + (" A tie: every tied month must be named." if len(best_months) > 1 else ""))
add(L, "What flat-rate penalty did Voltaris propose to settle the late delivery of lot VL-2508-C?", "A flat 2% of the invoice value (proposed by Jürgen Stolz on 2 September 2025, in German). Arvenne refused and applied clause 7.2.", "short", ["mail"], ["lookup", "cross-lingual"], value=2, unit="%", tol=0)
add(L, "According to Voltaris, when did the strike that delayed lot VL-2508-C begin, and where?", "30 July 2025, in the port of Hamburg", "short", ["mail"], ["lookup", "cross-lingual"])
add(L, "What will the meal voucher be worth from January 2026, and how much of it will the employer pay?", "€10 face value (up from €9), employer share 60%, so €6", "short", ["cse"], ["lookup", "cross-lingual", "calculation"], value=6, unit="EUR", tol=0)
add(L, "Who receives the 2025 value-sharing bonus, and how much is it?", "€600 gross, paid with the December 2025 payroll to every employee present on 30 November 2025, pro rata for part-time staff", "short", ["cse"], ["lookup", "cross-lingual"], value=600, unit="EUR", tol=0)
add(L, "How many order lines were cancelled in 2025?", f"{len(cancelled_rows)}", "number", ["orders"], ["counting", "table"], value=len(cancelled_rows), tol=0)
add(L, "How many bikes were delivered in 2025 (all channels, delivered orders only)?", f"{units_total:,}", "number", ["orders", "sreadme"], ["aggregation", "table"], value=units_total, tol=0)
add(L, "How many warranty claims were still pending at the end of 2025?", f"{pending}", "number", ["claims"], ["counting", "table"], value=pending, tol=0)
add(L, "Which component has the most warranty claims in 2025, and how many?", f"{top_comp[0]}, {top_comp[1]} claims", "short", ["claims"], ["aggregation", "table"], value=top_comp[1], tol=0)
add(L, "How many production batches were built on Line B in 2025?", f"{lineB_batches}", "number", ["batches"], ["counting", "table"], value=lineB_batches, tol=0)
add(L, "What was the Mule's recommended retail price in France before July 2025?", "€4,290 including VAT (it rose to €4,460 on 1 July 2025)", "number", ["m06"], ["lookup", "temporal"], value=4290, unit="EUR", tol=0, note="The autumn catalogue only shows the new price.")
add(L, "On which day of the field test did the motor go into thermal derate, and after how long?", "Day 5, Saturday 14 June: after 28 minutes of climbing the Col du Frêne, power dropped to about 60%", "short", ["field"], ["ocr-handwriting"])
add(L, "What was changed on the prototype during the workshop day of the field test?", "Jonas fitted a 4-piston front caliper with a 220 mm rotor (previously 2-piston, 203 mm) and new pads at both ends; the rear stayed 2-piston, 180 mm", "free", ["field"], ["ocr-handwriting"], rubric=["4-piston front caliper", "220 mm front rotor", "previously 2-piston / 203 mm", "new pads (both ends)"])
add(L, "Which priority on the Q4 whiteboard has two owners?", "Item 3, recovering the cost of the VL-2507-B claims from Voltaris: CD and NK (Camille Dufresne and Nadia Kowalczyk)", "short", ["wb"], ["ocr-handwriting"])
add(L, "What is the total of Felix Hartmann's Zurich hotel bill, and how much accommodation VAT does it include?", "CHF 492.00 in total, including CHF 17.43 of accommodation VAT (3.8%)", "short", ["receipt"], ["ocr-print"], value=492.00, unit="CHF", tol=0)
add(L, "What happened to the packs of lot VL-2508-C that arrived damaged?", "4 VP-750 packs had dented casings; they were quarantined and Voltaris sent free replacements", "short", ["mail", "dn"], ["multi-source", "ocr-handwriting"])
add(L, "What was the root cause of the overheating battery connectors (IR-2025-014)?", "Crimp height below the connector maker's specification at Voltaris, after a crimping die replaced in July was not re-qualified; pull tests were only sampled once per shift, and Arvenne's incoming inspection did not check crimps", "free", ["ir"], ["explanation"], rubric=["crimp height out of spec / high contact resistance", "crimping die replaced in July, not re-qualified", "sampling of pull tests too sparse or incoming inspection blind to crimps"])
add(L, "Which department has the largest opex budget for 2025?", f"{top_dep}, {budget_tot[top_dep]:,.1f} kEUR", "short", ["budget"], ["aggregation", "table"], value=budget_tot[top_dep], unit="kEUR", tol=.5)
add(L, "What is Marketing's opex budget for the fourth quarter of 2025?", f"{mkt_q4:,.1f} kEUR", "number", ["budget"], ["aggregation", "table"], value=mkt_q4, unit="kEUR", tol=.5)
add(L, "What headcount does the 2025 plan foresee at the end of the year?", f"{sum(v[3] for v in D.HEADCOUNT_PLAN.values())} people", "number", ["budget"], ["aggregation", "table"], value=sum(v[3] for v in D.HEADCOUNT_PLAN.values()), tol=0)
add(L, "How many fleet orders were placed in 2025, including cancelled ones?", f"{len(fleet)}", "number", ["orders"], ["counting", "filtering"], value=len(fleet), tol=0)
add(L, "What list price excluding VAT does the order data use for a Barge 2 sold in euros?", f"€{round(5690 / 1.2, 2):,.2f}", "number", ["orders", "sreadme"], ["lookup", "table"], value=round(5690 / 1.2, 2), unit="EUR", tol=.01)
add(L, "Can people working at the plant work remotely under the 2025 handbook?", "No. Plant roles (production, logistics, quality) are not eligible for remote work.", "short", ["hb"], ["lookup", "negation"])
add(L, "Who reports directly to the Head of Operations?", "Elena Vasquez (Plant Manager), Karim Benali (Logistics Manager) and Nadia Kowalczyk (Quality Manager)", "list", ["org"], ["vision-diagram", "listing"])
add(L, "Which models use a mid-drive motor?", "Mule, Barge and Barge 2", "list", ["cat"], ["filtering", "table", "listing"])
add(L, "Which catalogue accessories fit the Mule, and at what price?", "Rear child seat (€139) and the pair of 25 l panniers (€119)", "list", ["cat"], ["filtering", "table", "listing"])
add(L, "What is the takt time on Line B?", "22 minutes", "number", ["batches"], ["lookup", "table"], value=22, unit="min", tol=0)
add(L, "When was the Villefranche plant closed in summer 2025?", "From 4 to 17 August 2025", "date", ["batches"], ["lookup"])
add(L, "What late-delivery penalty does the Voltaris agreement set?", "1.5% of the lot's invoice value per full week of delay, capped at 9% of that value, settled by credit note", "short", ["contract"], ["lookup"])
add(L, "Which Arvenne markets are served only by dealers and fleet contracts?", "Switzerland, the United Kingdom and Austria", "list", ["sreadme"], ["lookup", "negation", "listing"])
add(L, "How many Barge 2 bikes were delivered from 2025 orders?", f"{b2_units}", "number", ["orders"], ["aggregation", "filtering"], value=b2_units, tol=0)
add(L, "Which fleet customers bought the Trike in 2025?", "Stadtbote Berlin (two orders, 12 and 8) and Bruxelles Propre (8)", "list", ["orders"], ["filtering", "listing"])
add(L, "In the Barge 2 architecture, how is the display connected?", "Over the CAN bus", "short", ["cat"], ["vision-diagram"])
add(L, "What is the price of the Barge 2 in US dollars?", "Not in the documents: Arvenne publishes prices in EUR, CHF and GBP only and does not sell in the United States.", "unanswerable", ["cat", "faq"], ["unanswerable"])

# ------------------------------------------------------------------ level 3: several documents, conditions, time
L = 3
add(L, "What was Arvenne's total net revenue in 2025, in euros?", f"{money(rev_total)} (delivered orders, net of discounts, excl. VAT, CHF and GBP converted at the budget rates)", "number", ["orders", "sreadme", "budget"], ["aggregation", "currency", "multi-source"], value=round(rev_total), unit="EUR", tol=.005)
add(L, "Did Arvenne reach its 2025 net revenue target? By how much did it miss or beat it?", f"No. {money(rev_total)} against a target of €12.0M: {money(REVENUE_TARGET_EUR - rev_total)} short ({(rev_total / REVENUE_TARGET_EUR - 1) * 100:+.1f}%)", "free", ["orders", "sreadme", "budget", "m06"], ["aggregation", "comparison", "multi-source"], value=round(rev_total - REVENUE_TARGET_EUR), unit="EUR", tol=.05, rubric=["target was €12.0M", f"actual about {money(rev_total)}", "target missed"])
add(L, "What share of 2025 net revenue came through the webshop?", f"{rev_channel['Direct'] / rev_total * 100:.1f}%", "number", ["orders", "sreadme"], ["aggregation", "ratio"], value=round(rev_channel["Direct"] / rev_total * 100, 1), unit="%", tol=1.0)
add(L, "Which model brought in the most net revenue in 2025, and how much?", f"{max(rev_model, key=rev_model.get)}, {money(max(rev_model.values()))}", "short", ["orders", "sreadme", "budget"], ["aggregation", "comparison"], value=round(max(rev_model.values())), unit="EUR", tol=.01)
add(L, "By how much did net revenue change from Q2 to Q3 2025, and why according to the company?", f"{(rev_q[3] / rev_q[2] - 1) * 100:+.0f}% (from {money(rev_q[2])} to {money(rev_q[3])}); the company attributes it to the August plant closure", "free", ["orders", "deck", "m12"], ["aggregation", "multi-source"], value=round((rev_q[3] / rev_q[2] - 1) * 100), unit="%", tol=1, rubric=["drop of about " + f"{abs((rev_q[3] / rev_q[2] - 1) * 100):.0f}%", "August closure / summer"])
add(L, "Which Gold-tier dealer fell furthest short of its 2025 unit target?", f"{dealer_info[gold_short][1]} ({gold_short}): {du[gold_short]} bikes delivered against a target of {T[gold_short]}", "short", ["orders", "dealers"], ["join", "aggregation", "comparison"])
add(L, "How many dealers met or beat their 2025 unit target?", f"{len(met)} of {len(target_dealers)}", "number", ["orders", "dealers"], ["join", "aggregation", "counting"], value=len(met), tol=0)
add(L, "What per diem applied to a business trip to Berlin that started on 12 August 2025?", "€45: the travel policy update (€55) only applies to trips starting on or after 1 September 2025", "number", ["hb", "travel"], ["temporal", "supersession"], value=45, unit="EUR", tol=0)
add(L, "What per diem applies to a trip to Hamburg starting on 8 September 2025?", "€55 (travel policy update, trips from 1 September 2025)", "number", ["hb", "travel"], ["temporal", "supersession"], value=55, unit="EUR", tol=0)
add(L, "How many days a week can an eligible employee work remotely in February 2026?", "3 days (amendment signed at the CSE of 13 November 2025, from 1 January 2026; the handbook's 2 days applied before)", "number", ["hb", "cse"], ["temporal", "supersession", "cross-lingual"], value=3, unit="days", tol=0)
add(L, "What is the hotel cap per night for a business trip to Paris in October 2025?", "€190 per night, room only, city taxes on top (travel policy update)", "number", ["hb", "travel"], ["temporal", "supersession"], value=190, unit="EUR", tol=0)
add(L, "What is the maximum total load of the Trike?", f"The documents disagree: the catalogue says {PRODUCTS['Trike']['max_load']} kg, the support FAQ says {TRIKE_MAX_LOAD_FAQ} kg. Neither is marked as a correction of the other.", "contradiction", ["cat", "faq"], ["contradiction"], rubric=["catalogue 280 kg", "FAQ 250 kg", "flags the conflict rather than picking one silently"])
add(L, "What was Arvenne's headcount at 30 September 2025?", f"The sources disagree: the Q3 investor update gives {HEADCOUNT_Q3_DECK}, the December board minutes give {HEADCOUNT_Q3_MINUTES_Q4} for the same date.", "contradiction", ["deck", "m12"], ["contradiction"], rubric=["investor update 81", "December minutes 79", "flags the conflict"])
add(L, "When did the Barge 2 launch?", "It depends on what 'launch' means, and the sources agree once read together: launch event in Lyon on 15 September 2025 (investor update, press release), dealer pre-orders from 22 September, customer deliveries and availability from 1 October 2025 (catalogue, press release, September minutes).", "free", ["deck", "press", "cat", "m09"], ["reconciliation", "multi-source"], rubric=["15 September launch event", "1 October availability / deliveries", "explains these are not contradictory (pre-orders 22 September optional)"])
add(L, "What range does the Barge 2 offer?", "60 to 120 km on the standard 750 Wh battery (Eco mode at 100 kg for the top figure, Tour mode at 200 kg for the low one). The 140 km in the investor update is with the optional ~500 Wh Range Extender, not a contradiction of the 120 km.", "free", ["cat", "press", "deck"], ["reconciliation", "multi-source"], rubric=["60-120 km standard", "140 km only with Range Extender"])
add(L, "How much extra range does the Range Extender add to a Barge 2?", "The sources disagree: the press release says up to 60 km more, while the investor update gives up to 140 km with the extender against 120 km without, i.e. about 20 km more. The documents do not settle it.", "contradiction", ["press", "deck", "cat"], ["contradiction", "calculation"], rubric=["press release: up to +60 km", "investor update: 140 vs 120, about +20 km", "flags the conflict"])
add(L, "When did the Utrecht distribution hub go live, and was that the original plan?", "17 November 2025. The June board targeted 3 November; racking installation slipped two weeks (September minutes)", "free", ["m06", "m09", "wb", "m12"], ["temporal", "multi-source"], rubric=["went live 17 November", "originally 3 November"])
add(L, "What was the recommended retail price of a Mule in France in August 2025?", "€4,460 including VAT (4% rise on 1 July 2025 from €4,290, rounded to the nearest €10)", "number", ["m06", "cat"], ["temporal", "calculation"], value=4460, unit="EUR", tol=0)
add(L, "How many Mules were delivered from orders placed before the July 2025 price increase, and how many from orders placed after?", f"{mule_h1} before 1 July, {mule_after_units} from 1 July", "short", ["orders", "m06"], ["aggregation", "temporal"], value=mule_after_units, tol=0)
add(L, "How many bikes were built with battery lot VL-2507-B?", f"{bad_units}", "number", ["batches", "m09"], ["aggregation", "filtering"], value=bad_units, tol=0)
add(L, "Which production batches used battery lot VL-2507-B, and on which lines?", f"{', '.join(b['batch_id'] + ' (' + b['model'] + ', line ' + b['line'] + ')' for b in bad_batches)}", "list", ["batches", "ir"], ["filtering", "listing"])
add(L, "How many battery connector claims were logged by the end of 2025 for bikes built with lot VL-2507-B?", f"{len(bad_conn_all)} (all statuses)", "number", ["claims", "batches"], ["join", "counting"], value=len(bad_conn_all), tol=0)
add(L, "At which dealer did Margot Leclerc buy her bike, what tier is it, and who is its account manager?", "Cycles du Dauphiné in Grenoble (D001), a Gold dealer, managed by Chloé Martin", "short", ["letter", "dealers"], ["ocr-handwriting", "cross-lingual", "join"])
add(L, "A member of the logistics team submits a single expense claim of €3,200. Who has to approve it?", "Both the head of department, Mathieu Okafor (Head of Operations), and the CFO, Camille Dufresne", "short", ["hb", "org"], ["policy-application", "vision-diagram", "multi-source"], rubric=["Mathieu Okafor", "Camille Dufresne"])
add(L, "Who owns the Utrecht hub priority on the Q4 whiteboard? Give the full name and job title.", "Karim Benali, Logistics Manager (initials KB on the whiteboard)", "short", ["wb", "org"], ["ocr-handwriting", "join"])
add(L, "Did Arvenne meet the whiteboard goal for new dealers in the Netherlands and Belgium in Q4?", f"No. The goal was +6; {len(new_q4_nlbe)} joined in Q4 ({', '.join(d[1] for d in new_q4_nlbe)})", "free", ["wb", "dealers"], ["ocr-handwriting", "counting", "multi-source"], value=len(new_q4_nlbe), tol=0, rubric=["goal 6", f"{len(new_q4_nlbe)} joined", "not met"])
add(L, "Did Barge 2 production reach the rate set on the Q4 whiteboard in December?", f"No. The target was 150 a month by December; batches started in December total {b2_dec_prod} Barge 2 ({b2_nov_prod} in November)", "free", ["wb", "batches"], ["ocr-handwriting", "aggregation", "comparison"], value=b2_dec_prod, tol=0, rubric=["target 150 / month", f"{b2_dec_prod} in December", "not reached"], note="The December minutes say Line B reached its *planned* rate in November; the whiteboard goal is a different, higher figure.")
add(L, "How much net revenue did the webshop make during the Black Friday promotion?", f"{money(bf_rev)} from delivered webshop orders placed 24 November to 1 December 2025 (10% off)", "number", ["orders", "wb", "sreadme"], ["filtering", "aggregation", "multi-source"], value=round(bf_rev), unit="EUR", tol=.01)
add(L, "What did the board decide about the Trike, and where had the question been raised?", "Kept in the 2026 range (December board: fleet demand justifies it, no new Trike development before 2027). The 'kill or keep?' question was on the October ops and sales whiteboard, owner IM (Inès Marchetti)", "free", ["wb", "m12"], ["multi-source", "ocr-handwriting"], rubric=["Trike kept in 2026", "raised on the whiteboard / October sync"])
add(L, "How far did the Barge 2 prototype ride in total during the field test?", f"{sum(field_km)} km over 7 days (42 + 51 + 38 + 0 + 58 + 47 + 33)", "number", ["field"], ["ocr-handwriting", "aggregation"], value=sum(field_km), unit="km", tol=0)
add(L, "How much net revenue did Arvenne make in Switzerland in 2025, in euros?", money(ch_rev), "number", ["orders", "sreadme", "budget"], ["filtering", "aggregation", "currency"], value=round(ch_rev), unit="EUR", tol=.01)
add(L, "What was Arvenne's UK net revenue in 2025, in pounds and in euros?", f"£{uk_gbp:,.0f}, i.e. {money(uk_eur)} at the budget rate of 0.85", "short", ["orders", "sreadme", "budget"], ["filtering", "aggregation", "currency"], value=round(uk_eur), unit="EUR", tol=.01)
add(L, "What was the average net value of a delivered webshop order in 2025?", money(direct_aov), "number", ["orders", "sreadme"], ["aggregation", "ratio"], value=round(direct_aov), unit="EUR", tol=.01)
add(L, "Which month of 2025 had the highest net revenue?", f"{MONTHS[max(rev_m, key=rev_m.get) - 1]} ({money(max(rev_m.values()))})", "short", ["orders", "sreadme"], ["aggregation", "comparison"])
add(L, "Which sales channel had the highest cancellation rate in 2025?", f"{max(canc_rate, key=canc_rate.get)}: {max(canc_rate.values()):.1f}% of its order lines (Dealer {canc_rate['Dealer']:.1f}%, Direct {canc_rate['Direct']:.1f}%)", "short", ["orders"], ["aggregation", "ratio", "comparison"], note="Fleet has one cancellation out of 18 lines.")
add(L, "What share of webshop orders were returned in 2025?", f"{len(returned_direct) / len(direct_rows) * 100:.1f}% ({len(returned_direct)} of {len(direct_rows)} order lines)", "number", ["orders"], ["counting", "ratio"], value=round(len(returned_direct) / len(direct_rows) * 100, 1), unit="%", tol=.3)
add(L, "How many bikes did Fietskoerier Utrecht receive in 2025?", f"{fietskoerier}, all first-generation Barge (orders of 25 February and 19 August)", "number", ["orders"], ["filtering", "aggregation"], value=fietskoerier, tol=0)
add(L, "By how much is Operations' opex budget higher in the second half of 2025 than in the first?", f"{ops_h2 - ops_h1:,.1f} kEUR ({ops_h1:,.1f} → {ops_h2:,.1f}, {(ops_h2 / ops_h1 - 1) * 100:+.1f}%)", "number", ["budget"], ["aggregation", "comparison"], value=round(ops_h2 - ops_h1, 1), unit="kEUR", tol=.5)
add(L, "What was Arvenne's net revenue in 2024?", "Not in the documents. The corpus only covers 2025 orders, budget and reporting.", "unanswerable", ["orders", "budget"], ["unanswerable"])
add(L, "How much does Arvenne's CFO earn?", "Not in the documents.", "unanswerable", ["org", "budget"], ["unanswerable"])

# ------------------------------------------------------------------ level 4: expert chains and traps
L = 4
add(L, "During the Barge 2 field test, what was the temperature on the day of the second brake-fade event?", "22°C, on day 6 (Monday 16 June), when the rear brake faded. The first fade was on day 3 (front, 27°C). Day 2's 'second descent' had only a squeal, no fade.", "number", ["field"], ["ocr-handwriting", "temporal", "trap"], value=22, unit="°C", tol=0)
add(L, "What total load was the prototype carrying when the second brake fade happened?", "200 kg (the rider wrote 180, crossed it out and wrote 200, on day 6)", "number", ["field"], ["ocr-handwriting", "trap"], value=200, unit="kg", tol=0)
add(L, "How much late-delivery penalty does Voltaris owe for lot VL-2508-C?", f"{money(penalty, dec=2)}: confirmed for 4 August, delivered 27 August (delivery note) = {late_days} days = {late_weeks} full weeks × 1.5% = {late_weeks * 1.5:.1f}% of the {money(LATE_LOT_VALUE)} invoice value. The force majeure notice was late, and Voltaris's 26 August ETA would give the same 3 full weeks.", "number", ["contract", "mail", "dn"], ["multi-hop", "calculation", "ocr-print", "cross-lingual"], value=round(penalty, 2), unit="EUR", tol=.001, rubric=["3 full weeks", "4.5%", f"{money(penalty, dec=2)}"])
add(L, "Could Voltaris escape the late-delivery penalty on lot VL-2508-C by invoking force majeure?", f"No. Clause 7.4 requires written notice within 5 Business Days of the start of the event. The Hamburg strike began on 30 July 2025, so notice was due by {fm_deadline:%d %B %Y}; Voltaris only invoked force majeure on 18 August.", "free", ["contract", "mail"], ["policy-application", "temporal", "cross-lingual", "multi-hop"], rubric=["5 business days rule", "strike started 30 July", "notice on 18 August, too late", "deadline about 6 August"])
add(L, "Does the invoice value Voltaris confirmed for lot VL-2508-C match the contract prices?", f"Yes: 240 × VP-625 at €268 + 380 × VP-750 at €318 = €64,320 + €120,840 = {money(LATE_LOT_VALUE, dec=2)}, the value in Jürgen Stolz's confirmation", "free", ["contract", "mail", "dn"], ["calculation", "multi-hop", "cross-lingual"], value=LATE_LOT_VALUE, unit="EUR", tol=0, rubric=["quantities 240 and 380", "prices 268 and 318", "185,160 matches"])
add(L, "Does lot VL-2507-B trigger the field-failure clause of the Voltaris agreement?", f"Yes. Clause 9.4 triggers above 1.0% approved battery-related claims per bike built with the lot. {len(bad_batt_appr)} approved battery-related claims (connectors and cells) on {bad_units} bikes = {bad_rate:.1f}%.", "free", ["contract", "claims", "batches", "m12"], ["join", "policy-application", "multi-hop"], value=round(bad_rate, 1), unit="%", tol=.3, rubric=["threshold 1.0%", f"{len(bad_batt_appr)} approved battery-related claims", f"{bad_units} bikes", "yes, triggered"])
add(L, "How much should Voltaris reimburse Arvenne under clause 9.4 for lot VL-2507-B, based on the year-end claims register?", f"{money(reimb, dec=2)}: {money(reimb - 40 * len(bad_batt_appr), dec=2)} of approved battery-related claim costs plus €40 handling × {len(bad_batt_appr)} claims. Pending and rejected claims are excluded, as the December board specified.", "number", ["contract", "claims", "batches", "m12"], ["join", "aggregation", "policy-application", "multi-hop"], value=round(reimb, 2), unit="EUR", tol=.002)
add(L, "Which batch built Margot Leclerc's bike, with which battery lot, on which line, and is her claim in the register?", f"Batch {LB['batch_id']} (Mule, line {LB['line']}, started {LB['start_date']:%d %B %Y}), battery lot {LB['battery_lot']}, the lot behind the connector incident, so her bike is covered by the inspection campaign. Her claim is logged as {letter_claim['claim_id']} on 5 November 2025, still pending.", "free", ["letter", "batches", "claims", "ir"], ["ocr-handwriting", "cross-lingual", "join", "multi-hop"], rubric=[LB["batch_id"], BAD_LOT, f"line {LB['line']}", letter_claim["claim_id"] + " pending"])
add(L, "How much of Felix Hartmann's Zurich hotel bill can be reimbursed, and who approves the claim?", "CHF 467.00: the trip (14 October 2025) falls under the updated policy, so rooms are capped at CHF 230 a night (2 × 230 = 460 instead of 476), city taxes are reimbursed on top (7.00) and the minibar (9.00) is never reimbursed. The CHF 16 excess would need his line manager's written approval before the trip. At about €497 the claim is under €500, so his line manager, Ruth Achterberg, approves it.", "free", ["receipt", "travel", "hb", "org", "budget"], ["ocr-print", "policy-application", "temporal", "currency", "multi-hop"], value=467.00, unit="CHF", tol=0, rubric=["new policy applies (trip after 1 September)", "cap CHF 230 per night", "city tax reimbursed, minibar not", "CHF 467", "Ruth Achterberg approves"])
add(L, "How does the battery connector claim rate of lot VL-2507-B compare with Arvenne's other Voltaris lots?", f"{len(bad_conn_all) / bad_units * 100:.1f}% ({len(bad_conn_all)} connector claims on {bad_units} bikes) against {other_v_conn / other_v_units * 100:.2f}% ({other_v_conn} on {other_v_units:,}) for all other Voltaris lots combined: about {(len(bad_conn_all) / bad_units) / (other_v_conn / other_v_units):.0f} times higher", "free", ["claims", "batches"], ["join", "aggregation", "ratio"], value=round(len(bad_conn_all) / bad_units * 100, 1), unit="%", tol=.3)
add(L, "How did front-loader net revenue (Barge and Barge 2 together) change from Q3 to Q4 2025?", f"From {money(fl_q3)} in Q3 to {money(fl_q4)} in Q4 ({(fl_q4 / fl_q3 - 1) * 100:+.0f}%). Q4 is Barge 2 only, the first-generation Barge having stopped on 30 September.", "free", ["orders", "sreadme", "budget", "m06"], ["aggregation", "temporal", "comparison"], value=round(fl_q4), unit="EUR", tol=.01)
add(L, "Among Gold-tier dealers outside France, which one achieved the highest percentage of its 2025 unit target?", f"{dealer_info[gold_non_fr_best][1]} ({gold_non_fr_best}, {dealer_info[gold_non_fr_best][2]}): {du[gold_non_fr_best]} bikes for a target of {T[gold_non_fr_best]}, {du[gold_non_fr_best] / T[gold_non_fr_best] * 100:.0f}%", "short", ["orders", "dealers"], ["join", "filtering", "ratio", "comparison"])
add(L, "Which account manager's dealers generated the most net revenue in 2025?", f"{am_top}, {money(am_rev[am_top])} (" + ", ".join(f"{k} {money(v)}" for k, v in sorted(am_rev.items(), key=lambda x: -x[1])) + ")", "short", ["orders", "dealers", "sreadme", "budget"], ["join", "aggregation", "currency"], value=round(am_rev[am_top]), unit="EUR", tol=.01)
add(L, "How much extra net revenue did the July 2025 Mule price increase bring, on delivered orders placed from 1 July?", f"{money(mule_uplift)} over {mule_after_units} bikes, comparing each line's price with the pre-July list price in its currency after the same discount", "number", ["orders", "m06", "cat", "budget"], ["calculation", "temporal", "currency", "multi-hop"], value=round(mule_uplift), unit="EUR", tol=.02)
add(L, "How much revenue did Arvenne give up through fleet discounts in 2025?", f"{money(fleet_forgone)} on delivered fleet orders (list price × discount, converted to EUR)", "number", ["orders", "sreadme", "budget"], ["calculation", "filtering", "currency"], value=round(fleet_forgone), unit="EUR", tol=.01)
add(L, "Which fleet customer took delivery of the most bikes in 2025?", f"{fleet_top[0][0]}, {fleet_top[0][1]} bikes. {fleet_naive[0]} ordered more ({fleet_naive[1]}) but cancelled {fleet_naive[1] - fleet_units_ok[fleet_naive[0]]}, so only {fleet_units_ok[fleet_naive[0]]} were delivered.", "short", ["orders", "sreadme"], ["filtering", "aggregation", "trap"], value=fleet_top[0][1], tol=0)
add(L, "Is the Barge 2's 120 km range claim supported by the prototype field test?", "Only in the catalogue's best case. 120 km is Eco mode with 100 kg; the catalogue's own chart gives 88 km in Eco and 60 km in Tour at 200 kg. In the field test at 200 kg and 31°C the prototype used 91% of its battery for 58 km (about 64 km on a full charge) and the rider wrote that range at 200 kg in heat was 'way below the 120 km claim'.", "free", ["cat", "field", "press"], ["vision-chart", "ocr-handwriting", "calculation", "synthesis"], rubric=["120 km is Eco at 100 kg", "chart at 200 kg (88 Eco / 60 Tour)", "field test day 5: 58 km for 91% of battery (≈64 km)", "rider's note that range is way below the claim"])
add(L, "Why was battery lot VL-2507-B still used after the summer closure, and how many bikes did that add to the lot?", f"Lot VL-2508-C was meant for the restart after the closure (Karim Benali's 2 July order, due 4 August) but arrived on 27 August. Production restarted on 18 August, so batches {', '.join(bad_after_restart_batches)} built {bad_after_restart} more bikes with VL-2507-B until VL-2508-C took over on 28 August.", "free", ["mail", "dn", "batches", "ir"], ["multi-hop", "temporal", "explanation", "cross-lingual"], value=bad_after_restart, tol=0, rubric=["VL-2508-C was intended for the restart and was late", "restart 18 August", f"{bad_after_restart} bikes after restart"])
add(L, "From January 2026, how much remote-work allowance would an employee receive in a month in which they work remotely three days every week?", "€30: €2.50 per remote day for 12 or 13 days is €30 to €32.50, and the allowance is capped at €30 a month", "number", ["cse", "hb"], ["calculation", "cross-lingual", "policy-application"], value=30, unit="EUR", tol=0)
add(L, "Which Spanish dealer sold the most Barge 2 bikes in 2025?", "None. Arvenne has no dealer in Spain and does not sell there yet (support FAQ); the dealer list covers France, Germany, the Netherlands, Belgium, Switzerland, the United Kingdom and Austria.", "unanswerable", ["dealers", "faq"], ["unanswerable", "false-premise"])
add(L, "Why was the Pup recalled in 2025?", "It was not. There is no recall: a voluntary inspection campaign covers bikes built with Voltaris lot VL-2507-B (Mules, Barges and a Trike batch). The Pup uses Kelda Energy packs and was not affected.", "unanswerable", ["faq", "ir", "batches"], ["false-premise"])
add(L, "How much does the Range Extender for the Pup cost?", "There is none. The Range Extender fits the Barge 2 only, and the December board decided there will be no Pup Range Extender in 2026.", "unanswerable", ["cat", "faq", "m12"], ["false-premise"])
add(L, "What did the board decide at its March 2026 meeting?", "Not in the documents. The December 2025 minutes only schedule the next meeting for 17 March 2026.", "unanswerable", ["m12"], ["unanswerable", "temporal"])
add(L, "Which dealer delivered the most Barge 2 bikes in 2025, and what share of all Barge 2 dealer sales is that?", f"{dealer_info[b2_top][1]} ({b2_top}): {b2_top_u} of {b2_dealer_total} Barge 2 sold through dealers, {b2_top_u / b2_dealer_total * 100:.1f}%", "short", ["orders", "dealers"], ["join", "aggregation", "ratio"], value=b2_top_u, tol=0)
add(L, "What did approved warranty claims on the Pup cost in 2025, and how does the Pup's claim rate per 100 bikes built compare with the Mule's?", f"{money(pup_appr_cost, dec=2)} of approved Pup claims. {len(pup_claims) / pup_built * 100:.1f} claims per 100 Pups built ({len(pup_claims)} on {pup_built}) against {len(mule_claims) / mule_built * 100:.1f} per 100 Mules ({len(mule_claims)} on {mule_built}), all statuses; the Mule is higher partly because of the VL-2507-B connector claims.", "free", ["claims", "batches"], ["join", "aggregation", "ratio", "comparison"], value=round(pup_appr_cost, 2), unit="EUR", tol=.005)
add(L, "The September board minutes give a number of connector claims for lot VL-2507-B. How many more were logged by the end of the year, and how many of the year-end total were approved?", f"{len(bad_conn_sep)} at 23 September, {len(bad_conn_all)} at year end, so {len(bad_conn_all) - len(bad_conn_sep)} more; {sum(1 for c in bad_conn_all if c['status'] == 'Approved')} of the {len(bad_conn_all)} are approved", "free", ["m09", "claims", "batches"], ["temporal", "join", "counting"], value=len(bad_conn_all) - len(bad_conn_sep), tol=0)
add(L, "A Barge 2 owner wants maximum range for a 200 kg family load. What should they buy and what range can they expect from the documents?", "The ~500 Wh Range Extender (€690, Barge 2 only), which adds a 13S3P pack behind its own diode isolation. At 200 kg the 750 Wh main pack alone gives 88 km in Eco and 60 km in Tour. The documents give no figure with the extender at 200 kg, and their best-case figures for it disagree (up to +60 km in the press release, 140 km in total in the investor update).", "free", ["cat", "deck", "faq", "press"], ["synthesis", "vision-chart", "vision-diagram", "partial-answer"], rubric=["Range Extender, €690, Barge 2 only", "88 km Eco / 60 km Tour at 200 kg without it", "no figure with the extender at 200 kg"])
add(L, "How many cells does a Barge 2 carry with the Range Extender fitted, and why is only one pack charged from the charge port?", "91 cells: 52 in the 13S4P main pack and 39 in the 13S3P Range Extender. The charge port and 4 A charger feed the main pack only; a diode isolation module (DM-2) keeps the packs from cross-charging, and each pack has its own BMS.", "free", ["cat"], ["vision-diagram", "calculation", "explanation"], value=91, unit="cells", tol=0, rubric=["91 cells (52 + 39)", "diode isolation prevents cross-charging", "charger feeds main pack only"])
add(L, "Margot Leclerc asks for her taxi to be refunded. What do Arvenne's documents say about reimbursing a customer's costs like this?", "Nothing. The warranty covers repair or replacement of the bike's parts (FAQ, catalogue) and the inspection campaign replaces the connector free of charge, but no document covers refunding a customer's taxi or other consequential costs. Her claim is still pending in the register.", "unanswerable", ["letter", "faq", "ir", "claims"], ["unanswerable", "ocr-handwriting", "cross-lingual"], rubric=["no policy on consequential costs in the documents", "connector replacement is covered free", "claim pending"])
add(L, "If a Gold dealer in Zurich ordered two Barge 2 at list price, what would Arvenne invoice in euros?", f"CHF 4,760 × 2 × (1 − 30%) = CHF 6,664, i.e. {money(6664 / 0.94, dec=2)} at the budget rate of 0.94 CHF per euro (excl. VAT)", "number", ["cat", "dealers", "budget"], ["calculation", "currency", "multi-hop"], value=round(6664 / 0.94, 2), unit="EUR", tol=.002)


# ------------------------------------------------------------------ write
def main():
    for i, q in enumerate(Q, 1):
        q["id"] = f"ARB-{i:03d}"
    lv = Counter(q["level"] for q in Q)
    out = ROOT / "dataset"
    out.mkdir(exist_ok=True)
    keys = ["id", "level", "question", "answer", "answer_type", "value", "unit", "tolerance", "accept", "rubric", "sources", "skills", "note"]
    with (out / "questions.jsonl").open("w", encoding="utf-8") as f:
        for q in Q:
            f.write(json.dumps({k: q[k] for k in keys}, ensure_ascii=False) + "\n")
    with (out / "questions_blind.jsonl").open("w", encoding="utf-8") as f:
        for q in Q:
            f.write(json.dumps({"id": q["id"], "level": q["level"], "question": q["question"]}, ensure_ascii=False) + "\n")
    print(len(Q), dict(sorted(lv.items())))
    print(Counter(q["answer_type"] for q in Q))
    sk = Counter(s for q in Q for s in q["skills"])
    print(sk.most_common())


if __name__ == "__main__":
    main()
