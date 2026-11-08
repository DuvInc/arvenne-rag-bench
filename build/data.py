"""Seeded tables: orders, production batches, warranty claims, budget. Deterministic."""

import math
import random
from datetime import date, timedelta

from world import *  # noqa: F403

rng = random.Random(2025)

SEASON = {1: .55, 2: .6, 3: .9, 4: 1.15, 5: 1.3, 6: 1.3, 7: 1.1, 8: .65, 9: 1.1, 10: 1.0, 11: .95, 12: .7}
BASE = {"Mule": 128, "Barge": 82, "Barge 2": 0, "Trike": 28, "Pup": 66}
BARGE2_MONTH = {9: 24, 10: 118, 11: 142, 12: 126}

CHANNEL_W = {"Dealer": .66, "Direct": .34}
DEALER_COUNTRY_W = {"FR": .36, "DE": .22, "NL": .15, "BE": .07, "CH": .08, "UK": .08, "AT": .04}
DIRECT_COUNTRY_W = {"FR": .55, "DE": .25, "NL": .14, "BE": .06}
TIER_W = {"Gold": 3.0, "Silver": 1.8, "Bronze": 1.0}


def d(s):
    return date.fromisoformat(s)


def days_in_month(m):
    return (date(YEAR + (m == 12), m % 12 + 1, 1) - date(YEAR, m, 1)).days


def pick(weights):
    r, acc = rng.random() * sum(weights.values()), 0
    for k, w in weights.items():
        acc += w
        if r <= acc:
            return k
    return k


def unit_price(model, currency, day):
    p = PRODUCTS[model]
    after = model == "Mule" and day >= PRICE_RISE_DATE
    if currency == "EUR":
        return round((p["rrp_after"] if after else p["rrp"]) / (1 + VAT_FR), 2)
    if currency == "CHF":
        return float(p["chf_after"] if after else p["chf"])
    return float(p["gbp_after"] if after else p["gbp"])


def currency_of(country):
    return {"CH": "CHF", "UK": "GBP"}.get(country, "EUR")


def model_window(model):
    if model == "Barge":
        return date(YEAR, 1, 1), BARGE_END_OF_SALE
    if model == "Barge 2":
        return BARGE2_FIRST_ORDER, date(YEAR, 12, 31)
    return date(YEAR, 1, 1), date(YEAR, 12, 31)


def eligible_dealers(country, day):
    out = []
    for did, name, city, c, tier, onb, status in DEALERS:
        if c != country or d(onb) > day:
            continue
        if status.startswith("Terminated") and day > d(status.split()[-1]):
            continue
        out.append((did, tier))
    return out


def build_orders():
    rows = []
    for m in range(1, 13):
        for model in PRODUCTS:
            target = BARGE2_MONTH.get(m, 0) if model == "Barge 2" else round(BASE[model] * SEASON[m] * rng.uniform(.9, 1.1))
            lo, hi = model_window(model)
            start, end = max(lo, date(YEAR, m, 1)), min(hi, date(YEAR, m, days_in_month(m)))
            if start > end or target == 0:
                continue
            span = (end - start).days
            units = 0
            while units < target:
                day = start + timedelta(days=rng.randint(0, span))
                ch = pick(CHANNEL_W)
                if model == "Barge 2" and day < BARGE2_DELIVERIES:
                    ch = "Dealer"  # pre-orders through dealers only
                if ch == "Direct" and BLACK_FRIDAY[0] <= day <= BLACK_FRIDAY[1]:
                    pass
                if ch == "Dealer":
                    country = pick(DEALER_COUNTRY_W)
                    ds = eligible_dealers(country, day)
                    did, tier = rng.choices(ds, [TIER_W[t] for _, t in ds])[0]
                    qty = rng.choices([1, 2, 3, 4], [.55, .27, .12, .06])[0]
                    disc = TIER_DISCOUNT[tier]
                else:
                    country = pick(DIRECT_COUNTRY_W)
                    did, qty = "", 1
                    disc = 10 if BLACK_FRIDAY[0] <= day <= BLACK_FRIDAY[1] else (5 if rng.random() < .15 else 0)
                r = rng.random()
                status = "Cancelled" if r < .04 else ("Returned" if ch == "Direct" and r < .075 else "Delivered")
                cur = currency_of(country)
                rows.append(dict(order_date=day, channel=ch, country=country, dealer_id=did, customer="",
                                 model=model, quantity=qty, unit_price=unit_price(model, cur, day),
                                 currency=cur, discount_pct=disc, status=status))
                units += qty
    # Black Friday boost for direct: extra orders
    for i in range(46):
        day = BLACK_FRIDAY[0] + timedelta(days=rng.randint(0, 7))
        model = rng.choices(["Mule", "Barge 2", "Pup", "Trike"], [.4, .25, .3, .05])[0]
        country = pick(DIRECT_COUNTRY_W)
        status = "Cancelled" if rng.random() < .04 else ("Returned" if rng.random() < .04 else "Delivered")
        rows.append(dict(order_date=day, channel="Direct", country=country, dealer_id="", customer="",
                         model=model, quantity=1, unit_price=unit_price(model, "EUR", day), currency="EUR",
                         discount_pct=10, status=status))
    for cust, ds, country, model, qty, disc, status in FLEET:
        day = d(ds)
        cur = currency_of(country)
        rows.append(dict(order_date=day, channel="Fleet", country=country, dealer_id="", customer=cust,
                         model=model, quantity=qty, unit_price=unit_price(model, cur, day), currency=cur,
                         discount_pct=disc, status=status))
    rows.sort(key=lambda r: (r["order_date"], r["channel"], r["model"]))
    for i, r in enumerate(rows, 1):
        r["order_id"] = f"SO-25-{i:05d}"
    return rows


