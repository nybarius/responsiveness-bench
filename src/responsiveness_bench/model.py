from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Verdict(StrEnum):
    FULLY_RESPONSIVE = "fully_responsive"
    PARTIALLY_RESPONSIVE = "partially_responsive"
    NONRESPONSIVE = "nonresponsive"
    INVALID = "invalid"


class ClaimKind(StrEnum):
    ASSERTION = "assertion"
    CAUSAL = "causal"
    CONDITIONAL = "conditional"
    NORMATIVE = "normative"
    COMPARATIVE = "comparative"


class LayerKind(StrEnum):
    EXPLICIT = "explicit"
    IMPLICATED = "implicated"


class ResponseAct(StrEnum):
    ADMIT = "admit"
    DENY = "deny"
    QUALIFY = "qualify"
    REQUEST_EVIDENCE = "request_evidence"
    COUNTERASSERT = "counterassert"
    DEFLECT = "deflect"
    IGNORE = "ignore"


class Relation(StrEnum):
    SAME = "same"
    CONTRADICTS = "contradicts"
    ENTAILS = "entails"
    NARROWS = "narrows"
    IRRELEVANT = "irrelevant"
    UNKNOWN = "unknown"


class Valence(StrEnum):
    LEFT = "left"
    RIGHT = "right"
    NEUTRAL = "neutral"


@dataclass(frozen=True, slots=True)
class ClaimLayer:
    layer_id: str
    text: str
    kind: ClaimKind = ClaimKind.ASSERTION
    layer_kind: LayerKind = LayerKind.EXPLICIT
    required: bool = True


@dataclass(frozen=True, slots=True)
class ResponseMove:
    move_id: str
    text: str
    act: ResponseAct
    target_layer_id: str | None = None
    relation: Relation = Relation.UNKNOWN


@dataclass(frozen=True, slots=True)
class Case:
    case_id: str
    family_id: str
    variant: str
    valence: Valence
    claim_layers: tuple[ClaimLayer, ...]
    response_moves: tuple[ResponseMove, ...]
    expected_verdict: Verdict | None = None
    source: str | None = None
    annotation_notes: str | None = None


@dataclass(frozen=True, slots=True)
class ScoreReport:
    case_id: str
    verdict: Verdict
    covered_layer_ids: tuple[str, ...] = ()
    uncovered_layer_ids: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
