from __future__ import annotations

import json
from pathlib import Path

import pytest

from responsiveness_bench import (
    Case,
    ClaimKind,
    ClaimLayer,
    CorpusFormatError,
    LayerKind,
    Relation,
    ResponseAct,
    ResponseMove,
    Valence,
    Verdict,
    case_from_record,
    case_to_record,
    load_cases,
    load_predictions,
    write_cases,
)
from responsiveness_bench.cli import main


def sample_case(case_id: str = "sample") -> Case:
    return Case(
        case_id=case_id,
        family_id="family",
        variant="left",
        valence=Valence.LEFT,
        claim_layers=(
            ClaimLayer(
                "surface",
                "The audit found no discrepancy.",
                ClaimKind.ASSERTION,
                LayerKind.EXPLICIT,
            ),
            ClaimLayer(
                "implication",
                "Therefore every concern is baseless.",
                ClaimKind.CONDITIONAL,
                LayerKind.IMPLICATED,
            ),
        ),
        response_moves=(
            ResponseMove(
                "move-1",
                "I accept the audit result but deny the implication.",
                ResponseAct.ADMIT,
                "surface",
                Relation.SAME,
            ),
            ResponseMove(
                "move-2",
                "The broader inference does not follow.",
                ResponseAct.DENY,
                "implication",
                Relation.CONTRADICTS,
            ),
        ),
        expected_verdict=Verdict.FULLY_RESPONSIVE,
        source="transcript:raffensperger",
        annotation_notes="Bilayer example.",
    )


def test_case_record_round_trip_preserves_typed_structure() -> None:
    original = sample_case()

    restored = case_from_record(case_to_record(original))

    assert restored == original


def test_jsonl_round_trip_is_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    cases = (sample_case("b"), sample_case("a"))

    write_cases(path, cases)
    restored = load_cases(path)

    assert restored == cases
    lines = path.read_text().splitlines()
    assert len(lines) == 2
    assert lines[0] == json.dumps(case_to_record(cases[0]), sort_keys=True)


def test_bad_jsonl_reports_line_number(tmp_path: Path) -> None:
    path = tmp_path / "bad.jsonl"
    path.write_text('{"case_id": "ok"}\nnot-json\n')

    with pytest.raises(CorpusFormatError, match=r"bad\.jsonl:1"):
        load_cases(path)


def test_validate_cli_emits_machine_readable_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset = tmp_path / "dataset.jsonl"
    base = sample_case("left")
    trio = (
        base,
        Case(
            case_id="right",
            family_id=base.family_id,
            variant="right",
            valence=Valence.RIGHT,
            claim_layers=base.claim_layers,
            response_moves=base.response_moves,
            expected_verdict=base.expected_verdict,
            source=base.source,
            annotation_notes=base.annotation_notes,
        ),
        Case(
            case_id="neutral",
            family_id=base.family_id,
            variant="neutral",
            valence=Valence.NEUTRAL,
            claim_layers=base.claim_layers,
            response_moves=base.response_moves,
            expected_verdict=base.expected_verdict,
            source=base.source,
            annotation_notes=base.annotation_notes,
        ),
    )
    write_cases(dataset, trio)

    exit_code = main(["validate", str(dataset)])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["valid"] is True
    assert output["case_count"] == 3


def test_oracle_and_evaluate_cli_compose_end_to_end(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dataset = tmp_path / "dataset.jsonl"
    predictions = tmp_path / "predictions.jsonl"
    base = sample_case("left")
    trio = tuple(
        Case(
            case_id=valence.value,
            family_id=base.family_id,
            variant=valence.value,
            valence=valence,
            claim_layers=base.claim_layers,
            response_moves=base.response_moves,
            expected_verdict=base.expected_verdict,
        )
        for valence in Valence
    )
    write_cases(dataset, trio)

    assert main(["oracle", str(dataset), str(predictions)]) == 0
    assert load_predictions(predictions) == {
        "left": Verdict.FULLY_RESPONSIVE,
        "neutral": Verdict.FULLY_RESPONSIVE,
        "right": Verdict.FULLY_RESPONSIVE,
    }
    capsys.readouterr()

    assert main(["evaluate", str(dataset), str(predictions)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["accuracy"] == 1.0
    assert output["left_right_consistency"] == 1.0
