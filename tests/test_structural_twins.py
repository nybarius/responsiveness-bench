from __future__ import annotations

from dataclasses import replace

from responsiveness_bench import (
    Case,
    ClaimLayer,
    InferencePrediction,
    Relation,
    ResponseAct,
    ResponseMove,
    Valence,
    Verdict,
    evaluate_inference,
    structural_signature,
)


def _twin_case(case_id: str, valence: Valence) -> Case:
    return Case(
        case_id=case_id,
        family_id="twin-order",
        variant=valence.value,
        valence=valence,
        claim_layers=(
            ClaimLayer("authorization", "The program was unauthorized."),
            ClaimLayer("budget", "The program was over budget."),
        ),
        response_moves=(
            ResponseMove(
                "r1",
                "The budget was fully appropriated.",
                ResponseAct.DENY,
                "budget",
                Relation.CONTRADICTS,
            ),
        ),
        expected_verdict=Verdict.PARTIALLY_RESPONSIVE,
    )


def test_twin_layer_emission_order_does_not_change_structure_metrics() -> None:
    cases = tuple(_twin_case(valence.value, valence) for valence in Valence)
    predictions = {
        case.case_id: InferencePrediction(
            case_id=case.case_id,
            claim_layers=case.claim_layers,
            response_moves=case.response_moves,
            stated_verdict=case.expected_verdict,
        )
        for case in cases
    }
    reordered = cases[0]
    predictions[reordered.case_id] = replace(
        predictions[reordered.case_id],
        claim_layers=tuple(reversed(reordered.claim_layers)),
    )

    report = evaluate_inference(cases, predictions)

    reordered_result = next(
        result for result in report.cases if result.case_id == reordered.case_id
    )
    assert reordered_result.structure_exact is True
    assert reordered_result.layer_f1 == 1.0
    assert reordered_result.move_f1 == 1.0
    assert report.structure_flip_rate == 0.0


def test_signature_distinguishes_same_twin_from_split_twin_attachments() -> None:
    same_twin = replace(
        _twin_case("same-twin", Valence.NEUTRAL),
        response_moves=(
            ResponseMove(
                "r1",
                "No.",
                ResponseAct.DENY,
                "authorization",
                Relation.CONTRADICTS,
            ),
            ResponseMove(
                "r2",
                "Still no.",
                ResponseAct.DENY,
                "authorization",
                Relation.CONTRADICTS,
            ),
        ),
    )
    split_twins = replace(
        same_twin,
        case_id="split-twins",
        response_moves=(
            same_twin.response_moves[0],
            replace(same_twin.response_moves[1], target_layer_id="budget"),
        ),
        expected_verdict=Verdict.FULLY_RESPONSIVE,
    )

    assert structural_signature(same_twin) != structural_signature(split_twins)
