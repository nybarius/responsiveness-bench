from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable
from uuid import UUID

from .model import AdjudicationStatus, Case, Valence
from .scoring import score_case


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    case_id: str | None = None
    family_id: str | None = None


@dataclass(frozen=True, slots=True)
class DatasetValidationReport:
    valid: bool
    case_count: int
    family_count: int
    issues: tuple[ValidationIssue, ...] = ()


def structural_signature(case: Case) -> tuple[Any, ...]:
    """Return the content-free claim-response structure for invariance checks."""
    attachment_profiles: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for move in case.response_moves:
        if move.target_layer_id is not None:
            attachment_profiles[move.target_layer_id].append(
                (move.act.value, move.relation.value)
            )

    canonical_layers = tuple(
        sorted(
            case.claim_layers,
            key=lambda layer: (
                layer.layer_kind.value,
                layer.kind.value,
                layer.required,
                layer.backed,
                tuple(sorted(attachment_profiles[layer.layer_id])),
            ),
        )
    )
    target_positions = {
        layer.layer_id: index for index, layer in enumerate(canonical_layers)
    }
    layers = tuple(
        (
            layer.kind.value,
            layer.layer_kind.value,
            layer.required,
            layer.backed,
        )
        for layer in canonical_layers
    )
    moves = tuple(
        sorted(
            (
                move.act.value,
                (
                    target_positions[move.target_layer_id]
                    if move.target_layer_id in target_positions
                    else None
                ),
                move.relation.value,
            )
            for move in case.response_moves
        )
    )
    return layers, moves


def validate_dataset(cases: Iterable[Case]) -> DatasetValidationReport:
    materialized = tuple(cases)
    gold = tuple(
        case
        for case in materialized
        if case.adjudication_status is AdjudicationStatus.GOLD
    )
    issues: list[ValidationIssue] = []

    case_id_counts = Counter(case.case_id for case in materialized)
    for case_id in sorted(case_id for case_id, count in case_id_counts.items() if count > 1):
        issues.append(
            ValidationIssue(
                code="duplicate_case_id",
                message=f"case id '{case_id}' appears more than once",
                case_id=case_id,
            )
        )

    canaries = {
        case.contamination_canary
        for case in materialized
        if case.contamination_canary is not None
    }
    if canaries:
        if len(canaries) != 1 or any(
            case.contamination_canary is None for case in materialized
        ):
            issues.append(
                ValidationIssue(
                    code="dataset_canary_mismatch",
                    message="all records must carry one identical contamination canary",
                )
            )
        for canary in sorted(canaries):
            try:
                UUID(canary)
            except (ValueError, AttributeError):
                issues.append(
                    ValidationIssue(
                        code="invalid_contamination_canary",
                        message=f"contamination canary '{canary}' is not a GUID",
                    )
                )

    for case in materialized:
        score = score_case(case)
        if score.errors:
            issues.append(
                ValidationIssue(
                    code="case_invalid",
                    message="; ".join(score.errors),
                    case_id=case.case_id,
                    family_id=case.family_id,
                )
            )
        if case.adjudication_status is AdjudicationStatus.CONTESTED:
            continue
        if case.expected_verdict is None:
            issues.append(
                ValidationIssue(
                    code="missing_expected_verdict",
                    message="gold case has no expected verdict",
                    case_id=case.case_id,
                    family_id=case.family_id,
                )
            )
        elif case.expected_verdict is not score.verdict:
            issues.append(
                ValidationIssue(
                    code="label_disagrees_with_kernel",
                    message=(
                        f"expected '{case.expected_verdict.value}' but kernel "
                        f"computed '{score.verdict.value}'"
                    ),
                    case_id=case.case_id,
                    family_id=case.family_id,
                )
            )

    families: dict[str, list[Case]] = defaultdict(list)
    for case in gold:
        families[case.family_id].append(case)

    required_valences = frozenset(Valence)
    for family_id in sorted(families):
        family = families[family_id]
        present_valences = {case.valence for case in family}
        missing = sorted(
            (valence.value for valence in required_valences - present_valences)
        )
        if missing:
            issues.append(
                ValidationIssue(
                    code="family_missing_valence",
                    message=f"family is missing valence(s): {', '.join(missing)}",
                    family_id=family_id,
                )
            )

        valence_counts = Counter(case.valence for case in family)
        duplicates = sorted(
            valence.value for valence, count in valence_counts.items() if count > 1
        )
        if duplicates:
            issues.append(
                ValidationIssue(
                    code="family_duplicate_valence",
                    message=f"family repeats valence(s): {', '.join(duplicates)}",
                    family_id=family_id,
                )
            )

        signatures = {structural_signature(case) for case in family}
        if len(signatures) > 1:
            issues.append(
                ValidationIssue(
                    code="family_structure_mismatch",
                    message="family variants do not share one structural signature",
                    family_id=family_id,
                )
            )

        labels = {case.expected_verdict for case in family}
        if len(labels) > 1:
            issues.append(
                ValidationIssue(
                    code="family_label_mismatch",
                    message="family variants do not share one expected verdict",
                    family_id=family_id,
                )
            )

    return DatasetValidationReport(
        valid=not issues,
        case_count=len(materialized),
        family_count=len(families),
        issues=tuple(issues),
    )
