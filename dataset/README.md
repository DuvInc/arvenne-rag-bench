# Arvenne RAG Bench

150 questions over the shared drive of a fictional company, built to measure what retrieval-augmented systems actually do on real office documents: scanned handwriting, figures, spreadsheets, policies that supersede each other, sources that disagree, and questions with no answer.

The company is **Arvenne Cycles SAS**, a cargo e-bike maker in Lyon, in 2025. Every document and every answer was written on purpose from one model of the company, so each reference answer is known exactly and every number is reproducible.

## The corpus

25 documents in 11 formats, in `corpus/`, in English with one German email thread and two French documents.

| Folder | Documents |
| --- | --- |
| `sales/` | 2,632 order lines (CSV), dealer list with targets and tier terms (XLSX), data dictionary (MD) |
| `products/` | autumn catalogue (PDF, key facts in a diagram and a chart), Barge 2 press release (MD) |
| `operations/` | production batches (XLSX), warranty claims (CSV), incident report (DOCX), handwritten field-test notebook (scanned PDF), meeting whiteboard (photo) |
| `suppliers/` | supply agreement (PDF), email thread partly in German (saved HTML), delivery note (scanned PDF with stamp and handwriting) |
| `finance/` | 2025 budget (XLSX), Q3 investor update (PPTX, figures in a chart image), hotel receipt (photo) |
| `hr/` | employee handbook (MD), travel policy update (DOCX), org chart (PNG), works-council minutes in French (DOCX) |
| `meetings/` | board minutes of June (MD), September (DOCX) and December (TXT) |
| `support/` | support FAQ (JSON), handwritten customer letter in French (photo) |

Index the whole folder. Every question may draw on any document.

## The questions

`questions.jsonl`, one question per line. `questions_blind.jsonl` has the same ids and questions without answers, for runs that must not see them.

| Level | Questions | What it takes | Several documents | Image or scan | Tables | Long answer |
| --- | --- | --- | --- | --- | --- | --- |
| **L1 find** | 40 | One fact, stated once | 12* | 6 | 4 | 0 |
| **L2 read** | 40 | One document, with counting, filtering, reading a figure or another language | 4 | 11 | 17 | 3 |
| **L3 combine** | 40 | Several documents, aggregation over full tables, dates and superseded rules, contradictions | 35 | 7 | 25 | 13 |
| **L4 expert** | 30 | Chains of 3 to 5 steps with traps, contract and policy application, false premises | 26 | 9 | 19 | 18 |

\* At L1 the fact is repeated in several documents; any one of them is enough.

Fields:

| Field | Meaning |
| --- | --- |
| `id`, `level` | `ARB-001`…`ARB-150`, 1 to 4 |
| `question` | The question, as a user would ask it |
| `answer` | The reference answer, in full sentences when the question needs it |
| `answer_type` | `number`, `short`, `date`, `list`, `free`, `contradiction`, `unanswerable` |
| `value`, `unit`, `tolerance` | For numeric answers: the value, its unit, and the absolute tolerance accepted |
| `rubric` | For long answers: the facts a correct answer must contain |
| `sources` | The documents that hold the evidence |
| `skills` | What the question exercises: `ocr-handwriting`, `vision-diagram`, `join`, `aggregation`, `temporal`, `supersession`, `contradiction`, `unanswerable`, `false-premise`, `cross-lingual`, `policy-application`, `trap`… |

Most answers are not a single word. 23 need a few sentences judged against a rubric, 3 require reporting a contradiction instead of picking a side, and 8 have no answer in the documents or rest on a false premise.

## Scoring

Grade full answers against the reference and rubric, including numeric questions. Strict accuracy gives zero credit to partial answers and retains every question in the denominator. Protocol and prompt: [JUDGING.md](JUDGING.md). Script: `scripts/score.py` (no model call; it writes missing judge prompts for you and validates supplied verdicts).

Report: accuracy per level and overall, the judge models, and whether the system saw the images (OCR or vision) or text only.

## What makes it hard

- **Aggregation over whole tables.** "What share of 2025 net revenue came through the webshop?" needs every delivered line, discounts, two currencies converted at the budget's rates, and the exclusion rules of the data dictionary. Top-k chunks cannot answer it.
- **Superseded rules.** The per diem depends on whether the trip started before or after the travel policy update; remote work changes in 2026 through French works-council minutes.
- **Real and apparent contradictions.** Some sources disagree and the right answer says so. Others only look contradictory (a launch event and an availability date) and the right answer reconciles them.
- **Facts only in pixels.** Cell counts in a wiring diagram, ranges on a chart, a crossed-out load in a notebook, initials on a whiteboard, a room number on a crumpled receipt.
- **Order of events.** "The second brake fade" is not the day that mentions a "2nd descent".
- **Restraint.** Questions about a recall that never happened or a dealer country with no dealers.

## Licence and provenance

Fictional company, people, places and figures: any resemblance is coincidental. Generated by `build/` (seeded, deterministic). Handwriting fonts from Google Fonts under the SIL Open Font License or Apache 2.0 (`build/fonts/README.md`).
