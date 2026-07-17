from __future__ import annotations

from collections import Counter
from pathlib import Path

from responsiveness_bench import Verdict, load_cases, score_case, validate_dataset

SEED = Path(__file__).parents[1] / "data" / "seed"


def test_seed_corpus_is_complete_and_self_validating() -> None:
    cases = load_cases(SEED)

    report = validate_dataset(cases)

    assert report.valid is True
    assert report.case_count == 33
    assert report.family_count == 11
    assert report.issues == ()


def test_seed_corpus_covers_each_responsiveness_verdict() -> None:
    cases = load_cases(SEED)

    counts = Counter(score_case(case).verdict for case in cases)

    assert counts == {
        Verdict.FULLY_RESPONSIVE: 18,
        Verdict.PARTIALLY_RESPONSIVE: 3,
        Verdict.NONRESPONSIVE: 12,
    }


def test_every_seed_family_is_a_left_right_neutral_triple() -> None:
    cases = load_cases(SEED)
    by_family: dict[str, set[str]] = {}
    for case in cases:
        by_family.setdefault(case.family_id, set()).add(case.valence.value)

    assert all(values == {"left", "right", "neutral"} for values in by_family.values())


def test_seed_cases_carry_inference_heat_and_provenance_fields() -> None:
    cases = load_cases(SEED)

    canaries = {case.contamination_canary for case in cases}
    assert len(canaries) == 1
    assert None not in canaries
    assert all(case.claim_text for case in cases)
    assert all(case.response_text for case in cases)
    assert all(case.claimant_side is not None for case in cases)
    assert all(case.provenance is not None for case in cases)
    assert all(case.provenance.date for case in cases if case.provenance)
    assert all(
        case.salience.value == ("sterile" if case.valence.value == "neutral" else "loaded")
        for case in cases
    )


def test_new_seed_families_preserve_aimed_but_nonengaging_moves() -> None:
    by_id = {case.case_id: case for case in load_cases(SEED)}

    posture = by_id["posture-occurrence-neutral"]
    assert posture.response_moves[0].act.value == "deny"
    assert posture.response_moves[0].target_layer_id == "posture"
    assert posture.response_moves[0].relation.value == "irrelevant"
    assert posture.expected_verdict is Verdict.NONRESPONSIVE

    channel = by_id["channel-content-neutral"]
    assert channel.response_moves[0].relation.value == "scope_mismatch"
    assert channel.expected_verdict is Verdict.NONRESPONSIVE


def test_new_seed_families_cover_inverse_and_burden_traps() -> None:
    by_id = {case.case_id: case for case in load_cases(SEED)}

    entailment = by_id["entailment-counterassertion-neutral"]
    assert entailment.response_moves[0].act.value == "counterassert"
    assert entailment.response_moves[0].relation.value == "contradicts"
    assert entailment.expected_verdict is Verdict.FULLY_RESPONSIVE

    backed = by_id["backed-challenge-neutral"]
    assert backed.claim_layers[0].backed is True
    assert backed.response_moves[0].act.value == "request_evidence"
    assert backed.expected_verdict is Verdict.NONRESPONSIVE

    qualified = by_id["matched-scope-qualification-neutral"]
    assert qualified.response_moves[0].relation.value == "narrows_within_scope"
    assert qualified.expected_verdict is Verdict.FULLY_RESPONSIVE
