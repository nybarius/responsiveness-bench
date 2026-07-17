from __future__ import annotations

from dataclasses import replace

from responsiveness_bench import (
    Case,
    ClaimLayer,
    Relation,
    ResponseAct,
    ResponseMove,
    Valence,
    Verdict,
    structural_signature,
    validate_dataset,
)


def variant(
    *,
    case_id: str,
    valence: Valence,
    claim_text: str,
    response_text: str,
    expected: Verdict = Verdict.FULLY_RESPONSIVE,
    relation: Relation = Relation.CONTRADICTS,
) -> Case:
    return Case(
        case_id=case_id,
        family_id="direct-denial",
        variant=valence.value,
        valence=valence,
        claim_layers=(ClaimLayer("claim", claim_text),),
        response_moves=(
            ResponseMove(
                "response",
                response_text,
                ResponseAct.DENY,
                "claim",
                relation,
            ),
        ),
        expected_verdict=expected,
    )


def trio() -> tuple[Case, Case, Case]:
    return (
        variant(
            case_id="left",
            valence=Valence.LEFT,
            claim_text="The conservative policy causes harm.",
            response_text="It does not cause harm.",
        ),
        variant(
            case_id="right",
            valence=Valence.RIGHT,
            claim_text="The progressive policy causes harm.",
            response_text="It does not cause harm.",
        ),
        variant(
            case_id="neutral",
            valence=Valence.NEUTRAL,
            claim_text="The cache policy causes latency.",
            response_text="It does not cause latency.",
        ),
    )


def test_signature_ignores_text_ids_and_valence() -> None:
    left, right, neutral = trio()

    assert structural_signature(left) == structural_signature(right)
    assert structural_signature(right) == structural_signature(neutral)


def test_signature_changes_when_response_relation_changes() -> None:
    left, _, _ = trio()
    altered = replace(
        left,
        response_moves=(
            replace(left.response_moves[0], relation=Relation.IRRELEVANT),
        ),
    )

    assert structural_signature(left) != structural_signature(altered)


def test_complete_structurally_equivalent_trio_is_valid() -> None:
    report = validate_dataset(trio())

    assert report.valid is True
    assert report.case_count == 3
    assert report.family_count == 1
    assert report.issues == ()


def test_mislabeled_case_is_detected_by_kernel_agreement() -> None:
    left, right, neutral = trio()
    mislabeled = replace(right, expected_verdict=Verdict.NONRESPONSIVE)

    report = validate_dataset((left, mislabeled, neutral))

    assert report.valid is False
    assert [issue.code for issue in report.issues] == [
        "label_disagrees_with_kernel",
        "family_label_mismatch",
    ]
    assert report.issues[0].case_id == "right"


def test_structural_mismatch_is_detected_within_family() -> None:
    left, right, neutral = trio()
    mismatched = replace(
        neutral,
        response_moves=(
            replace(neutral.response_moves[0], relation=Relation.IRRELEVANT),
        ),
        expected_verdict=Verdict.NONRESPONSIVE,
    )

    report = validate_dataset((left, right, mismatched))

    assert "family_structure_mismatch" in {issue.code for issue in report.issues}


def test_incomplete_valence_trio_is_rejected() -> None:
    left, right, _ = trio()

    report = validate_dataset((left, right))

    assert [issue.code for issue in report.issues] == ["family_missing_valence"]
    assert "neutral" in report.issues[0].message


def test_duplicate_case_id_is_rejected() -> None:
    left, right, neutral = trio()
    duplicate = replace(neutral, case_id=left.case_id)

    report = validate_dataset((left, right, duplicate))

    assert "duplicate_case_id" in {issue.code for issue in report.issues}
