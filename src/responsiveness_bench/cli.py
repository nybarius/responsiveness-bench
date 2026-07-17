from __future__ import annotations

import argparse
import json
import signal
import sys
from collections.abc import Sequence
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .codec import load_cases, load_predictions, write_predictions
from .agreement import measure_annotation_agreement
from .audit import audit_constant_policies
from .evaluation import evaluate_predictions
from .inference import evaluate_inference, load_inference_predictions
from .invariance import validate_dataset
from .protocol import PromptArm, build_manifest, inference_schema, prompt_text
from .scoring import score_case


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _emit(value: Any) -> None:
    print(json.dumps(_jsonable(value), indent=2, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="responsiveness-bench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="validate a JSONL corpus")
    validate.add_argument("dataset", type=Path)

    oracle = subparsers.add_parser(
        "oracle", help="write deterministic kernel verdicts as predictions"
    )
    oracle.add_argument("dataset", type=Path)
    oracle.add_argument("output", type=Path)

    evaluate = subparsers.add_parser("evaluate", help="evaluate prediction JSONL")
    evaluate.add_argument("dataset", type=Path)
    evaluate.add_argument("predictions", type=Path)
    evaluate.add_argument("--model-id", default="external")

    inference = subparsers.add_parser(
        "evaluate-inference", help="evaluate emitted full structures"
    )
    inference.add_argument("dataset", type=Path)
    inference.add_argument("predictions", type=Path)
    inference.add_argument("--model-id", required=True)
    inference.add_argument(
        "--prompt-arm",
        choices=(PromptArm.ZERO_SHOT.value, PromptArm.FEW_SHOT.value),
        required=True,
    )

    prepare = subparsers.add_parser(
        "prepare-inference", help="write raw claim-response inputs"
    )
    prepare.add_argument("dataset", type=Path)
    prepare.add_argument("output", type=Path)

    schema = subparsers.add_parser("schema", help="emit inference JSON schema")

    prompt = subparsers.add_parser("prompt", help="emit a fixed inference prompt")
    prompt.add_argument(
        "arm", choices=(PromptArm.ZERO_SHOT.value, PromptArm.FEW_SHOT.value)
    )

    audit = subparsers.add_parser("audit", help="run constant-policy exploit audit")
    audit.add_argument("dataset", type=Path)
    audit.add_argument("--threshold", type=float, default=0.75)
    audit.add_argument("--check", action="store_true")

    agreement = subparsers.add_parser(
        "agreement", help="measure field-level annotation agreement"
    )
    agreement.add_argument("annotations", type=Path, nargs="+")

    score = subparsers.add_parser("score", help="emit per-case kernel reports")
    score.add_argument("dataset", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(signal, "SIGPIPE"):
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    args = _parser().parse_args(argv)
    if args.command == "validate":
        report = validate_dataset(load_cases(args.dataset))
        _emit(report)
        return 0 if report.valid else 1
    if args.command == "oracle":
        cases = load_cases(args.dataset)
        predictions = {case.case_id: score_case(case).verdict for case in cases}
        write_predictions(args.output, predictions)
        _emit({"output": str(args.output), "prediction_count": len(predictions)})
        return 0
    if args.command == "evaluate":
        report = evaluate_predictions(
            load_cases(args.dataset), load_predictions(args.predictions)
        )
        payload = _jsonable(report)
        payload["manifest"] = _jsonable(
            build_manifest(
                args.dataset,
                model_id=args.model_id,
                prompt_arm=PromptArm.VERDICT_ONLY,
            )
        )
        _emit(payload)
        return 0
    if args.command == "evaluate-inference":
        manifest = build_manifest(
            args.dataset, model_id=args.model_id, prompt_arm=args.prompt_arm
        )
        report = evaluate_inference(
            load_cases(args.dataset),
            load_inference_predictions(args.predictions),
            manifest=manifest,
        )
        _emit(report)
        return 0
    if args.command == "prepare-inference":
        cases = load_cases(args.dataset)
        records = [
            {
                "case_id": case.case_id,
                "claim": case.claim_text,
                "response": case.response_text,
            }
            for case in cases
        ]
        args.output.write_text(
            "".join(json.dumps(record, sort_keys=True) + "\n" for record in records),
            encoding="utf-8",
        )
        _emit({"case_count": len(records), "output": str(args.output)})
        return 0
    if args.command == "schema":
        _emit(inference_schema())
        return 0
    if args.command == "prompt":
        print(prompt_text(args.arm), end="")
        return 0
    if args.command == "audit":
        report = audit_constant_policies(
            load_cases(args.dataset), threshold=args.threshold
        )
        payload = _jsonable(report)
        payload["manifest"] = _jsonable(
            build_manifest(
                args.dataset,
                model_id="constant-policy-audit",
                prompt_arm=PromptArm.TYPED_INPUT,
            )
        )
        _emit(payload)
        return 1 if args.check and not report.passed else 0
    if args.command == "agreement":
        _emit(
            measure_annotation_agreement(
                load_cases(path) for path in args.annotations
            )
        )
        return 0
    if args.command == "score":
        _emit(
            {
                "manifest": build_manifest(
                    args.dataset,
                    model_id="kernel",
                    prompt_arm=PromptArm.TYPED_INPUT,
                ),
                "reports": [score_case(case) for case in load_cases(args.dataset)],
            }
        )
        return 0
    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
