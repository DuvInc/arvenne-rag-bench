"""Shared computations over the generated tables, used both to write documents and to compute
reference answers, so a number a document states is the number the data gives."""

from collections import Counter, defaultdict
from datetime import date

import data as D
from world import *  # noqa: F403

ALL = D.build_all()
ORDERS, BATCHES, CLAIMS, BUDGET = ALL["orders"], ALL["batches"], ALL["claims"], ALL["budget"]
LETTER_SERIAL, LETTER_BATCH = ALL["letter_serial"], ALL["letter_batch"]


def q_of(day):
    return (day.month - 1) // 3 + 1


def delivered(rows=None):
    return [r for r in (rows if rows is not None else ORDERS) if r["status"] == "Delivered"]


def rev(rows):
    return sum(D.net_eur(r) for r in rows)


def units(rows):
    return sum(r["quantity"] for r in rows)


def where(**kw):
    out = []
    for r in ORDERS:
        ok = True
        for k, v in kw.items():
            if k == "quarter":
                ok = q_of(r["order_date"]) == v
            elif k == "month":
                ok = r["order_date"].month == v
            elif k == "between":
                ok = v[0] <= r["order_date"] <= v[1]
            elif callable(v):
                ok = v(r[k])
            else:
                ok = r[k] == v
            if not ok:
                break
        if ok:
            out.append(r)
    return out


def serial_int(s):
    return int(s.split("-")[1])


def batch_of(serial):
    n = serial_int(serial)
    for b in BATCHES:
        if b["serial_from"] <= n <= b["serial_to"]:
            return b
    return None


def lot_units(lot):
    return sum(b["units"] for b in BATCHES if b["battery_lot"] == lot)


def claims_where(lot=None, components=None, status=None, until=None, model=None):
    out = []
    for c in CLAIMS:
        b = batch_of(c["serial_number"])
        if lot and b["battery_lot"] != lot:
            continue
        if components and c["component"] not in components:
            continue
        if status and c["status"] not in status:
            continue
        if until and c["claim_date"] > until:
            continue
        if model and c["model"] != model:
            continue
        out.append(c)
    return out


def dealer_units():
    u = Counter()
    for r in delivered(where(channel="Dealer")):
        u[r["dealer_id"]] += r["quantity"]
    return u


def dealer_targets():
    """Targets were set in January from a plan; derive them deterministically from the outcome."""
    import random
    rng = random.Random(77)
    du = dealer_units()
    t = {}
    for did, name, city, c, tier, onb, status in DEALERS:
        if onb >= "2025-10-01":
            t[did] = 10
        elif status.startswith("Terminated"):
            t[did] = 90
        else:
            t[did] = max(20, int(round(du[did] * rng.uniform(.82, 1.22) / 5) * 5))
    return t


TARGETS = dealer_targets()


def business_days_after(start, n):
    from datetime import timedelta
    day, k = start, 0
    while k < n:
        day += timedelta(days=1)
        if day.weekday() < 5 and day not in FR_HOLIDAYS:
            k += 1
    return day


FR_HOLIDAYS = {date(2025, 1, 1), date(2025, 4, 21), date(2025, 5, 1), date(2025, 5, 8), date(2025, 5, 29),
               date(2025, 6, 9), date(2025, 7, 14), date(2025, 8, 15), date(2025, 11, 1), date(2025, 11, 11),
               date(2025, 12, 25)}


def monthly_units_delivered(months):
    return {m: units(delivered(where(month=m))) for m in months}


def headline():
    q3 = delivered(where(quarter=3))
    q2 = delivered(where(quarter=2))
    return dict(q3_rev=rev(q3), q2_rev=rev(q2), q3_units=units(q3), q2_units=units(q2),
                active_dealers_sep30=sum(1 for d in DEALERS if d[5] <= "2025-09-30" and d[6] == "Active"))


if __name__ == "__main__":
    h = headline()
    print(h)
    print("targets", TARGETS)
    print("dealer units", dealer_units())
    print("bad-lot connector claims by Sep 23:", len(claims_where(lot=BAD_LOT, components=["Battery connector"], until=date(2025, 9, 23))))
    print("letter batch", LETTER_BATCH)
