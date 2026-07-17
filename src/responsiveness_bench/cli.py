from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .codec import load_cases, load_predictions, write_predictions
from .evaluation import evaluate_predictions
from .invariance import validate_dataset
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

    score = subparsers.add_parser("score", help="emit per-case kernel reports")
    score.add_argument("dataset", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
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
        _emit(report)
        return 0
    if args.command == "score":
        _emit([score_case(case) for case in load_cases(args.dataset)])
        return 0
    print(f"unknown command: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
