# Naturalistic Corpus Protocol

## Heat

The naturalistic corpus is designed to place the annotation judgment under political load.

1. Harvest public statements verbatim, editing only enough to make the exchange self-contained.
2. Retain public names and politically salient objects.
3. Record source, date, URL when available, and whether the text is verbatim.
4. Prefer found mirrors: real exchanges in which the opposing side made the same structural move.
5. When synthesis is unavoidable, require a believability screen: a partisan of the coded side must plausibly utter the text.
6. Pair each loaded arm with a sterile control preserving the same gold structure.

Found mirrors reduce the risk that asymmetry is manufactured by an implausible reversal. Synthetic mirrors remain admissible only when provenance marks them as such and the believability screen is documented.

## Annotation

Two annotators independently identify layers, backing, moves, targets, and relations. They apply the compatibility test before assigning `contradicts` and produce written arguments for disagreements. Agreement is reported separately for layer count, act, target, and relation.

Unresolved disagreements enter the contested-typing set. They remain public, but are excluded from gold metrics.

## Contamination control

Every corpus file carries a fixed GUID canary before model evaluation begins. The canary is not used as a prompt feature. Its purpose is to permit later contamination checks against model outputs, memorized fragments, or leaked evaluation material.
