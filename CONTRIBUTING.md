# Contributing

Maintenance is best-effort by one author. Open an issue in [DuvInc/arvenne-rag-bench](https://github.com/DuvInc/arvenne-rag-bench/issues) before a large change.

Use Node 22+ and run `npm test`. Dataset-specific Python checks are described in the README. No credentials or model inference are needed for the release tests.

For a data correction, identify the question, the released file and the evidence. Do not silently rewrite prior results, reference answers or timing fields. New evaluation settings belong in a separately labeled release. Keep third-party notices and do not add real customer data.

Pull requests need a clear scope, passing local checks and signed-off commits (`git commit -s`). The sign-off records your Developer Certificate of Origin 1.1 agreement: <https://developercertificate.org/>. Do not sign off code you do not have the right to contribute.

For security concerns use [private reporting](https://github.com/DuvInc/arvenne-rag-bench/security/advisories/new), not a public issue. If you fork the repository, update the contact and reporting links in the policy and issue templates.
