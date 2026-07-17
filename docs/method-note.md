# Responsiveness as an Inferred and Verifiable Relation

## Abstract

Responsiveness Bench separates semantic inference from deterministic verification. A system receives raw claim and response prose and emits a typed representation: proposition layers, backing status, response moves, aimed targets, and relations. The kernel then computes coverage from that representation. This division localizes the open judgment instead of hiding it inside a holistic evaluator.

The principal measurement is structural invariance. Left-coded, right-coded, and sterile variants share one gold signature. A model may preserve its verdict while changing the layers, targets, or relations it assigns; structure-flip rate detects that lower-level content effect. Verdict-flip rate, sterile-minus-loaded accuracy, and signed directional asymmetry describe the resulting disposition.

## Aimed and engaged

Target annotation records what a move purports to answer. Relation annotation records whether the move actually engages that proposition under the protocol. Keeping both makes posture-versus-occurrence and channel-versus-content failures representable rather than forcing them into a null target.

The compatibility test supplies the operative standard: assume the response proposition is true and ask whether the target can remain true. Joint possibility defeats `contradicts`. Matched-scope limitations use `narrows_within_scope`; changes in object or granularity use `scope_mismatch`.

## Burdens

A request for evidence covers an unbacked assertion. It does not cover a backed assertion merely by repeating the demand; the response must engage the proffered support. `backed` records the textual fact that support was offered, not a judgment that the support is sufficient.

## Measurement

Inference evaluation reports self-consistency, exact structural match, layer and move multiset F1, verdict accuracy, verdict-flip rate, structure-flip rate, Content Effect, and Directional Asymmetry with an exact family-level sign-flip test.

Every run includes hashes for the protocol, dataset, and prompt. Results are expressly protocol-relative and reproducible.

## Boundary of reduction

Independent annotators type naturalistic cases blind. Field-level agreement is reported separately. Cases that resist adjudication are retained as contested rather than coerced into gold. The contested share is itself evidence about how much of ordinary disagreement can be reduced to a stable responsiveness relation.
