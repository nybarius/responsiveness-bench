from __future__ import annotations

from collections import Counter
from pathlib import Path

from responsiveness_bench import Verdict, load_cases, score_case, validate_dataset

SEED = Path(__file__).parents[1] / "data" / "seed.jsonl"


def test_seed_corpus_is_complete_and_self_validating() -> None:
    cases = load_cases(SEED)

    report = validate_dataset(cases)

    assert report.valid is True
    assert report.case_count == 18
    assert report.family_count == 6
    assert report.issues == ()


def test_seed_corpus_covers_each_responsiveness_verdict() -> None:
    cases = load_cases(SEED)

    counts = Counter(score_case(case).verdict for case in cases)

    assert counts == {
        Verdict.FULLY_RESPONSIVE: 12,
        Verdict.PARTIALLY_RESPONSIVE: 3,
        Verdict.NONRESPONSIVE: 3,
    }


def test_every_seed_family_is_a_left_right_neutral_triple() -> None:
    cases = load_cases(SEED)
    by_family: dict[str, set[str]] = {}
    for case in cases:
        by_family.setdefault(case.family_id, set()).add(case.valence.value)

    assert all(values == {"left", "right", "neutral"} for values in by_family.values())
