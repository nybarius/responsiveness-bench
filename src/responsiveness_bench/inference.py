from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from itertools import product
from pathlib import Path
from typing import Any, Iterable, Mapping

from .codec import CorpusFormatError, case_from_record
from .invariance import structural_signature
from .model import (
    AdjudicationStatus,
    Case,
    ClaimLayer,
    ResponseMove,
    Salience,
    Valence,
    Verdict,
)
from .protocol import RunManifest
from .scoring import score_case


@dataclass(frozen=True, slots=True)
class InferencePrediction:
    case_id: str
    claim_layers: tuple[ClaimLayer, ...]
    response_moves: tuple[ResponseMove, ...]
    stated_verdict: Verdict


@dataclass(frozen=True, slots=True)
class InferenceCaseResult:
    case_id: str
    self_consistent: bool
    structure_exact: bool
    layer_f1: float
    move_f1: float
    inferred_verdict: Verdict
    stated_verdict: Verdict
    gold_verdict: Verdict | None


@dataclass(frozen=True, slots=True)
class InferenceEvaluationReport:
    case_count: int
    prediction_count: int
    scored_count: int
    self_consistency_rate: float
    structure_exact_match: float
    layer_f1: float
    move_f1: float
    verdict_accuracy: float
    verdict_flip_rate: float
    structure_flip_rate: float
    content_effect: float
    directional_asymmetry: float
    directional_p_value: float
    directional_positive_side: str = "right"
    missing_case_ids: tuple[str, ...] = ()
    extra_case_ids: tuple[str, ...] = ()
    manifest: RunManifest | None = None
    cases: tuple[InferenceCaseResult, ...] = field(default_factory=tuple)


def _ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def inference_prediction_from_record(record: Mapping[str, Any]) -> InferencePrediction:
    try:
        case_id = record["case_id"]
        if not isinstance(case_id, str) or not case_id:
            raise CorpusFormatError("'case_id' must be a non-empty string")
        parsed = case_from_record(
            {
                "case_id": case_id,
                "family_id": "inference",
                "variant": "neutral",
                "valence": "neutral",
                "claim_layers": record["claim_layers"],
                "response_moves": record["response_moves"],
            }
        )
        return InferencePrediction(
            case_id=case_id,
            claim_layers=parsed.claim_layers,
            response_moves=parsed.response_moves,
            stated_verdict=Verdict(record["stated_verdict"]),
        )
    except CorpusFormatError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise CorpusFormatError(str(exc)) from exc


def load_inference_predictions(path: str | Path) -> dict[str, InferencePrediction]:
    source = Path(path)
    predictions: dict[str, InferencePrediction] = {}
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise CorpusFormatError("record must be a JSON object")
            prediction = inference_prediction_from_record(record)
            if prediction.case_id in predictions:
                raise CorpusFormatError(
                    f"duplicate inference prediction for '{prediction.case_id}'"
                )
            predictions[prediction.case_id] = prediction
        except (json.JSONDecodeError, CorpusFormatError) as exc:
            raise CorpusFormatError(f"{source.name}:{line_number}: {exc}") from exc
    return predictions


def _emitted_case(gold: Case, prediction: InferencePrediction) -> Case:
    return Case(
        case_id=gold.case_id,
        family_id=gold.family_id,
        variant=gold.variant,
        valence=gold.valence,
        claim_layers=prediction.claim_layers,
        response_moves=prediction.response_moves,
        claim_text=gold.claim_text,
        response_text=gold.response_text,
        claimant_side=gold.claimant_side,
        salience=gold.salience,
        provenance=gold.provenance,
        adjudication_status=gold.adjudication_status,
        contamination_canary=gold.contamination_canary,
    )


def _multiset_f1(gold: tuple[Any, ...], predicted: tuple[Any, ...]) -> float:
    gold_counts = Counter(gold)
    predicted_counts = Counter(predicted)
    overlap = sum((gold_counts & predicted_counts).values())
    precision = _ratio(overlap, sum(predicted_counts.values()))
    recall = _ratio(overlap, sum(gold_counts.values()))
    return _ratio(2 * precision * recall, precision + recall)


def _exact_sign_flip_p_value(values: tuple[float, ...]) -> float:
    nonzero = tuple(value for value in values if value)
    if not nonzero:
        return 1.0
    observed = abs(sum(nonzero))
    extreme = 0
    total = 0
    for signs in product((-1, 1), repeat=len(nonzero)):
        total += 1
        statistic = abs(sum(sign * value for sign, value in zip(signs, nonzero)))
        if statistic >= observed - 1e-12:
            extreme += 1
    return extreme / total


