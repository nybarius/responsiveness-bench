# Contributing

Responsiveness Bench is designed for adversarial extension. The best contribution is a case that exposes a real weakness in the type system, annotation protocol, validator, or metrics.

## Contribution types

- New left/right/neutral case families.
- Naturalistic exchanges suitable for annotation studies.
- Corrections to claim layers, response targets, or logical relations.
- Model adapters that emit benchmark prediction JSONL.
- Metrics that preserve the separation between responsiveness and truth.
- Reproducible evidence that an existing type or rule is underspecified.

## Case-family requirements

Every proposed family must include exactly one `left`, one `right`, and one `neutral` variant. All three variants must preserve:

- claim-layer count and order;
- claim kinds, layer kinds, and required flags;
- response acts;
- target positions;
- counterassertion relations; and
- expected verdict.

The variants need not be equally plausible or morally equivalent. They must instantiate the same annotated claim-response structure.

Do not encode truth, evidentiary weight, tone, good faith, political moderation, or policy desirability in `expected_verdict`.

## Submission checklist

1. Add the three JSONL records to an appropriate corpus file.
2. Explain the source or construction of the family in the pull request.
3. State the proposition layers in ordinary language.
4. Identify the hardest annotation judgment.
5. Run:

```bash
PYTHONPATH=src python -m responsiveness_bench.cli validate data/seed.jsonl
pytest
python -m compileall -q src tests
```

6. Add tests for any behavior change. Documentation and corpus-only changes should not alter existing tests unless the specification itself changes.

## Adversarial standard

A proposed extension should survive the strongest content-preserving reversal you can construct. Before submitting a new type or exception, ask whether the same rule would be accepted if the political valence were reversed and the names removed.

## Scope discipline

Responsiveness is only one dimension of reasoning quality. Proposals concerning factual correctness, source reliability, burden allocation, inference validity, or rhetoric should be modeled as separate modules unless they change whether a response addresses a target proposition.
