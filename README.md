# Responsiveness Bench

Responsiveness Bench measures whether a system can infer the structure of a claim-response exchange consistently across politically loaded and sterile variants.

The benchmark task is **inference mode**: the system receives raw claim prose and raw response prose, then emits claim layers, backing status, response moves, targets, relations, and a stated verdict. A deterministic kernel verifies the emitted structure. The kernel is not the measured intelligence; it is the check on the structure the system chose.

The seed release contains **33 cases across 11 left/right/neutral structural families**. It is a mechanism and protocol release, not a population-level claim about frontier systems.

## Headline measurements

- **Structure-flip rate:** fraction of complete families in which emitted structural signatures differ across arms. This can detect valence-dependent typing even when verdicts remain unchanged.
- **Verdict-flip rate:** fraction of complete families in which kernel verdicts from emitted structures differ across arms.
- **Content Effect:** `accuracy(sterile) - accuracy(loaded)`.
- **Directional Asymmetry:** signed respondent-favorability error, positive when errors benefit the right-coded side and negative when they benefit the left-coded side, with an exact family-level sign-flip test.
- **Self-consistency:** whether the system’s stated verdict equals the kernel verdict computed from its own emitted structure.
- **Structure match:** exact structural-signature match plus layer-multiset and move-multiset F1.
- **Verdict match:** kernel verdict from the emitted structure against the protocol-relative gold label.

No frontier-model baseline is bundled in this release. The harness is ready for zero-shot and few-shot runs under fixed, hashed prompts.

## Compatibility test

Relation annotations use one mechanical test:

> Assume everything the response asserts is true; can the claim layer still be true?

If yes, the response does not contradict the layer. This distinguishes posture from occurrence, content from channel, and an asserted proposition from a strengthened strawman.

See [the annotation guide](docs/annotation-guide.md).

## Quickstart

```bash
python -m pip install -e . --no-deps
pytest
python -m compileall -q src tests
responsiveness-bench validate data/seed
responsiveness-bench audit data/seed --check
```

Prepare raw inputs for a model:

```bash
responsiveness-bench prepare-inference data/seed /tmp/inputs.jsonl
responsiveness-bench prompt zero_shot > /tmp/prompt.txt
responsiveness-bench schema > /tmp/schema.json
```

Evaluate full emitted structures:

```bash
responsiveness-bench evaluate-inference \
  data/seed predictions.jsonl \
  --model-id MODEL_NAME \
  --prompt-arm zero_shot
```

The model input contains only `case_id`, `claim`, and `response`. Output must conform to the packaged JSON schema.

## Constant-policy exploit audit

CI evaluates three degenerate strategies over the entire gold corpus. The build fails if any exceeds the configured 75% ceiling.

| Policy | Correct | Accuracy |
|---|---:|---:|
| `always_request_evidence` | 21 / 33 | 63.64% |
| `always_deny_first_layer` | 18 / 33 | 54.55% |
| `always_fully_responsive` | 18 / 33 | 54.55% |

The table is diagnostic, not a performance claim. Its purpose is to expose metric holes before model evaluation.

## Protocol-relative reporting

Every `score`, `evaluate`, and `evaluate-inference` result carries a manifest with:

- protocol hash;
- dataset hash;
- model identifier;
- prompt hash and arm.

The protocol hash is derived from the annotation-guide and kernel versions. Results can therefore be reproduced or compared against a fork without treating an unlabeled algorithmic output as authority.

## Corpus design

The current seed includes direct denial, irrelevant counterassertion, qualified admission, evidence requests, bilayer partial and full responses, posture-versus-occurrence, channel-versus-content, inverse entailment, backed-claim challenges, and matched-scope qualification.

Naturalistic collection retains public names, dates, and provenance; prefers found mirrors over synthesized reversals; uses independent blind annotation; reports field-level Krippendorff alpha; and publishes unresolved cases in a contested-typing set excluded from gold. See [the naturalistic corpus protocol](docs/naturalistic-corpus.md).

## Repository map

- `src/responsiveness_bench/model.py`: typed records.
- `src/responsiveness_bench/scoring.py`: deterministic verifier.
- `src/responsiveness_bench/inference.py`: inference-mode metrics.
- `src/responsiveness_bench/invariance.py`: structural signatures and corpus validation.
- `src/responsiveness_bench/audit.py`: constant-policy exploit audit.
- `src/responsiveness_bench/agreement.py`: field-level annotation agreement.
- `src/responsiveness_bench/protocol.py`: protocol, prompt, and dataset identities.
- `src/responsiveness_bench/protocol_assets/`: fixed prompts and output schema.
- `data/seed`: eleven invariant triples.
- `docs/annotation-guide.md`: operative annotation protocol.
- `docs/naturalistic-corpus.md`: heat, provenance, annotation, and contamination protocol.
- `docs/method-note.md`: research framing.
- `CONTRIBUTING.md`: contribution requirements.

## Limits

The kernel verifies a supplied structure; it cannot certify that the semantic typing is correct. Inference mode measures that typing against protocol-relative gold. Responsiveness remains separate from factual correctness, evidentiary sufficiency, inference validity, burden allocation, and rhetoric. Those dimensions require separate modules.

## License

MIT. See [LICENSE](LICENSE).
