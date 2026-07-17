from __future__ import annotations


def test_public_api_exposes_constant_policy_audit() -> None:
    import responsiveness_bench as rb

    assert hasattr(rb, "ExploitAuditReport")
    assert hasattr(rb, "audit_constant_policies")

import json
from pathlib import Path

import pytest

from responsiveness_bench import audit_constant_policies, load_cases
from responsiveness_bench.cli import main

SEED = Path(__file__).parents[1] / "data" / "seed"


def test_seed_constant_policies_stay_below_exploit_threshold() -> None:
    report = audit_constant_policies(load_cases(SEED))
    scores = {score.policy: score.accuracy for score in report.scores}

    assert scores == {
        "always_request_evidence": 21 / 33,
        "always_deny_first_layer": 18 / 33,
        "always_fully_responsive": 18 / 33,
    }
    assert report.passed is True


def test_audit_cli_can_enforce_threshold(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["audit", str(SEED), "--check"]) == 0
    output = json.loads(capsys.readouterr().out)

    assert output["passed"] is True
    assert output["manifest"]["model_id"] == "constant-policy-audit"
