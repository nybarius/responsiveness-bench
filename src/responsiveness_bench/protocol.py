from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from importlib.resources import files
from pathlib import Path
from typing import Any

ANNOTATION_GUIDE_VERSION = "2.0.0"
KERNEL_VERSION = "2.0.0"
PROMPT_VERSION = "1.0.0"


class PromptArm(StrEnum):
    ZERO_SHOT = "zero_shot"
    FEW_SHOT = "few_shot"
    TYPED_INPUT = "typed_input"
    VERDICT_ONLY = "verdict_only"


@dataclass(frozen=True, slots=True)
class RunManifest:
    protocol_hash: str
    dataset_hash: str
    model_id: str
    prompt_hash: str
    prompt_arm: str


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _asset_text(name: str) -> str:
    return (
        files("responsiveness_bench")
        .joinpath("protocol_assets", name)
        .read_text(encoding="utf-8")
    )


def prompt_text(arm: PromptArm | str) -> str:
    selected = PromptArm(arm)
    if selected is PromptArm.ZERO_SHOT:
        return _asset_text("inference-zero-shot-v1.txt")
    if selected is PromptArm.FEW_SHOT:
        return _asset_text("inference-few-shot-v1.txt")
    if selected is PromptArm.TYPED_INPUT:
        return "typed-input-v1"
    return "verdict-only-v1"


def prompt_hash(arm: PromptArm | str) -> str:
    return _sha256_bytes(prompt_text(arm).encode("utf-8"))


def inference_schema() -> dict[str, Any]:
    return json.loads(_asset_text("inference-output.schema.json"))


def protocol_hash() -> str:
    descriptor = json.dumps(
        {
            "annotation_guide_version": ANNOTATION_GUIDE_VERSION,
            "kernel_version": KERNEL_VERSION,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return _sha256_bytes(descriptor.encode("utf-8"))


def dataset_hash(path: str | Path) -> str:
    source = Path(path)
    if source.is_dir():
        payload = b"".join(
            relative.as_posix().encode("utf-8") + b"\0" + file.read_bytes()
            for file in sorted(source.glob("*.jsonl"))
            for relative in (file.relative_to(source),)
        )
        return _sha256_bytes(payload)
    return _sha256_bytes(source.read_bytes())


def build_manifest(
    dataset: str | Path,
    *,
    model_id: str,
    prompt_arm: PromptArm | str,
) -> RunManifest:
    selected = PromptArm(prompt_arm)
    return RunManifest(
        protocol_hash=protocol_hash(),
        dataset_hash=dataset_hash(dataset),
        model_id=model_id,
        prompt_hash=prompt_hash(selected),
        prompt_arm=selected.value,
    )
