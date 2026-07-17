from __future__ import annotations

import pytest

from responsiveness_bench import (
    Case,
    ClaimLayer,
    LayerKind,
    Relation,
    ResponseAct,
    ResponseMove,
    Valence,
    Verdict,
    score_case,
)


def make_case(
    *,
    layers: tuple[ClaimLayer, ...],
    moves: tuple[ResponseMove, ...],
    case_id: str = "case",
) -> Case:
    return Case(
        case_id=case_id,
        family_id="family",
        variant="neutral",
        valence=Valence.NEUTRAL,
        claim_layers=layers,
        response_moves=moves,
    )


@pytest.mark.parametrize(
    ("act", "relation"),
    [
        (ResponseAct.ADMIT, Relation.SAME),
        (ResponseAct.DENY, Relation.CONTRADICTS),
        (ResponseAct.QUALIFY, Relation.NARROWS_WITHIN_SCOPE),
        (ResponseAct.REQUEST_EVIDENCE, Relation.SAME),
        (ResponseAct.COUNTERASSERT, Relation.CONTRADICTS),
        (ResponseAct.COUNTERASSERT, Relation.ENTAILS),
        (ResponseAct.COUNTERASSERT, Relation.NARROWS_WITHIN_SCOPE),
    ],
)
def test_single_layer_is_fully_responsive_when_a_move_addresses_it(
    act: ResponseAct,
    relation: Relation,
) -> None:
    case = make_case(
        layers=(ClaimLayer("p", "The proposition."),),
        moves=(ResponseMove("r", "A response.", act, "p", relation),),
    )

    report = score_case(case)

    assert report.verdict is Verdict.FULLY_RESPONSIVE
    assert report.covered_layer_ids == ("p",)
    assert report.uncovered_layer_ids == ()
    assert report.errors == ()


def test_irrelevant_counterassertion_is_nonresponsive() -> None:
    case = make_case(
        layers=(ClaimLayer("p", "The proposition."),),
        moves=(
            ResponseMove(
                "r",
                "A different proposition.",
                ResponseAct.COUNTERASSERT,
                "p",
                Relation.IRRELEVANT,
            ),
        ),
    )

    report = score_case(case)

    assert report.verdict is Verdict.NONRESPONSIVE
    assert report.covered_layer_ids == ()
    assert report.uncovered_layer_ids == ("p",)


def test_deflection_is_nonresponsive_even_when_it_names_the_target() -> None:
    case = make_case(
        layers=(ClaimLayer("p", "The proposition."),),
        moves=(ResponseMove("r", "A deflection.", ResponseAct.DEFLECT, "p"),),
    )

    assert score_case(case).verdict is Verdict.NONRESPONSIVE


def test_bilayer_claim_is_partial_when_only_surface_layer_is_addressed() -> None:
    case = make_case(
        layers=(
            ClaimLayer("surface", "The audit found no tabulation discrepancy."),
            ClaimLayer(
                "implicature",
                "Therefore all broader concerns are baseless.",
                layer_kind=LayerKind.IMPLICATED,
            ),
        ),
        moves=(
            ResponseMove(
                "r",
                "I accept the audit result.",
                ResponseAct.ADMIT,
                "surface",
                Relation.SAME,
            ),
        ),
    )

    report = score_case(case)

    assert report.verdict is Verdict.PARTIALLY_RESPONSIVE
    assert report.covered_layer_ids == ("surface",)
    assert report.uncovered_layer_ids == ("implicature",)


def test_bilayer_claim_is_full_when_each_required_layer_is_addressed() -> None:
    case = make_case(
        layers=(
            ClaimLayer("surface", "The audit found no tabulation discrepancy."),
            ClaimLayer(
                "implicature",
                "Therefore all broader concerns are baseless.",
                layer_kind=LayerKind.IMPLICATED,
            ),
        ),
        moves=(
            ResponseMove("r1", "I accept the audit result.", ResponseAct.ADMIT, "surface", Relation.SAME),
            ResponseMove(
                "r2",
                "I deny the broader inference.",
                ResponseAct.DENY,
                "implicature",
                Relation.CONTRADICTS,
            ),
        ),
    )

    assert score_case(case).verdict is Verdict.FULLY_RESPONSIVE