def net_local(r):
    return r["quantity"] * r["unit_price"] * (1 - r["discount_pct"] / 100)


def net_eur(r):
    if r["status"] != "Delivered":
        return 0.0
    return net_local(r) / FX[r["currency"]]


def lot_for(model, day):
    lots = KELDA_LOTS if PRODUCTS[model]["supplier"] == "Kelda Energy" else VOLTARIS_LOTS
    for name, a, b in lots:
        if d(a) <= day <= d(b):
            return name
    raise ValueError(day)


def working_days(m):
    out = []
    for i in range(days_in_month(m)):
        day = date(YEAR, m, i + 1)
        if day.weekday() < 5 and not (PLANT_CLOSURE[0] <= day <= PLANT_CLOSURE[1]):
            out.append(day)
    return out


def build_production(orders):
    """Monthly production per model follows that month's non-cancelled demand, in batches."""
    plan = []
    for m in range(1, 13):
        wd = working_days(m)
        for model in PRODUCTS:
            units = sum(r["quantity"] for r in orders if r["order_date"].month == m and r["model"] == model and r["status"] != "Cancelled")
            if units == 0:
                continue
            n = max(1, math.ceil(units / 45))
            sizes = [units // n + (1 if i < units % n else 0) for i in range(n)]
            for i, size in enumerate(sizes):
                if model == "Barge 2":
                    pool = [x for x in wd if x >= date(2025, 9, 15)]
                else:
                    pool = wd
                day = pool[min(len(pool) - 1, int((i + rng.uniform(.1, .9)) * len(pool) / n))]
                plan.append(dict(model=model, start_date=day, units=size))
    plan.sort(key=lambda b: (b["start_date"], PRODUCTS[b["model"]]["line"], b["model"]))
    serial = 1
    for i, b in enumerate(plan, 1):
        b["batch_id"] = f"B25-{i:03d}"
        b["line"] = PRODUCTS[b["model"]]["line"]
        b["serial_from"] = serial
        b["serial_to"] = serial + b["units"] - 1
        serial += b["units"]
        b["battery_supplier"] = PRODUCTS[b["model"]]["supplier"]
        b["battery_lot"] = lot_for(b["model"], b["start_date"])
    return plan


def sn(n):
    return f"ARV25-{n:05d}"


COMPONENTS = {
    # component: (base probability, cost range, descriptions)
    "Battery connector": (.003, (180, 420), ["Connector hot after charging", "Burnt smell at battery connector", "Intermittent power cut, connector discoloured", "Melted connector housing"]),
    "Battery cell": (.003, (450, 720), ["Range dropped by half", "Battery will not charge past 60%", "Cell imbalance error E07"]),
    "Motor": (.006, (300, 880), ["Grinding noise from motor", "Motor cuts out under load", "Torque sensor fault"]),
    "Brakes": (.009, (60, 160), ["Rear brake squeal", "Hydraulic leak front caliper", "Brake lever spongy"]),
    "Frame": (.0008, (500, 1400), ["Crack near box mount", "Paint blistering on frame", "Kickstand mount loose"]),
    "Electronics": (.006, (90, 340), ["Display blank", "Lights flicker", "App will not pair"]),
    "Drivetrain": (.008, (70, 260), ["Belt slipping", "Chain snapped", "Hub gear skips"]),
}
BATTERY_COMPONENTS = ("Battery connector", "Battery cell")


def build_claims(batches):
    claims = []
    end = date(YEAR, 12, 31)
    for b in batches:
        for s in range(b["serial_from"], b["serial_to"] + 1):
            for comp, (p, (lo, hi), descs) in COMPONENTS.items():
                if comp == "Battery connector" and b["battery_lot"] == BAD_LOT:
                    p = .045
                if rng.random() < p:
                    lag = rng.randint(18, 150) if comp != "Battery connector" or b["battery_lot"] != BAD_LOT else rng.randint(20, 100)
                    cd = b["start_date"] + timedelta(days=lag)
                    if cd > end:
                        continue
                    status = rng.choices(["Approved", "Rejected", "Pending"], [.82, .08, .10])[0]
                    if cd > date(2025, 12, 10):
                        status = "Pending"
                    claims.append(dict(claim_date=cd, serial_number=sn(s), model=b["model"], component=comp,
                                       description=rng.choice(descs), cost_eur=round(rng.uniform(lo, hi), 2),
                                       status=status))
    return claims


def plant_letter_claim(batches, claims):
    """Margot Leclerc's Mule: a VL-2507-B Mule; her claim is logged on 2025-11-05, pending."""
    cand = [b for b in batches if b["model"] == "Mule" and b["battery_lot"] == BAD_LOT]
    b = cand[0]
    taken = {c["serial_number"] for c in claims}
    for s in range(b["serial_from"] + 17, b["serial_to"] + 1):
        if sn(s) not in taken:
            break
    claims.append(dict(claim_date=date(2025, 11, 5), serial_number=sn(s), model="Mule",
                       component="Battery connector", description="Melted connector housing, customer letter received",
                       cost_eur=0.0, status="Pending"))
    return sn(s), b


def finalize_claims(claims):
    claims.sort(key=lambda c: (c["claim_date"], c["serial_number"]))
    for i, c in enumerate(claims, 1):
        c["claim_id"] = f"WC-25-{i:04d}"
        if c["status"] == "Pending" and c["cost_eur"] == 0.0:
            pass
    return claims


DEPTS = ["Engineering", "Operations", "Sales", "Marketing", "Finance & Admin"]


def build_budget():
    """Monthly opex budget in kEUR, by department."""
    base = {"Engineering": 182, "Operations": 236, "Sales": 121, "Marketing": 64, "Finance & Admin": 78}
    shape = {
        "Engineering": [1, 1, 1, 1.02, 1.02, 1.04, 1.04, .9, 1.06, 1.06, 1.06, 1.08],
        "Operations": [.92, .92, .97, 1, 1.03, 1.05, 1.05, .78, 1.12, 1.18, 1.22, 1.2],
        "Sales": [.95, .95, 1, 1.02, 1.02, 1.02, 1, .85, 1.08, 1.12, 1.14, 1.06],
        "Marketing": [.7, .75, 1.1, 1.2, 1.1, .95, .8, .55, 1.65, 1.5, 1.45, .8],
        "Finance & Admin": [1, 1, 1, 1, 1, 1, 1, .95, 1, 1.02, 1.02, 1.08],
    }
    return {dep: [round(base[dep] * k, 1) for k in shape[dep]] for dep in DEPTS}


HEADCOUNT_PLAN = {  # end of quarter
    "Engineering": [14, 15, 16, 17],
    "Operations": [30, 34, 38, 42],
    "Sales": [11, 12, 13, 14],
    "Marketing": [5, 5, 6, 6],
    "Finance & Admin": [6, 6, 6, 7],
    "Executive": [1, 1, 1, 1],
}


def build_all():
    orders = build_orders()
    batches = build_production(orders)
    claims = build_claims(batches)
    letter_serial, letter_batch = plant_letter_claim(batches, claims)
    claims = finalize_claims(claims)
    return dict(orders=orders, batches=batches, claims=claims, budget=build_budget(),
                letter_serial=letter_serial, letter_batch=letter_batch)


if __name__ == "__main__":
    D = build_all()
    o = D["orders"]
    print("orders", len(o), "units", sum(r["quantity"] for r in o if r["status"] == "Delivered"))
    print("net EUR", round(sum(net_eur(r) for r in o)))
    print("batches", len(D["batches"]), "claims", len(D["claims"]))
    bad = [b for b in D["batches"] if b["battery_lot"] == BAD_LOT]
    print("bad lot units", sum(b["units"] for b in bad), [(b["batch_id"], b["model"]) for b in bad])
    print("bad lot connector claims", sum(1 for c in D["claims"] if c["component"] == "Battery connector"
          and any(b["serial_from"] <= int(c["serial_number"][-5:]) <= b["serial_to"] for b in bad)))
    print("letter", D["letter_serial"], D["letter_batch"]["batch_id"])
