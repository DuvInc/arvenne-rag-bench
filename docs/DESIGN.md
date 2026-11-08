# Design notes

For maintainers. It spoils the benchmark: do not feed it to a system under test.

## One source of truth

`build/world.py` holds every fact of the company (people, products, prices, dates, contract terms, policy values, planted disagreements). `build/data.py` generates the tables from a fixed seed. `build/calc.py` computes over them, and both the documents (`render_text.py`, `render_visual.py`) and the reference answers (`questions.py`) call it. A number a document states is therefore the number the data gives, unless it is a planted contradiction. `scripts/verify.py` then recomputes 38 answers from the published CSV and XLSX files alone and checks what text extraction can and cannot see.

## Planted contradictions

| Topic | Source A | Source B | Expected answer |
| --- | --- | --- | --- |
| Trike max load | catalogue: 280 kg | FAQ: 250 kg | report both, unresolved |
| Headcount at 30 Sept | investor update: 81 | December minutes: 79 | report both, unresolved |
| Range Extender gain | press release: up to +60 km | investor update: 140 vs 120 km, so +20 | report both, unresolved |

## Apparent contradictions that resolve

| Topic | Looks like | Resolved by |
| --- | --- | --- |
| Barge 2 launch | 15 Sept (deck, press) vs 1 Oct (catalogue, press) | September minutes: event 15 Sept, pre-orders 22 Sept, deliveries 1 Oct |
| Barge 2 range | 120 km (catalogue) vs 140 km (deck) | 140 km is with the Range Extender |
| Per diem, hotel caps | €45 / €150 (handbook) vs €55 / per-country caps (update) | trip start date vs 1 Sept 2025 |
| Remote days | 2 (handbook) vs 3 (French CSE minutes) | 3 from 1 Jan 2026 |
| Utrecht go-live | 3 Nov (June minutes) vs 17 Nov (whiteboard, Sept and Dec minutes) | slipped two weeks |
| Mule price | €4,290 (June minutes, order data before July) vs €4,460 (catalogue) | +4% on 1 July 2025 |

## Traps

- **Second brake fade** (field notes, handwriting): day 2 says "2nd descent… squeal, no fade"; the first fade is day 3; the second is day 6 at 22°C. Day 5 is the hottest day (31°C) and has a different incident. The day-6 load is written 180, crossed out, then 200.
- **Fleet customer with most bikes**: GreenDrop London ordered the most (48) but cancelled 16; Pédalo Logistique received the most (45).
- **Fleet cancellation rate**: the highest rate (Fleet, 1 of 18 lines) rests on one order.
- **Mule price in the catalogue**: the autumn catalogue only shows the new price; the old one is in the June minutes.
- **Head of department**: the logistics team's head of department is the Head of Operations, not the Logistics Manager.
- **Hotel receipt**: city tax is outside the cap and reimbursed; the minibar never is; the trip falls under the new policy; CHF 467 is under €500 at the budget rate, so the line manager approves.
- **Force majeure**: 5 business days from 30 July lands on 6 August (31 Jul, 1, 4, 5, 6 Aug); the notice came on 18 August.
- **Late delivery**: 23 days is 3 full weeks, not 4; the ETA (26 Aug) and the delivery note (27 Aug) give the same result.
- **Clause 9.4**: counts approved battery-related claims only (connectors and cells), as the December minutes specify; Margot Leclerc's claim is pending at zero cost.
- **Defective lot after the closure**: VL-2507-B kept being used after the restart because VL-2508-C, ordered for the restart, was late.
- **Whiteboard rate vs board statement**: the December minutes say Line B reached its *planned* rate; the whiteboard target (150 a month) was not reached in December.
- **False premises**: a Pup recall, a Pup Range Extender, a Spanish dealer.

## What each format tests

| Document | Format | Only readable by |
| --- | --- | --- |
| Catalogue figures 3 and 4 | raster inside a born-digital PDF | vision or OCR on the figure |
| Investor update volumes slide | chart image in PPTX | vision or OCR |
| Field-test notebook | 3 scanned pages, cursive (Homemade Apple, Reenie Beanie), ruled paper, a coffee ring, strike-through | handwriting OCR |
| Delivery note | scanned print, rubber stamp, handwritten remark | OCR |
| Whiteboard | photo, marker, colours, skew, glare | OCR or vision |
| Receipt | photo on a desk, rotated thermal-print look | OCR |
| Customer letter | handwriting in French | OCR + French |
| Org chart | PNG diagram | vision (reporting lines are lines, not text) |
| Orders, claims | CSV, 2,632 and 124 rows | code or table reasoning |
| Dealers, batches, budget | XLSX with several sheets | spreadsheet parsing |
| Email thread | saved HTML, half in German | HTML parsing + German |

## Regenerating

Everything is deterministic: `sh build/build.sh` rewrites `corpus/` and `dataset/` byte-for-byte except PDF and Office metadata timestamps. Changing a fact means changing `world.py`, rebuilding, and running `scripts/verify.py`.
