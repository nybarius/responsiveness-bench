from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_annotation_guide_leads_with_compatibility_test() -> None:
    guide = (ROOT / "docs" / "annotation-guide.md").read_text(encoding="utf-8")

    assert "## Compatibility test" in guide
    assert "Assume everything the response asserts is true" in guide
    assert "can the claim layer still be true" in guide
    assert guide.index("## Compatibility test") < guide.index("## Claim layers")
    assert "narrows_within_scope" in guide
    assert "scope_mismatch" in guide
    assert "backed" in guide
    assert "contested" in guide


def test_readme_publishes_measurement_and_exploit_audit() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert "Inference mode" in readme
    assert "Structure-flip rate" in readme
    assert "Content Effect" in readme
    assert "Directional Asymmetry" in readme
    assert "always_request_evidence" in readme
    assert "63.64%" in readme
    assert "33 cases" in readme
    assert "11" in readme


def test_ci_enforces_full_gate_and_exploit_audit() -> None:
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )

    assert "pytest" in workflow
    assert "compileall" in workflow
    assert "validate data/seed" in workflow
    assert "audit data/seed --check" in workflow


def test_release_version_is_protocol_v2() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")

    assert 'version = "0.2.0"' in pyproject
    assert "version: 0.2.0" in citation


def test_repository_contains_no_process_or_promotion_layer() -> None:
    forbidden_names = {"AGENTS.md", "HANDOFF.md", "substack-note.md"}
    assert not any(path.name in forbidden_names for path in ROOT.rglob("*"))

    forbidden_phrases = (
        "substack",
        "chatgpt",
        "human-ai collaboration",
        "ai-assisted",
        "publication draft",
    )
    text_suffixes = {".md", ".txt", ".toml", ".yml", ".yaml", ".py", ".json", ".cff"}
    for path in ROOT.rglob("*"):
        if (
            ".git" in path.parts
            or path == Path(__file__)
            or not path.is_file()
            or path.suffix not in text_suffixes
        ):
            continue
        lowered = path.read_text(encoding="utf-8").lower()
        assert not any(phrase in lowered for phrase in forbidden_phrases), path
