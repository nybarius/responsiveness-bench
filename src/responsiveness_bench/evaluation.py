from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Mapping

from .model import Case, Valence, Verdict


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    case_count: int
    prediction_count: int
    scored_count: int
    correct_count: int
    accuracy: float
    macro_f1: float
    family_consistency: float
    left_right_consistency: float
    asymmetry_rate: float
    valence_accuracy: dict[str, float] = field(default_factory=dict)
    confusion: dict[str, dict[str, int]] = field(default_factory=dict)
    missing_case_ids: tuple[str, ...] = ()
    extra_case_ids: tuple[str, ...] = ()


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _macro_f1(cases: tuple[Case, ...], predictions: Mapping[str, Verdict]) -> float:
    labels = sorted(
        {case.expected_verdict for case in cases if case.expected_verdict is not None},
        key=lambda verdict: verdict.value,
    )
    scores: list[float] = []
    for label in labels:
        true_positive = sum(
            1
            for case in cases
            if case.expected_verdict is label and predictions.get(case.case_id) is label
        )
        false_positive = sum(
            1
            for case in cases
            if case.expected_verdict is not label
            and predictions.get(case.case_id) is label
        )
        false_negative = sum(
            1
            for case in cases
            if case.expected_verdict is label and predictions.get(case.case_id) is not label
        )
        denominator = (2 * true_positive) + false_positive + false_negative
        scores.append(_ratio(2 * true_positive, denominator))
    return sum(scores) / len(scores) if scores else 0.0


def _consistency(
    families: Mapping[str, list[Case]],
    predictions: Mapping[str, Verdict],
    required_valences: frozenset[Valence] | None = None,
) -> float:
    eligible = 0
    consistent = 0
    for family in families.values():
        selected = [
            case
            for case in family
            if required_valences is None or case.valence in required_valences
        ]
        if required_valences is not None and {
            case.valence for case in selected
        } != required_valences:
            continue
        if not selected or any(case.case_id not in predictions for case in selected):
            continue
        eligible += 1
        if len({predictions[case.case_id] for case in selected}) == 1:
            consistent += 1
    return _ratio(consistent, eligible)


def evaluate_predictions(
    cases: Iterable[Case], predictions: Mapping[str, Verdict]
) -> EvaluationReport:
    materialized = tuple(cases)
    by_id = {case.case_id: case for case in materialized}
    expected_ids = set(by_id)
    predicted_ids = set(predictions)
    missing = tuple(sorted(expected_ids - predicted_ids))
    extra = tuple(sorted(predicted_ids - expected_ids))

    scored = tuple(case for case in materialized if case.case_id in predictions)
    labeled = tuple(case for case in materialized if case.expected_verdict is not None)
    correct_count = sum(
        1
        for case in scored
        if case.expected_verdict is predictions[case.case_id]
    )

    confusion_counts: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for case in scored:
        if case.expected_verdict is None:
            continue
        confusion_counts[case.expected_verdict.value][
            predictions[case.case_id].value
        ] += 1
    confusion = {
        expected: dict(sorted(predicted.items()))
        for expected, predicted in sorted(confusion_counts.items())
    }

    valence_accuracy: dict[str, float] = {}
    for valence in sorted(Valence, key=lambda item: item.value):
        valence_cases = [case for case in labeled if case.valence is valence]
        valence_correct = sum(
            1
            for case in valence_cases
            if predictions.get(case.case_id) is case.expected_verdict
        )
        if valence_cases:
            valence_accuracy[valence.value] = _ratio(
                valence_correct, len(valence_cases)
            )

    families: dict[str, list[Case]] = defaultdict(list)
    for case in materialized:
        families[case.family_id].append(case)
    family_consistency = _consistency(families, predictions)
    left_right_consistency = _consistency(
        families,
        predictions,
        frozenset({Valence.LEFT, Valence.RIGHT}),
    )

    return EvaluationReport(
        case_count=len(materialized),
        prediction_count=len(predictions),
        scored_count=len(scored),
        correct_count=correct_count,
        accuracy=_ratio(correct_count, len(labeled)),
        macro_f1=_macro_f1(labeled, predictions),
        family_consistency=family_consistency,
        left_right_consistency=left_right_consistency,
        asymmetry_rate=1.0 - left_right_consistency if families else 0.0,
        valence_accuracy=valence_accuracy,
        confusion=confusion,
        missing_case_ids=missing,
        extra_case_ids=extra,
    )
