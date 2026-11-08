# Scoring

Each answer gets one verdict: **correct**, **partial** or **wrong**. Strict accuracy gives one point only to a fully correct answer; partial and wrong answers receive zero. Report per-level and overall strict accuracy, the fixed denominator, grading coverage and the judge model.

## Automatic part

Numeric diagnostics can check whether a number falls within `tolerance` of `value` (in the expected unit). These checks alone can accept a wrong answer that happens to contain the expected number. The headline score therefore uses complete answer judgments, including for numeric questions.

## Judged part

Every other question (`short`, `date`, `list`, `free`, `contradiction`, `unanswerable`) goes to a judge model with the prompt below. The judge sees the question, the reference answer, the rubric and the candidate answer, never the name of the system. We recommend two judges from different model families and reporting both figures; when they disagree, a human decides and the disagreement count is published.

Rules the judge applies:

- **Facts, not wording.** A different phrasing of the same facts is correct. Extra facts are fine if they are true; a false extra fact that changes the meaning makes the answer wrong.
- **Rubric points** are the facts an answer must contain. All points: correct. The main point but not all: partial. The main point missing or wrong: wrong.
- **contradiction**: correct only if the answer reports both conflicting values and says the sources disagree. Picking one value silently is wrong, even if it is one of the two.
- **unanswerable** (includes false premises): correct only if the answer says the information is not in the documents, or rejects the premise. An invented answer is wrong. Saying "not found" on any other question is wrong.
- **Numbers inside judged answers** follow the question's tolerance when there is one; otherwise a rounding at the precision of the reference is fine.

```text
You are grading an answer produced by a question-answering system over a company's documents.

Question:
{question}

Reference answer:
{reference}

Facts the answer must contain (rubric):
{rubric}

Question type: {answer_type}
- "contradiction": the answer must report both conflicting values and say the sources disagree.
- "unanswerable": the answer must say the information is not in the documents or reject the false premise.

Candidate answer:
{answer}

Judge facts, not wording. Extra true details are fine. A false detail that changes the meaning makes the answer wrong.
Return JSON only: {"reasoning": "<one or two sentences>", "verdict": "correct" | "partial" | "wrong"}
```
