# Responsiveness Bench v0.2.0

Version 0.2.0 moves the measured task from verdict prediction over pretyped input to full-structure inference from raw claim-response prose.

## Added

- Relation-gated coverage for every response act.
- Separate `narrows_within_scope` and `scope_mismatch` relations.
- Backing-aware evidence requests.
- Five new invariant structural families, for 33 cases across 11 families.
- Full-structure inference evaluation with self-consistency, structure match, verdict match, structure and verdict flips, Content Effect, and Directional Asymmetry.
- Fixed zero-shot and few-shot prompts with a constrained output schema.
- Protocol, dataset, and prompt hashes in run manifests.
- Constant-policy exploit audit enforced in CI.
- Field-level Krippendorff agreement and contested-typing support.
- Provenance, salience, claimant-side, and contamination-canary fields.