def test_optional_layer_does_not_reduce_responsiveness() -> None:
    case = make_case(
        layers=(
            ClaimLayer("required", "Required."),
            ClaimLayer("optional", "Context.", required=False),
        ),
        moves=(ResponseMove("r", "Denied.", ResponseAct.DENY, "required", Relation.CONTRADICTS),),
    )

    report = score_case(case)

    assert report.verdict is Verdict.FULLY_RESPONSIVE
    assert report.uncovered_layer_ids == ()


def test_unknown_target_makes_case_invalid() -> None:
    case = make_case(
        layers=(ClaimLayer("p", "The proposition."),),
        moves=(ResponseMove("r", "Denied.", ResponseAct.DENY, "missing", Relation.CONTRADICTS),),
    )

    report = score_case(case)

    assert report.verdict is Verdict.INVALID
    assert report.errors == ("response move 'r' targets unknown layer 'missing'",)


def test_duplicate_layer_ids_make_case_invalid() -> None:
    case = make_case(
        layers=(ClaimLayer("p", "One."), ClaimLayer("p", "Two.")),
        moves=(),
    )

    report = score_case(case)

    assert report.verdict is Verdict.INVALID
    assert report.errors == ("duplicate claim layer id 'p'",)


def test_case_without_required_layers_is_invalid() -> None:
    case = make_case(
        layers=(ClaimLayer("context", "Context.", required=False),),
        moves=(),
    )

    report = score_case(case)

    assert report.verdict is Verdict.INVALID
    assert report.errors == ("case has no required claim layers",)


@pytest.mark.parametrize(
    ("act", "relation"),
    [
        (ResponseAct.ADMIT, Relation.IRRELEVANT),
        (ResponseAct.DENY, Relation.IRRELEVANT),
        (ResponseAct.QUALIFY, Relation.SCOPE_MISMATCH),
        (ResponseAct.REQUEST_EVIDENCE, Relation.IRRELEVANT),
    ],
)
def test_targeted_direct_act_does_not_cover_without_a_covering_relation(
    act: ResponseAct, relation: Relation
) -> None:
    case = make_case(
        layers=(ClaimLayer("p", "The proposition."),),
        moves=(ResponseMove("r", "Aimed elsewhere in substance.", act, "p", relation),),
    )

    report = score_case(case)

    assert report.verdict is Verdict.NONRESPONSIVE
    assert report.covered_layer_ids == ()
    assert report.uncovered_layer_ids == ("p",)


def test_request_evidence_covers_only_an_unbacked_layer() -> None:
    move = ResponseMove(
        "r",
        "What supports that?",
        ResponseAct.REQUEST_EVIDENCE,
        "p",
        Relation.SAME,
    )
    unbacked = make_case(
        layers=(ClaimLayer("p", "A bare assertion.", backed=False),),
        moves=(move,),
        case_id="unbacked",
    )
    backed = make_case(
        layers=(ClaimLayer("p", "An assertion with cited support.", backed=True),),
        moves=(move,),
        case_id="backed",
    )

    assert score_case(unbacked).verdict is Verdict.FULLY_RESPONSIVE
    assert score_case(backed).verdict is Verdict.NONRESPONSIVE


def test_counterassertion_that_merely_restates_target_is_nonresponsive() -> None:
    case = make_case(
        layers=(ClaimLayer("p", "The proposition."),),
        moves=(
            ResponseMove(
                "r",
                "The proposition.",
                ResponseAct.COUNTERASSERT,
                "p",
                Relation.SAME,
            ),
        ),
    )

    assert score_case(case).verdict is Verdict.NONRESPONSIVE
