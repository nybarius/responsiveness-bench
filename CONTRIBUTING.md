# Contributing

Responsiveness Bench is designed for adversarial extension. The strongest contribution is a case that exposes a weakness in the type system, annotation protocol, verifier, or metrics.

## Structural families

Every gold family must contain one left-coded, one right-coded, and one sterile neutral arm. Preserve layer count and order, layer kinds, required and backed flags, response acts, target positions, relations, and expected verdict.

Before assigning `contradicts`, write the compatibility test: assume the response proposition is true and ask whether the target layer can remain true. If it can, use `scope_mismatch`, `irrelevant`, or another non-covering relation.

## Naturalistic cases

Prefer verbatim public exchanges and found political mirrors. Record source and date, retain public names, and mark whether a mirror was found or synthesized. Synthesized text must pass a believability screen.

Two annotators should type cases independently. Run:

```bash
responsiveness-bench agreement annotator-a.jsonl annotator-b.jsonl
```

Adjudicate disagreements with a written compatibility argument. Unresolved cases belong in the contested set with no gold verdict.

## Required gate

```bash
pytest
python -m compileall -q src tests
responsiveness-bench validate data/seed
responsiveness-bench audit data/seed --check
```

Behavior changes require tests. Corpus-only changes must preserve family invariance and the contamination canary.
