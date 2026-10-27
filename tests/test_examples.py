from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from conda_pypi_repodata_patches.blocks import REASONS, load_blocks
from conda_pypi_repodata_patches.generate import build_instructions
from conda_pypi_repodata_patches.patch_yaml_model import _ThenClauseItem
from conda_pypi_repodata_patches.patches import _DEPENDS_OPERATIONS, load_patches

ROOT = Path(__file__).parents[1]
EXAMPLES = ROOT / "docs" / "examples"
INDEX_START = "<!-- examples-index:start -->"
INDEX_END = "<!-- examples-index:end -->"
FIXTURE = json.loads(
    (ROOT / "tests" / "fixtures" / "conda_pypi_shards.json").read_text(
        encoding="utf-8"
    )
)
INDEX = FIXTURE["index"]
SHARDS = FIXTURE["shards"]
GET_SHARD = SHARDS.__getitem__
EXAMPLE_DIRS = sorted(path for path in EXAMPLES.iterdir() if path.is_dir())
UPDATE = bool(os.environ.get("UPDATE_EXAMPLES"))


def example_input(example: Path) -> Path:
    return next(example.glob("*/*.yaml"))


def render_index() -> str:
    rows = [
        "| Example | Input | Output | Summary |",
        "| --- | --- | --- | --- |",
    ]
    for example in EXAMPLE_DIRS:
        source = example_input(example)
        summary = source.read_text(encoding="utf-8").splitlines()[0]
        assert summary.startswith("# "), f"{source}: first line must be a '# ' summary"
        output = example / "delta_patch_instructions.json"
        rows.append(
            f"| `{example.name}` "
            f"| [{source.name}]({source.relative_to(EXAMPLES).as_posix()}) "
            f"| [{output.name}]({output.relative_to(EXAMPLES).as_posix()}) "
            f"| {summary.removeprefix('# ')} |"
        )
    return "\n".join(rows)


@pytest.mark.parametrize(
    "example", EXAMPLE_DIRS, ids=[path.name for path in EXAMPLE_DIRS]
)
def test_example_matches_committed_output(example: Path) -> None:
    messages = []
    instructions = build_instructions(
        load_blocks(example / "blocks"),
        load_patches(example / "patches"),
        INDEX,
        GET_SHARD,
        log=messages.append,
    )

    assert not messages, f"{example}: generator logged a no-op: {messages}"
    assert instructions["remove"] or instructions["v3"]["whl"], (
        f"{example}: generated output is empty"
    )

    serialized = json.dumps(instructions, indent=2, sort_keys=True) + "\n"
    output = example / "delta_patch_instructions.json"
    if UPDATE:
        output.write_text(serialized, encoding="utf-8")
    else:
        assert output.read_text(encoding="utf-8") == serialized, (
            f"{example}: output drifted; rerun with UPDATE_EXAMPLES=1"
        )


def test_index_matches_examples() -> None:
    readme_path = EXAMPLES / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    start = readme.index(INDEX_START) + len(INDEX_START)
    end = readme.index(INDEX_END)
    expected = f"\n{render_index()}\n"
    if UPDATE:
        readme_path.write_text(
            readme[:start] + expected + readme[end:], encoding="utf-8"
        )
    else:
        assert readme[start:end] == expected, (
            "docs/examples/README.md index is stale; rerun with UPDATE_EXAMPLES=1"
        )


def test_every_block_reason_has_an_example() -> None:
    covered = {
        block.reason for example in EXAMPLE_DIRS for block in load_blocks(example / "blocks")
    }
    assert covered == REASONS


def test_every_patch_operation_has_an_example() -> None:
    covered = {
        operation
        for example in EXAMPLE_DIRS
        for patch in load_patches(example / "patches")
        for instruction in patch.document["then"]
        for operation in instruction
    }
    assert covered == set(_ThenClauseItem.model_fields)


def test_readme_names_every_reason_and_depends_operation() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    missing = sorted(name for name in REASONS | _DEPENDS_OPERATIONS if name not in readme)
    assert not missing, f"README.md does not mention: {missing}"
