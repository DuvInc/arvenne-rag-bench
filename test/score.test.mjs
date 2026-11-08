import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, writeFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const questions = readFileSync(new URL("../dataset/questions.jsonl", import.meta.url), "utf8").trim().split("\n").map(JSON.parse);
const script = fileURLToPath(new URL("../scripts/score.py", import.meta.url));

function runScore(predictions, judgments) {
  const directory = mkdtempSync(join(tmpdir(), "arvenne-score-"));
  try {
    for (const [name, rows] of [["predictions", predictions], ["judgments", judgments]]) {
      writeFileSync(join(directory, `${name}.jsonl`), rows.map(row => JSON.stringify(row)).join("\n"));
    }
    const result = spawnSync(process.env.PYTHON || "python3", [script, "predictions.jsonl", "--judged", "judgments.jsonl"], { cwd: directory, encoding: "utf8" });
    assert.ifError(result.error);
    return result;
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

test("strict scoring gives partial answers zero on the full denominator", () => {
  const result = runScore(questions.map(row => ({ id: row.id, answer: "candidate" })), questions.map((row, index) => ({ id: row.id, verdict: index === 0 ? "correct" : "partial" })));
  assert.equal(result.status, 0, result.stderr);
  const summary = result.stdout.trim().split("\n").map(JSON.parse).find(row => row.level === "all");
  assert.equal(summary.questions, 150);
  assert.equal(summary.fully_correct, 1);
  assert.equal(summary.grading_complete, true);
});

test("incomplete evaluations fail rather than silently reduce the denominator", () => {
  const result = runScore([{ id: questions[0].id, answer: "candidate" }], [{ id: questions[0].id, verdict: "correct" }]);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Incomplete predictions or grades/);
  assert.equal(JSON.parse(result.stdout.trim().split("\n").at(-1)).questions, 150);
});

test("duplicate question IDs are refused", () => {
  const candidate = { id: questions[0].id, answer: "candidate" };
  const result = runScore([candidate, candidate], []);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /Duplicate IDs/);
});
