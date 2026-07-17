from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .model import (
    Case,
    ClaimKind,
    ClaimLayer,
    LayerKind,
    Relation,
    ResponseAct,
    ResponseMove,
    Valence,
    Verdict,
)


class CorpusFormatError(ValueError):
    """Raised when a corpus or prediction record cannot be decoded."""


def case_to_record(case: Case) -> dict[str, Any]:
    return {
        "annotation_notes": case.annotation_notes,
        "case_id": case.case_id,
        "claim_layers": [
            {
                "kind": layer.kind.value,
                "layer_id": layer.layer_id,
                "layer_kind": layer.layer_kind.value,
                "required": layer.required,
                "text": layer.text,
            }
            for layer in case.claim_layers
        ],
        "expected_verdict": (
            case.expected_verdict.value if case.expected_verdict is not None else None
        ),
        "family_id": case.family_id,
        "response_moves": [
            {
                "act": move.act.value,
                "move_id": move.move_id,
                "relation": move.relation.value,
                "target_layer_id": move.target_layer_id,
                "text": move.text,
            }
            for move in case.response_moves
        ],
        "source": case.source,
        "valence": case.valence.value,
        "variant": case.variant,
    }


def _required_string(record: Mapping[str, Any], key: str) -> str:
    value = record[key]
    if not isinstance(value, str) or not value:
        raise CorpusFormatError(f"'{key}' must be a non-empty string")
    return value


def case_from_record(record: Mapping[str, Any]) -> Case:
    try:
        raw_layers = record["claim_layers"]
        raw_moves = record["response_moves"]
        if not isinstance(raw_layers, list):
            raise CorpusFormatError("'claim_layers' must be a list")
        if not isinstance(raw_moves, list):
            raise CorpusFormatError("'response_moves' must be a list")

        layers = tuple(
            ClaimLayer(
                layer_id=_required_string(layer, "layer_id"),
                text=_required_string(layer, "text"),
                kind=ClaimKind(layer.get("kind", ClaimKind.ASSERTION.value)),
                layer_kind=LayerKind(
                    layer.get("layer_kind", LayerKind.EXPLICIT.value)
                ),
                required=bool(layer.get("required", True)),
            )
            for layer in raw_layers
        )
        moves = tuple(
            ResponseMove(
                move_id=_required_string(move, "move_id"),
                text=_required_string(move, "text"),
                act=ResponseAct(move["act"]),
                target_layer_id=move.get("target_layer_id"),
                relation=Relation(move.get("relation", Relation.UNKNOWN.value)),
            )
            for move in raw_moves
        )
        raw_expected = record.get("expected_verdict")
        return Case(
            case_id=_required_string(record, "case_id"),
            family_id=_required_string(record, "family_id"),
            variant=_required_string(record, "variant"),
            valence=Valence(record["valence"]),
            claim_layers=layers,
            response_moves=moves,
            expected_verdict=(
                Verdict(raw_expected) if raw_expected is not None else None
            ),
            source=record.get("source"),
            annotation_notes=record.get("annotation_notes"),
        )
    except CorpusFormatError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise CorpusFormatError(str(exc)) from exc


def load_cases(path: str | Path) -> tuple[Case, ...]:
    source = Path(path)
    cases: list[Case] = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise CorpusFormatError("record must be a JSON object")
            cases.append(case_from_record(record))
        except (json.JSONDecodeError, CorpusFormatError) as exc:
            raise CorpusFormatError(f"{source.name}:{line_number}: {exc}") from exc
    return tuple(cases)


def write_cases(path: str | Path, cases: Iterable[Case]) -> None:
    destination = Path(path)
    lines = [json.dumps(case_to_record(case), sort_keys=True) for case in cases]
    destination.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def load_predictions(path: str | Path) -> dict[str, Verdict]:
    source = Path(path)
    predictions: dict[str, Verdict] = {}
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
            if not isinstance(record, dict):
                raise CorpusFormatError("record must be a JSON object")
            case_id = _required_string(record, "case_id")
            if case_id in predictions:
                raise CorpusFormatError(f"duplicate prediction for '{case_id}'")
            predictions[case_id] = Verdict(record["verdict"])
        except (json.JSONDecodeError, CorpusFormatError, KeyError, ValueError) as exc:
            raise CorpusFormatError(f"{source.name}:{line_number}: {exc}") from exc
    return predictions


def write_predictions(path: str | Path, predictions: Mapping[str, Verdict]) -> None:
    destination = Path(path)
    lines = [
        json.dumps(
            {"case_id": case_id, "verdict": predictions[case_id].value},
            sort_keys=True,
        )
        for case_id in sorted(predictions)
    ]
    destination.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