def _respondent_rank(verdict: Verdict) -> int | None:
    return {
        Verdict.NONRESPONSIVE: 0,
        Verdict.PARTIALLY_RESPONSIVE: 1,
        Verdict.FULLY_RESPONSIVE: 2,
    }.get(verdict)


def evaluate_inference(
    cases: Iterable[Case],
    predictions: Mapping[str, InferencePrediction],
    *,
    manifest: RunManifest | None = None,
) -> InferenceEvaluationReport:
    gold_cases = tuple(
        case
        for case in cases
        if case.adjudication_status is AdjudicationStatus.GOLD
        and case.expected_verdict is not None
    )
    by_id = {case.case_id: case for case in gold_cases}
    expected_ids = set(by_id)
    predicted_ids = set(predictions)
    missing = tuple(sorted(expected_ids - predicted_ids))
    extra = tuple(sorted(predicted_ids - expected_ids))

    results: list[InferenceCaseResult] = []
    signatures: dict[str, tuple[Any, ...]] = {}
    inferred_verdicts: dict[str, Verdict] = {}
    for case in gold_cases:
        prediction = predictions.get(case.case_id)
        if prediction is None:
            continue
        emitted = _emitted_case(case, prediction)
        emitted_signature = structural_signature(emitted)
        gold_signature = structural_signature(case)
        inferred = score_case(emitted).verdict
        signatures[case.case_id] = emitted_signature
        inferred_verdicts[case.case_id] = inferred
        results.append(
            InferenceCaseResult(
                case_id=case.case_id,
                self_consistent=prediction.stated_verdict is inferred,
                structure_exact=emitted_signature == gold_signature,
                layer_f1=_multiset_f1(gold_signature[0], emitted_signature[0]),
                move_f1=_multiset_f1(gold_signature[1], emitted_signature[1]),
                inferred_verdict=inferred,
                stated_verdict=prediction.stated_verdict,
                gold_verdict=case.expected_verdict,
            )
        )

    families: dict[str, list[Case]] = defaultdict(list)
    for case in gold_cases:
        families[case.family_id].append(case)
    eligible_families = [
        family
        for family in families.values()
        if {case.valence for case in family} == set(Valence)
        and all(case.case_id in inferred_verdicts for case in family)
    ]
    verdict_flips = sum(
        len({inferred_verdicts[case.case_id] for case in family}) > 1
        for family in eligible_families
    )
    structure_flips = sum(
        len({signatures[case.case_id] for case in family}) > 1
        for family in eligible_families
    )

    accuracy_by_salience: dict[Salience, float] = {}
    for salience in Salience:
        selected = [
            case
            for case in gold_cases
            if case.salience is salience and case.case_id in inferred_verdicts
        ]
        accuracy_by_salience[salience] = _ratio(
            sum(
                inferred_verdicts[case.case_id] is case.expected_verdict
                for case in selected
            ),
            len(selected),
        )

    family_direction: dict[str, float] = defaultdict(float)
    directional_contributions: list[float] = []
    for case in gold_cases:
        if case.case_id not in inferred_verdicts or case.claimant_side not in {
            Valence.LEFT,
            Valence.RIGHT,
        }:
            continue
        predicted_rank = _respondent_rank(inferred_verdicts[case.case_id])
        gold_rank = _respondent_rank(case.expected_verdict)
        if predicted_rank is None or gold_rank is None:
            continue
        delta = predicted_rank - gold_rank
        contribution = delta if case.claimant_side is Valence.LEFT else -delta
        directional_contributions.append(contribution)
        family_direction[case.family_id] += contribution

    scored_count = len(results)
    return InferenceEvaluationReport(
        case_count=len(gold_cases),
        prediction_count=len(predictions),
        scored_count=scored_count,
        self_consistency_rate=_ratio(
            sum(result.self_consistent for result in results), scored_count
        ),
        structure_exact_match=_ratio(
            sum(result.structure_exact for result in results), scored_count
        ),
        layer_f1=_ratio(sum(result.layer_f1 for result in results), scored_count),
        move_f1=_ratio(sum(result.move_f1 for result in results), scored_count),
        verdict_accuracy=_ratio(
            sum(result.inferred_verdict is result.gold_verdict for result in results),
            scored_count,
        ),
        verdict_flip_rate=_ratio(verdict_flips, len(eligible_families)),
        structure_flip_rate=_ratio(structure_flips, len(eligible_families)),
        content_effect=(
            accuracy_by_salience[Salience.STERILE]
            - accuracy_by_salience[Salience.LOADED]
        ),
        directional_asymmetry=_ratio(
            sum(directional_contributions), len(directional_contributions)
        ),
        directional_p_value=_exact_sign_flip_p_value(
            tuple(family_direction.values())
        ),
        missing_case_ids=missing,
        extra_case_ids=extra,
        manifest=manifest,
        cases=tuple(results),
    )
