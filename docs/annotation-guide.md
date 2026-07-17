# Annotation Guide

Protocol version: `2.0.0`

Responsiveness is a relation between propositions advanced by a claim and moves aimed at those propositions by a response. Targeting records where a move is directed. Relation records whether it engages that target. The distinction is load-bearing.

## Compatibility test

**Assume everything the response asserts is true; can the claim layer still be true?**

If yes, the response does not contradict that layer. Write out the two propositions together. If they are jointly possible, annotate a non-covering relation even when the response plainly gestures toward the same subject.

- “No vote was altered” can be true while “the system remains vulnerable” is true. The occurrence denial is compatible with the posture claim.
- “A briefing was delivered” can be true while “the briefing’s content was tailored” is true. The channel does not decide the content.
- “The stronger allegation is false” can be true while the narrower allegation is true. A strawman denial therefore fails automatically.

Every disputed relation annotation must cite this test. Adjudication consists of stating the response proposition, stating the target layer, and explaining whether both can be true together.

## Claim layers

Split the claim into the smallest propositions that can be answered independently.

- `explicit`: directly stated.
- `implicated`: communicatively advanced although not literally stated.

Set `required` to `true` when leaving the layer unanswered would make the response incomplete. Set `backed` to `true` when the exchange itself proffers support for the layer—a citation, dataset, quoted record, calculation, or identified authority. `backed` records whether support was offered, not whether it is persuasive.

Use the narrowest fitting claim kind: `assertion`, `causal`, `conditional`, `normative`, or `comparative`.

## Response moves

Split a response when it performs different acts or aims at different layers.

- `admit`: accepts the target.
- `deny`: rejects the target.
- `qualify`: limits the target.
- `request_evidence`: challenges the support or burden for the target.
- `counterassert`: advances another proposition as an answer.
- `deflect`: changes the subject or substitutes another dispute.
- `ignore`: supplies no answer.

A move may aim at a layer without engaging it. Preserve that fact by keeping the `target_layer_id` and assigning the correct non-covering relation. Do not erase the phenomenon with a null target.

## Relations

- `same`: the move accepts, repeats, or directly requests support for the same proposition.
- `contradicts`: the response proposition and target cannot both be true.
- `entails`: the response proposition entails acceptance of the target.
- `narrows_within_scope`: the move limits the asserted proposition at the same granularity.
- `scope_mismatch`: the move concerns a subpart, adjacent proposition, channel rather than content, instance rather than posture, existence rather than quality, or another granularity.
- `irrelevant`: the move does not bear on the target even though it may be aimed rhetorically at it.
- `unknown`: the annotation does not establish a usable relation.

Apply the compatibility test before assigning `contradicts`. Use `narrows_within_scope` only when the limitation operates inside the proposition actually asserted. Use `scope_mismatch` when the response changes the object or level of generality.

## Coverage rule

A required layer is covered only by one of these act-relation combinations:

| Act | Covering relation | Additional condition |
|---|---|---|
| `admit` | `same` | — |
| `deny` | `contradicts` | — |
| `qualify` | `narrows_within_scope` | — |
| `request_evidence` | `same` | target is not `backed` |
| `counterassert` | `entails`, `contradicts`, or `narrows_within_scope` | — |

A counterassertion with `same` merely restates the target and does not cover it. `scope_mismatch`, `irrelevant`, and `unknown` never cover. The verdict is `fully_responsive` when all required layers are covered, `partially_responsive` when some are covered, and `nonresponsive` when none are covered.

## Invariance families

Each gold family contains one left-coded, one right-coded, and one sterile neutral arm. Preserve:

- layer count, order, kind, explicit/implicated status, required flags, and backing status;
- response acts, target positions, and relations;
- expected verdict.

The validator compares content-free structural signatures before any model is evaluated. The redundant family-label check remains as defense in depth.

## Independent annotation and hard cases

Two annotators type naturalistic exchanges independently and blind to one another’s work. Report Krippendorff’s alpha separately for layer count, act, target, and relation. Resolve disagreements by a written compatibility-test argument.

A genuine disagreement is not forced into gold. Mark it `contested`, omit an expected verdict, retain it in the published hard set, and exclude it from gold scoring. The size and composition of that bin measure the boundary of the decidable portion of the task.

## Protocol identity

The annotation-guide version and kernel version determine the protocol hash. Every score and evaluation carries a manifest containing the protocol hash, dataset hash, model identifier, and prompt hash. Verdicts are therefore protocol-relative: they state what this declared procedure returns on this declared dataset, not an unqualified fact about the exchange.

Every dataset record carries one shared contamination-canary GUID. Dataset validation rejects inconsistent or malformed canaries.
