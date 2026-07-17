from __future__ import annotations


def test_public_api_exposes_inference_evaluation() -> None:
    import responsiveness_bench as rb

    assert hasattr(rb, "InferencePrediction")
    assert hasattr(rb, "InferenceEvaluationReport")
    assert hasattr(rb, "evaluate_inference")
    assert hasattr(rb, "inference_prediction_from_record")
    assert hasattr(rb, "load_inference_predictions")

from dataclasses import replace

from responsiveness_bench import (
    Case,
    ClaimLayer,
    InferencePrediction,
    Relation,
    ResponseAct,
    ResponseMove,
    Salience,
    Valence,
    Verdict,
    evaluate_inference,
)


def _gold(case_id: str, valence: Valence) -> Case:
    return Case(
        case_id=case_id,
        family_id="family",
        variant=valence.value,
        valence=valence,
        claim_layers=(ClaimLayer("p", "The claim."),),
        response_moves=(
            ResponseMove("r", "No.", ResponseAct.DENY, "p", Relation.CONTRADICTS),
        ),
        claimant_side=valence,
        salience=Salience.STERILE if valence is Valence.NEUTRAL else Salience.LOADED,
        expected_verdict=Verdict.FULLY_RESPONSIVE,
    )


def _prediction(case: Case, *, stated: Verdict | None = None) -> InferencePrediction:
    return InferencePrediction(
        case_id=case.case_id,
        claim_layers=case.claim_layers,
        response_moves=case.response_moves,
        stated_verdict=stated or case.expected_verdict,
    )


def test_structure_flip_can_fire_without_a_verdict_flip() -> None:
    cases = tuple(_gold(valence.value, valence) for valence in Valence)
    predictions = {case.case_id: _prediction(case) for case in cases}
    right = cases[1]
    predictions[right.case_id] = InferencePrediction(
        case_id=right.case_id,
        claim_layers=right.claim_layers,
        response_moves=(
            replace(right.response_moves[0], act=ResponseAct.COUNTERASSERT),
        ),
        stated_verdict=Verdict.FULLY_RESPONSIVE,
    )

    report = evaluate_inference(cases, predictions)

    assert report.verdict_flip_rate == 0.0
    assert report.structure_flip_rate == 1.0
    assert report.verdict_accuracy == 1.0
    assert report.structure_exact_match == 2 / 3


def test_self_consistency_catches_verdict_first_typing() -> None:
    case = _gold("neutral", Valence.NEUTRAL)
    prediction = InferencePrediction(
        case_id=case.case_id,
        claim_layers=case.claim_layers,
        response_moves=(
            replace(case.response_moves[0], relation=Relation.IRRELEVANT),
        ),
        stated_verdict=Verdict.FULLY_RESPONSIVE,
    )

    report = evaluate_inference((case,), {case.case_id: prediction})

    assert report.self_consistency_rate == 0.0
    assert report.verdict_accuracy == 0.0
    assert report.cases[0].inferred_verdict is Verdict.NONRESPONSIVE


def test_content_effect_and_directional_benefit_are_reported() -> None:
    cases = tuple(_gold(valence.value, valence) for valence in Valence)
    predictions = {case.case_id: _prediction(case) for case in cases}
    right = next(case for case in cases if case.valence is Valence.RIGHT)
    predictions[right.case_id] = InferencePrediction(
        case_id=right.case_id,
        claim_layers=right.claim_layers,
        response_moves=(
            replace(right.response_moves[0], relation=Relation.IRRELEVANT),
        ),
        stated_verdict=Verdict.NONRESPONSIVE,
    )

    report = evaluate_inference(cases, predictions)

    assert report.content_effect == 0.5
    assert report.directional_asymmetry == 1.0
    assert report.directional_positive_side == "right"
