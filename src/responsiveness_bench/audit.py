from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable

from .model import Case, Relation, ResponseAct, ResponseMove, Verdict
from .scoring import score_case


@dataclass(frozen=True, slots=True)
class PolicyScore:
    policy: str
    correct: int
    total: int
    accuracy: float


@dataclass(frozen=True, slots=True)
class ExploitAuditReport:
    case_count: int
    scores: tuple[PolicyScore, ...]
    max_accuracy: float
    threshold: float
    passed: bool


def _accuracy(policy: str, gold: tuple[Case, ...], predictions: tuple[Verdict, ...]) -> PolicyScore:
    correct = sum(
        prediction is case.expected_verdict
        for case, prediction in zip(gold, predictions)
    )
    total = len(gold)
    return PolicyScore(
        policy=policy,
        correct=correct,
        total=total,
        accuracy=(correct / total if total else 0.0),
    )


def _request_every_layer(case: Case) -> Verdict:
    moves = tuple(
        ResponseMove(
            move_id=f"request-{index}",
            text="What evidence supports this?",
            act=ResponseAct.REQUEST_EVIDENCE,
            target_layer_id=layer.layer_id,
            relation=Relation.SAME,
        )
        for index, layer in enumerate(case.claim_layers)
        if layer.required
    )
    return score_case(replace(case, response_moves=moves)).verdict


def _deny_first_layer(case: Case) -> Verdict:
    first = next(layer for layer in case.claim_layers if layer.required)
    move = ResponseMove(
        move_id="deny-first",
        text="No.",
        act=ResponseAct.DENY,
        target_layer_id=first.layer_id,
        relation=Relation.CONTRADICTS,
    )
    return score_case(replace(case, response_moves=(move,))).verdict


def audit_constant_policies(
    cases: Iterable[Case], *, threshold: float = 0.75
) -> ExploitAuditReport:
    gold = tuple(case for case in cases if case.expected_verdict is not None)
    scores = (
        _accuracy(
            "always_request_evidence",
            gold,
            tuple(_request_every_layer(case) for case in gold),
        ),
        _accuracy(
            "always_deny_first_layer",
            gold,
            tuple(_deny_first_layer(case) for case in gold),
        ),
        _accuracy(
            "always_fully_responsive",
            gold,
            tuple(Verdict.FULLY_RESPONSIVE for _ in gold),
        ),
    )
    max_accuracy = max((score.accuracy for score in scores), default=0.0)
    return ExploitAuditReport(
        case_count=len(gold),
        scores=scores,
        max_accuracy=max_accuracy,
        threshold=threshold,
        passed=max_accuracy < threshold,
    )
