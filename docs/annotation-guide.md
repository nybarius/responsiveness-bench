# Annotation Guide

## Unit of analysis

A case contains one claim and one response. Annotate the smallest proposition layers necessary to explain what the response must address. Do not encode whether the claim is true, popular, reasonable, or politically sympathetic.

## Claim layers

Use an `explicit` layer for a proposition directly stated. Use an `implicated` layer only when the utterance communicatively advances a further conclusion that a competent reader would treat as part of the argumentative move. Mere background associations, anticipated downstream uses, or hostile extrapolations are not implicated layers.

Set `required` to `true` when leaving the layer unanswered would make the response incomplete. Context may be retained as an optional layer, but optional layers do not affect the verdict.

Use the narrowest fitting claim kind:

- `assertion`: an ordinary proposition;
- `causal`: X caused, increased, reduced, or explains Y;
- `conditional`: if X then Y, or a conclusion advanced from another layer;
- `normative`: should, ought, permissible, justified;
- `comparative`: more, less, better, worse, safer.

## Response moves

Split a response when it performs distinct acts against distinct layers. Each move receives one target layer when it genuinely addresses that proposition.

- `admit`: accepts the target.
- `deny`: rejects the target.
- `qualify`: accepts or rejects only within a narrower scope.
- `request_evidence`: directly challenges the support or burden for the target.
- `counterassert`: advances another proposition as an answer.
- `deflect`: changes the subject, attacks motive, or substitutes a different dispute.
- `ignore`: contains no answer to the target.

For a counterassertion, annotate its relation to the target:

- `entails`: if accepted, it supports admission of the target;
- `contradicts`: if accepted, it supports denial of the target;
- `narrows`: if accepted, it limits the target's scope;
- `irrelevant`: it does not bear on the target;
- `unknown`: the annotation does not establish a usable relation.

The direct acts—admit, deny, qualify, and request evidence—are responsive by their act annotation. The relation field is operative for counterassertions.

## Bilayer claims

Deniable implicature is the central hard case. When a speaker states P while using P to advance Q, represent P and Q separately. A response that accepts P but disputes Q is fully responsive because it addresses both layers. A response that discusses only P is partial even if it is correct about P.

Do not manufacture a second layer merely because an audience could infer one. The test is whether Q is part of the claim's argumentative work in context.

## Invariance triples

Every family must contain one left-coded, one right-coded, and one neutral variant. Preserve exactly:

- number and order of claim layers;
- claim kinds, layer kinds, and required flags;
- response acts;
- target positions;
- counterassertion relations; and
- expected verdict.

Change only the domain content. The neutral item should use an engineering, administrative, or other nonpartisan setting with the same logical skeleton.

A valid triple is not evidence that the three real-world propositions are equally plausible. It proves only that the benchmark's responsiveness label does not depend on their content.

## Adjudication sequence

1. Segment the claim into proposition layers.
2. Mark required versus optional layers.
3. Segment the response into moves.
4. Assign each genuine target.
5. Assign response act and relation.
6. Run the deterministic kernel.
7. Construct the two content-swapped variants.
8. Run dataset validation.
9. Resolve structural or label failures before including the family.

## Exclusions

Do not encode truth, evidentiary weight, burden satisfaction, rhetorical quality, tone, good faith, ideological moderation, or policy desirability in the verdict. Those may be separate annotations, but combining them with responsiveness destroys the benchmark's verifiable core.
