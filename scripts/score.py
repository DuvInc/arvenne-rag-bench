"""Strict local scoring: python scripts/score.py predictions.jsonl --judged judged.jsonl"""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(path):
    records = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    if len({row["id"] for row in records}) != len(records):
        raise ValueError(f"Duplicate IDs: {path}")
    return {row["id"]: row for row in records}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions")
    parser.add_argument("--judged")
    args = parser.parse_args()
    references = load(ROOT / "dataset/questions.jsonl")
    predictions = load(args.predictions)
    judged = load(args.judged) if args.judged else {}
    if set(predictions) - set(references) or set(judged) - set(references):
        raise ValueError("Unknown question IDs")
    if any(row.get("verdict") not in {"correct", "partial", "wrong"} for row in judged.values()):
        raise ValueError("Invalid verdict")
    prompt = (ROOT / "dataset/JUDGING.md").read_text().split("```text")[1].split("```")[0].strip()
    jobs = []
    for question_id, question in references.items():
        if question_id in judged or question_id not in predictions:
            continue
        rendered = prompt
        values = {"question": question["question"], "reference": question["answer"], "rubric": "\n".join(question.get("rubric", [])) or "(none)", "answer_type": question["answer_type"], "answer": predictions[question_id]["answer"]}
        for field, value in values.items():
            rendered = rendered.replace("{" + field + "}", str(value))
        jobs.append({"id": question_id, "prompt": rendered})
    if jobs:
        Path("judge_jobs.jsonl").write_text("".join(json.dumps(row) + "\n" for row in jobs))
    complete = len(predictions) == len(references) and len(judged) == len(references)
    for level in [1, 2, 3, 4, "all"]:
        selected = [row for row in references.values() if level == "all" or row["level"] == level]
        correct = sum(row["id"] in predictions and judged.get(row["id"], {}).get("verdict") == "correct" for row in selected)
        print(json.dumps({"level": level, "questions": len(selected), "fully_correct": correct, "strict_accuracy_pct": round(100 * correct / len(selected), 2), "grading_complete": complete}))
    if not complete:
        raise SystemExit("Incomplete predictions or grades; fixed-denominator figures are not a complete evaluation. Missing grading prompts were written where predictions exist.")


if __name__ == "__main__":
    main()
