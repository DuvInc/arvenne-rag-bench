import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";

const questions = readFileSync(new URL("../dataset/questions.jsonl", import.meta.url), "utf8").trim().split("\n").map(JSON.parse);
const blind = readFileSync(new URL("../dataset/questions_blind.jsonl", import.meta.url), "utf8").trim().split("\n").map(JSON.parse);

test("150 unique questions with existing evidence and no leaked blind references", () => {
  assert.equal(questions.length, 150);
  assert.equal(new Set(questions.map(row => row.id)).size, 150);
  assert.deepEqual(blind.map(row => row.id), questions.map(row => row.id));
  for (const question of questions) {
    assert.ok(question.answer);
    for (const source of question.sources) assert.ok(existsSync(new URL(`../corpus/${source}`, import.meta.url)), source);
  }
  for (const row of blind) {
    assert.equal(Object.hasOwn(row, "answer"), false);
    assert.equal(Object.hasOwn(row, "rubric"), false);
  }
});

test("published corpus and annotation checksums match", () => {
  const hashes = JSON.parse(readFileSync(new URL("../checksums.json", import.meta.url)));
  assert.equal(Object.keys(hashes).filter(path => path.startsWith("corpus/")).length, 25);
  for (const [path, hash] of Object.entries(hashes)) assert.equal(createHash("sha256").update(readFileSync(new URL(`../${path}`, import.meta.url))).digest("hex"), hash, path);
});
