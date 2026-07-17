"""Responsiveness Bench public API."""

from .model import (
    Case,
    ClaimKind,
    ClaimLayer,
    LayerKind,
    Relation,
    ResponseAct,
    ResponseMove,
    ScoreReport,
    Valence,
    Verdict,
)
from .scoring import score_case

__all__ = [
    "Case",
    "ClaimKind",
    "ClaimLayer",
    "LayerKind",
    "Relation",
    "ResponseAct",
    "ResponseMove",
    "ScoreReport",
    "Valence",
    "Verdict",
    "score_case",
]
from .invariance import (
    DatasetValidationReport,
    ValidationIssue,
    structural_signature,
    validate_dataset,
)

__all__ += [
    "DatasetValidationReport",
    "ValidationIssue",
    "structural_signature",
    "validate_dataset",
]
from .evaluation import EvaluationReport, evaluate_predictions

__all__ += ["EvaluationReport", "evaluate_predictions"]
from .codec import (
    CorpusFormatError,
    case_from_record,
    case_to_record,
    load_cases,
    load_predictions,
    write_cases,
    write_predictions,
)

__all__ += [
    "CorpusFormatError",
    "case_from_record",
    "case_to_record",
    "load_cases",
    "load_predictions",
    "write_cases",
    "write_predictions",
]
