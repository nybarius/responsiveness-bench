from __future__ import annotations


def test_public_api_exposes_annotation_agreement() -> None:
    import responsiveness_bench as rb

    assert hasattr(rb, "AgreementReport")
    assert hasattr(rb, "krippendorff_alpha_nominal")
    assert hasattr(rb, "measure_annotation_agreement")

from dataclasses import replace

from responsiveness_bench import (
    Case,
    ClaimLayer,
    Relation,
    ResponseAct,
    ResponseMove,
    Valence,
    measure_annotation_agreement,
)


def _case(relation: Relation = Relation.CONTRADICTS) -> Case:
    return Case(
        case_id="case",
        family_id="family",
        variant="neutral",
        valence=Valence.NEUTRAL,
        claim_layers=(ClaimLayer("p", "Claim."),),
        response_moves=(
            ResponseMove("r", "Response.", ResponseAct.DENY, "p", relation),
        ),
    )


def test_agreement_reports_field_alphas_and_contested_cases() -> None:
    first = _case()
    second = replace(
        first,
        response_moves=(
            replace(first.response_moves[0], relation=Relation.IRRELEVANT),
        ),
    )

    report = measure_annotation_agreement(((first,), (second,)))

    assert report.case_count == 1
    assert report.alpha["layer_count"] == 1.0
    assert report.alpha["act"] == 1.0
    assert report.alpha["target"] == 1.0
    assert report.alpha["relation"] < 1.0
    assert report.contested_case_ids == ("case",)
