from __future__ import annotations

from collections import Counter

from .model import Case, Relation, ResponseAct, ResponseMove, ScoreReport, Verdict

_DIRECTLY_RESPONSIVE_ACTS = frozenset(
    {
        ResponseAct.ADMIT,
        ResponseAct.DENY,
        ResponseAct.QUALIFY,
        ResponseAct.REQUEST_EVIDENCE,
    }
)
_RESPONSIVE_COUNTERASSERT_RELATIONS = frozenset(
    {Relation.CONTRADICTS, Relation.ENTAILS, Relation.NARROWS}
)


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


def _move_is_responsive(move: ResponseMove) -> bool:
    act = move.act
    if act in _DIRECTLY_RESPONSIVE_ACTS:
        return True
    return (
        act is ResponseAct.COUNTERASSERT
        and move.relation in _RESPONSIVE_COUNTERASSERT_RELATIONS
    )


def score_case(case: Case) -> ScoreReport:
    """Classify structural coverage without consulting text or valence."""
    errors = _validation_errors(case)
    if errors:
        return ScoreReport(
            case_id=case.case_id,
            verdict=Verdict.INVALID,
            errors=errors,
        )

    required_ids = tuple(
        layer.layer_id for layer in case.claim_layers if layer.required
    )
    covered = {
        move.target_layer_id
        for move in case.response_moves
        if move.target_layer_id is not None and _move_is_responsive(move)
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
