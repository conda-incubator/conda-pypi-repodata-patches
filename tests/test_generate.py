from __future__ import annotations

from conda_pypi_repodata_patches.blocks import Block
from conda_pypi_repodata_patches.generate import build_instructions
from conda_pypi_repodata_patches.patches import Patch

SHARDS = {
    "six": {
        "v3": {
            "whl": {
                "six-1.0-py3_none_any_0": {
                    "name": "six",
                    "fn": "six-1.0-py3-none-any.whl",
                    "version": "1.0",
                    "depends": ["python"],
                    "extra_depends": {"test": ["pytest"], "docs": ["sphinx"]},
                    "timestamp": 1000,
                }
            }
        }
    },
    "gone": {
        "v3": {
            "whl": {
                "gone-1.0-py3_none_any_0": {
                    "name": "gone",
                    "fn": "gone-1.0-py3-none-any.whl",
                    "version": "1.0",
                },
                "gone-2.0-py3_none_any_0": {
                    "name": "gone",
                    "fn": "gone-2.0-py3-none-any.whl",
                    "version": "2.0",
                },
            }
        }
    },
}
INDEX = {"shards": {"six": "six", "gone": "gone"}}
GET_SHARD = SHARDS.__getitem__


def block(name):
    return Block(name=name, reason="name-conflict")


def patch(name, then, **conditions):
    return Patch(
        document={
            "if": {"name": name, "timestamp_lt": 1760000000, **conditions},
            "then": then,
        },
        source=f"{name}.yaml",
    )


def test_removed_block_lists_every_artifact_filename():
    instructions = build_instructions([block("gone")], [], INDEX, GET_SHARD)

    assert instructions["remove"] == [
        "gone-1.0-py3-none-any.whl",
        "gone-2.0-py3-none-any.whl",
    ]
    assert instructions["v3"]["whl"] == {}


def test_patch_writes_only_changed_keys():
    instructions = build_instructions(
        [], [patch("six", [{"add_depends": "setuptools"}])], INDEX, GET_SHARD
    )

    assert instructions["v3"]["whl"] == {
        "six-1.0-py3_none_any_0": {"depends": ["python", "setuptools"]}
    }


def test_extra_scope_writes_extra_depends_map():
    instructions = build_instructions(
        [],
        [patch("six", [{"add_depends": "setuptools"}], extra="test")],
        INDEX,
        GET_SHARD,
    )

    assert instructions["v3"]["whl"] == {
        "six-1.0-py3_none_any_0": {
            "extra_depends": {"test": ["pytest", "setuptools"], "docs": ["sphinx"]}
        }
    }


def test_missing_name_is_logged():
    messages = []

    instructions = build_instructions(
        [block("absent")], [], INDEX, GET_SHARD, log=messages.append
    )

    assert instructions["remove"] == []
    assert messages == ["no-op: absent not in shard index"]


def test_patch_with_no_matching_records_is_logged():
    messages = []

    instructions = build_instructions(
        [],
        [patch("six", [{"add_depends": "setuptools"}], version="2.0")],
        INDEX,
        GET_SHARD,
        log=messages.append,
    )

    assert instructions["v3"]["whl"] == {}
    assert messages == ["no-op: six.yaml matched no records for six"]


def test_block_takes_precedence_over_patch():
    instructions = build_instructions(
        [block("six")],
        [patch("six", [{"add_depends": "setuptools"}])],
        INDEX,
        GET_SHARD,
    )

    assert instructions["remove"] == ["six-1.0-py3-none-any.whl"]
    assert instructions["v3"]["whl"] == {}
