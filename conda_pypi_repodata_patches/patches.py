from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from .patch_yaml_model import PatchYaml

_NAME_RE = re.compile(r"^[a-z0-9_.-]+$")
_PEP685_RE = re.compile(r"[-_.]+")
_PATCHES_DIR = Path(__file__).parent / "patches"

_DEPENDS_OPERATIONS = {
    "add_depends",
    "remove_depends",
    "replace_depends",
    "reset_depends",
    "rename_depends",
    "relax_exact_depends",
    "tighten_depends",
    "loosen_depends",
}
_GUARD_KEYS = ("timestamp_lt", "indexed_timestamp_lt")


@dataclass(frozen=True)
class Patch:
    """A single patch document and the file it came from."""

    document: dict
    source: str


def normalize_extra(name: str) -> str:
    """Normalize an extra name per PEP 685."""
    return _PEP685_RE.sub("-", name).lower()


def load_patches(directory: Path | None = None) -> list[Patch]:
    """Load and validate every ``patches/*.yaml`` file.

    Raises ``ValueError`` naming the offending file on any invalid document.
    """
    directory = directory or _PATCHES_DIR
    patches: list[Patch] = []
    for path in sorted(directory.glob("*.yaml")):
        docs = list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
        for doc in docs:
            if doc is None:
                continue
            patches.append(_validate(doc, path))
    return patches


def _validate(doc, path: Path) -> Patch:
    if not isinstance(doc, dict):
        raise ValueError(f"{path.name}: patch must be a mapping")

    try:
        PatchYaml(**doc)
    except ValidationError as e:
        raise ValueError(f"{path.name}: invalid patch document: {e}") from e

    if_clause = doc["if"]
    name = if_clause.get("name")
    if not isinstance(name, str) or not _NAME_RE.match(name):
        raise ValueError(
            f"{path.name}: 'if.name' must be a literal package name "
            "matching ^[a-z0-9_.-]+$"
        )

    if not any(if_clause.get(key) is not None for key in _GUARD_KEYS):
        raise ValueError(
            f"{path.name}: 'if' must include one of {', '.join(_GUARD_KEYS)} "
            "to guard against future records"
        )

    document = copy.deepcopy(doc)
    if_clause = document["if"]

    extra = if_clause.get("extra")
    if extra is not None:
        normalized = normalize_extra(extra)
        if_clause["extra"] = normalized
        for instruction in document["then"]:
            for operation in instruction:
                if operation not in _DEPENDS_OPERATIONS:
                    raise ValueError(
                        f"{path.name}: extra-scoped patches may only use depends "
                        f"operations, got {operation!r}"
                    )

    return Patch(document=document, source=path.name)
