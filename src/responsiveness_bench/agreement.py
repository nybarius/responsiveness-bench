from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Hashable, Iterable, Sequence

from .model import Case


@dataclass(frozen=True, slots=True)
class AgreementReport:
    case_count: int
    alpha: dict[str, float] = field(default_factory=dict)
    contested_case_ids: tuple[str, ...] = ()


def krippendorff_alpha_nominal(
    units: Iterable[Sequence[Hashable | None]],
) -> float:
    coincidence: Counter[tuple[Hashable, Hashable]] = Counter()
    marginal: Counter[Hashable] = Counter()
    total = 0.0
    for unit in units:
        labels = [label for label in unit if label is not None]
        count = len(labels)
        if count < 2:
            continue
        weight = 1.0 / (count - 1)
        for index, left in enumerate(labels):
            marginal[left] += 1
            total += 1
            for other_index, right in enumerate(labels):
                if index != other_index:
                    coincidence[(left, right)] += weight
    if total <= 1:
        return 1.0
    observed = sum(
        value for (left, right), value in coincidence.items() if left != right
    ) / total
    expected = (
        total * total - sum(value * value for value in marginal.values())
    ) / (total * (total - 1))
    if expected == 0:
        return 1.0 if observed == 0 else 0.0
    return 1.0 - (observed / expected)


def _target_position(case: Case, move_index: int) -> int | str:
    if move_index >= len(case.response_moves):
        return "<missing>"
    target = case.response_moves[move_index].target_layer_id
    if target is None:
        return "<none>"
    positions = {layer.layer_id: index for index, layer in enumerate(case.claim_layers)}
    return positions.get(target, "<unknown>")


def measure_annotation_agreement(
    annotation_sets: Iterable[Iterable[Case]],
) -> AgreementReport:
    coders = tuple({case.case_id: case for case in cases} for cases in annotation_sets)
    if not coders:
        return AgreementReport(case_count=0)
    common_ids = set.intersection(*(set(coder) for coder in coders))
    contested: set[str] = set()
    layer_units: list[tuple[Hashable, ...]] = []
    act_units: list[tuple[Hashable, ...]] = []
    target_units: list[tuple[Hashable, ...]] = []
    relation_units: list[tuple[Hashable, ...]] = []

    for case_id in sorted(common_ids):
        cases = tuple(coder[case_id] for coder in coders)
        layer_counts = tuple(len(case.claim_layers) for case in cases)
        layer_units.append(layer_counts)
        if len(set(layer_counts)) > 1:
            contested.add(case_id)
        max_moves = max(len(case.response_moves) for case in cases)
        for index in range(max_moves):
            acts = tuple(
                case.response_moves[index].act.value
                if index < len(case.response_moves)
                else "<missing>"
                for case in cases
            )
            targets = tuple(_target_position(case, index) for case in cases)
            relations = tuple(
                case.response_moves[index].relation.value
                if index < len(case.response_moves)
                else "<missing>"
                for case in cases
            )
            act_units.append(acts)
            target_units.append(targets)
            relation_units.append(relations)
            if len(set(acts)) > 1 or len(set(targets)) > 1 or len(set(relations)) > 1:
                contested.add(case_id)

    return AgreementReport(
        case_count=len(common_ids),
        alpha={
            "layer_count": krippendorff_alpha_nominal(layer_units),
            "act": krippendorff_alpha_nominal(act_units),
            "target": krippendorff_alpha_nominal(target_units),
            "relation": krippendorff_alpha_nominal(relation_units),
        },
        contested_case_ids=tuple(sorted(contested)),
    )
