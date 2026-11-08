# Working on Arvenne RAG Bench

This is a public synthetic dataset, not a product implementation.

1. Run `npm test` for structure and hashes; run `python scripts/verify.py` after installing `requirements.txt` for independent numeric checks.
2. Never feed `dataset/questions.jsonl`, `build/` or `docs/DESIGN.md` to a system under evaluation. Only `corpus/` and blind questions are system inputs.
3. Preserve released question IDs and reference answers. Corrections require an explicit version note, changed checksums and evidence from the corpus.
4. Keep partial answers separate; strict accuracy gives them zero points and uses all questions as the denominator.
5. Keep source content multilingual where intentional. Code and documentation are English, without em dashes.
6. No credentials, network calls or product code are needed to run the checks. Never add real customer documents.

`build/` generates the fictional company, `scripts/verify.py` checks corpus files independently, and `test/` checks release integrity. Rendering is deterministic in content, not necessarily in binary metadata. Bundled fonts have their own license files. Regenerate repository artwork from the upstream repository-image template, not by modifying corpus files.
