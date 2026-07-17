from __future__ import annotations


def test_public_api_exposes_protocol_identity_and_prompt_assets() -> None:
    import responsiveness_bench as rb

    assert hasattr(rb, "PromptArm")
    assert hasattr(rb, "RunManifest")
    assert hasattr(rb, "protocol_hash")
    assert hasattr(rb, "prompt_hash")
    assert hasattr(rb, "prompt_text")
    assert hasattr(rb, "inference_schema")
    assert hasattr(rb, "dataset_hash")

import hashlib
import json
from pathlib import Path

import pytest

from responsiveness_bench import PromptArm, dataset_hash, inference_schema, prompt_hash, protocol_hash
from responsiveness_bench.cli import main


def test_protocol_and_prompt_hashes_are_stable_and_distinct(tmp_path: Path) -> None:
    dataset = tmp_path / "data.jsonl"
    dataset.write_text("example\n", encoding="utf-8")

    descriptor = json.dumps(
        {"annotation_guide_version": "2.0.0", "kernel_version": "2.0.0"},
        separators=(",", ":"),
        sort_keys=True,
    )
    assert protocol_hash() == hashlib.sha256(descriptor.encode()).hexdigest()
    assert dataset_hash(dataset) == hashlib.sha256(b"example\n").hexdigest()
    assert prompt_hash(PromptArm.ZERO_SHOT) != prompt_hash(PromptArm.FEW_SHOT)
    assert "scope_mismatch" in inference_schema()["properties"]["response_moves"]["items"]["properties"]["relation"]["enum"]


def test_score_cli_attaches_protocol_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    from responsiveness_bench import (
        Case,
        ClaimLayer,
        Relation,
        ResponseAct,
        ResponseMove,
        Valence,
        Verdict,
        write_cases,
    )

    dataset = tmp_path / "dataset.jsonl"
    case = Case(
        case_id="neutral",
        family_id="family",
        variant="neutral",
        valence=Valence.NEUTRAL,
        claim_layers=(ClaimLayer("p", "Claim."),),
        response_moves=(
            ResponseMove("r", "No.", ResponseAct.DENY, "p", Relation.CONTRADICTS),
        ),
        expected_verdict=Verdict.FULLY_RESPONSIVE,
    )
    write_cases(dataset, (case,))

    assert main(["score", str(dataset)]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["manifest"]["model_id"] == "kernel"
    assert output["manifest"]["protocol_hash"] == protocol_hash()
    assert output["reports"][0]["case_id"] == "neutral"
