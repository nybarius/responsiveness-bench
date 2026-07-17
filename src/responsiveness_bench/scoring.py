from __future__ import annotations

from collections import Counter

from .model import Case, ClaimLayer, Relation, ResponseAct, ResponseMove, ScoreReport, Verdict

_COVERING_RELATIONS_BY_ACT = {
    ResponseAct.ADMIT: frozenset({Relation.SAME}),
    ResponseAct.DENY: frozenset({Relation.CONTRADICTS}),
    ResponseAct.QUALIFY: frozenset({Relation.NARROWS_WITHIN_SCOPE}),
    ResponseAct.REQUEST_EVIDENCE: frozenset({Relation.SAME}),
    ResponseAct.COUNTERASSERT: frozenset(
        {
            Relation.CONTRADICTS,
            Relation.ENTAILS,
            Relation.NARROWS_WITHIN_SCOPE,
        }
    ),
}


def _validation_errors(case: Case) -> tuple[str, ...]:
    errors: list[str] = []
    layer_ids = [layer.layer_id for layer in case.claim_layers]
    for layer_id, count in Counter(layer_ids).items():
        if count > 1:
            errors.append(f"duplicate claim layer id '{layer_id}'")

    known_layer_ids = set(layer_ids)
    for move in case.response_moves:
        if move.target_layer_id is not None and move.target_layer_id not in known_layer_ids:
            errors.append(
                f"response move '{move.move_id}' targets unknown layer "
                f"'{move.target_layer_id}'"
            )

    if not any(layer.required for layer in case.claim_layers):
        errors.append("case has no required claim layers")
    return tuple(errors)


def _move_covers_layer(move: ResponseMove, layer: ClaimLayer) -> bool:
    """Return whether an aimed move engages its target under this protocol.

    A counterassertion with ``same`` merely restates the target and is therefore
    uncovered; indirect engagement must entail, contradict, or narrow it.
    """
    if move.relation not in _COVERING_RELATIONS_BY_ACT.get(move.act, frozenset()):
        return False
    if move.act is ResponseAct.REQUEST_EVIDENCE and layer.backed:
        return False
    return True


def score_case(case: Case) -> ScoreReport:
    """Classify structural coverage without consulting text or valence."""
    errors = _validation_errors(case)
    if errors:
        return ScoreReport(
            case_id=case.case_id,
            verdict=Verdict.INVALID,
            errors=errors,
        )

    layers_by_id = {layer.layer_id: layer for layer in case.claim_layers}
    required_ids = tuple(
        layer.layer_id for layer in case.claim_layers if layer.required
    )
    covered = {
        move.target_layer_id
        for move in case.response_moves
        if move.target_layer_id is not None
        and _move_covers_layer(move, layers_by_id[move.target_layer_id])
    }
    covered_ids = tuple(layer_id for layer_id in required_ids if layer_id in covered)
    uncovered_ids = tuple(
        layer_id for layer_id in required_ids if layer_id not in covered
    )

    if not covered_ids:
        verdict = Verdict.NONRESPONSIVE
    elif not uncovered_ids:
        verdict = Verdict.FULLY_RESPONSIVE
    else:
        verdict = Verdict.PARTIALLY_RESPONSIVE

    return ScoreReport(
        case_id=case.case_id,
        verdict=verdict,
        covered_layer_ids=covered_ids,
        uncovered_layer_ids=uncovered_ids,
    )
