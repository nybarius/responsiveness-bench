"""Responsiveness Bench public API."""

from .model import (
    AdjudicationStatus,
    Case,
    ClaimKind,
    ClaimLayer,
    LayerKind,
    Provenance,
    Relation,
    ResponseAct,
    ResponseMove,
    Salience,
    ScoreReport,
    Valence,
    Verdict,
)
from .scoring import score_case

__all__ = [
    "AdjudicationStatus",
    "Case",
    "ClaimKind",
    "ClaimLayer",
    "LayerKind",
    "Provenance",
    "Relation",
    "ResponseAct",
    "ResponseMove",
    "Salience",
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

from .protocol import (
    PromptArm,
    RunManifest,
    build_manifest,
    dataset_hash,
    inference_schema,
    prompt_hash,
    prompt_text,
    protocol_hash,
)

__all__ += [
    "PromptArm",
    "RunManifest",
    "build_manifest",
    "dataset_hash",
    "inference_schema",
    "prompt_hash",
    "prompt_text",
    "protocol_hash",
]
from .inference import (
    InferenceCaseResult,
    InferenceEvaluationReport,
    InferencePrediction,
    evaluate_inference,
    inference_prediction_from_record,
    load_inference_predictions,
)

__all__ += [
    "InferenceCaseResult",
    "InferenceEvaluationReport",
    "InferencePrediction",
    "evaluate_inference",
    "inference_prediction_from_record",
    "load_inference_predictions",
]
from .audit import ExploitAuditReport, PolicyScore, audit_constant_policies

__all__ += ["ExploitAuditReport", "PolicyScore", "audit_constant_policies"]
from .agreement import (
    AgreementReport,
    krippendorff_alpha_nominal,
    measure_annotation_agreement,
)

__all__ += [
    "AgreementReport",
    "krippendorff_alpha_nominal",
    "measure_annotation_agreement",
]
