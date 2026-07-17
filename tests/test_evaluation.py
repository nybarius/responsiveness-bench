from __future__ import annotations

from responsiveness_bench import (
    Case,
    ClaimLayer,
    ResponseAct,
    ResponseMove,
    Valence,
    Verdict,
    evaluate_predictions,
)


def case(
    case_id: str,
    family_id: str,
    valence: Valence,
    expected: Verdict,
) -> Case:
    return Case(
        case_id=case_id,
        family_id=family_id,
        variant=valence.value,
        valence=valence,
        claim_layers=(ClaimLayer("p", "Claim."),),
        response_moves=(ResponseMove("r", "Response.", ResponseAct.DENY, "p"),),
        expected_verdict=expected,
    )


def corpus() -> tuple[Case, ...]:
    return (
        case("f1-left", "f1", Valence.LEFT, Verdict.FULLY_RESPONSIVE),
        case("f1-right", "f1", Valence.RIGHT, Verdict.FULLY_RESPONSIVE),
        case("f1-neutral", "f1", Valence.NEUTRAL, Verdict.FULLY_RESPONSIVE),
        case("f2-left", "f2", Valence.LEFT, Verdict.NONRESPONSIVE),
        case("f2-right", "f2", Valence.RIGHT, Verdict.NONRESPONSIVE),
        case("f2-neutral", "f2", Valence.NEUTRAL, Verdict.NONRESPONSIVE),
    )


def test_perfect_predictions_receive_perfect_scores() -> None:
    cases = corpus()
    predictions = {case.case_id: case.expected_verdict for case in cases}

    report = evaluate_predictions(cases, predictions)

    assert report.case_count == 6
    assert report.prediction_count == 6
    assert report.scored_count == 6
    assert report.correct_count == 6
    assert report.accuracy == 1.0
    assert report.macro_f1 == 1.0
    assert report.family_consistency == 1.0
    assert report.left_right_consistency == 1.0
    assert report.asymmetry_rate == 0.0
    assert report.valence_accuracy == {"left": 1.0, "neutral": 1.0, "right": 1.0}
    assert report.missing_case_ids == ()
    assert report.extra_case_ids == ()


def test_partisan_flip_error_is_visible_as_asymmetry() -> None:
    cases = corpus()
    predictions = {case.case_id: case.expected_verdict for case in cases}
    predictions["f1-right"] = Verdict.NONRESPONSIVE

    report = evaluate_predictions(cases, predictions)

    assert report.accuracy == 5 / 6
    assert report.family_consistency == 0.5
    assert report.left_right_consistency == 0.5
    assert report.asymmetry_rate == 0.5
    assert report.valence_accuracy == {"left": 1.0, "neutral": 1.0, "right": 0.5}
    assert report.confusion["fully_responsive"] == {
        "fully_responsive": 2,
        "nonresponsive": 1,
    }


def test_missing_and_extra_predictions_are_reported_not_silently_dropped() -> None:
    cases = corpus()
    predictions = {
        "f1-left": Verdict.FULLY_RESPONSIVE,
        "unknown": Verdict.NONRESPONSIVE,
    }

    report = evaluate_predictions(cases, predictions)

    assert report.scored_count == 1
    assert report.missing_case_ids == (
        "f1-neutral",
        "f1-right",
        "f2-left",
        "f2-neutral",
        "f2-right",
    )
    assert report.extra_case_ids == ("unknown",)


def test_macro_f1_averages_gold_labels_present_in_corpus() -> None:
    cases = corpus()
    predictions = {
        case.case_id: Verdict.FULLY_RESPONSIVE
        for case in cases
    }

    report = evaluate_predictions(cases, predictions)

    assert report.macro_f1 == 1 / 3
