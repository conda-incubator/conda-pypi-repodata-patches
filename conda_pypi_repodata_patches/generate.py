"""Generate ``patch_instructions.json`` from blocks and patch definitions."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

from . import patch_yaml_utils as engine
from .blocks import Block, load_blocks
from .patches import Patch, load_patches
from .shards import (
    DEFAULT_CHANNEL,
    load_shard,
    load_shard_index,
    shard_hash,
)

OUTPUT = Path("patch_instructions.json")


def build_instructions(
    blocks: list[Block],
    patches: list[Patch],
    shard_index: dict,
    get_shard,
    subdir: str = "noarch",
    log=print,
) -> dict:
    """Build the patch instructions from an index and a shard fetch callback."""
    instructions = {
        "patch_instructions_version": 1,
        "packages": {},
        "packages.conda": {},
        "revoke": [],
        "remove": [],
        "v3": {"whl": {}},
    }

    names = {block.name for block in blocks}
    names.update(patch.document["if"]["name"] for patch in patches)

    records_by_name: dict[str, dict] = {}
    for name in sorted(names):
        hex_hash = shard_hash(shard_index, name)
        if hex_hash is None:
            log(f"no-op: {name} not in shard index")
            continue
        shard = get_shard(hex_hash)
        records_by_name[name] = shard.get("v3", {}).get("whl", {})

    blocked = {block.name for block in blocks}
    for name in blocked:
        for record in records_by_name.get(name, {}).values():
            instructions["remove"].append(record["fn"])
    instructions["remove"] = sorted(set(instructions["remove"]))

    patches_by_name: dict[str, list[Patch]] = {}
    for patch in patches:
        patches_by_name.setdefault(patch.document["if"]["name"], []).append(patch)

    for name, records in records_by_name.items():
        if name in blocked:
            continue
        matched: set[str] = set()
        for key, record in records.items():
            working = copy.deepcopy(record)
            for patch in patches_by_name.get(name, []):
                if _apply_patch(
                    patch, working, subdir, record.get("fn", key)
                ):
                    matched.add(patch.source)
            changed = {
                field: value
                for field, value in working.items()
                if field not in record or record[field] != value
            }
            if changed:
                instructions["v3"]["whl"][key] = changed
        for patch in patches_by_name.get(name, []):
            if patch.source not in matched:
                log(f"no-op: {patch.source} matched no records for {name}")

    return instructions


def _apply_patch(patch: Patch, record: dict, subdir: str, fn: str) -> bool:
    if_clause = patch.document["if"]
    extra = if_clause.get("extra")
    if extra is None:
        document = patch.document
        if engine.test_patch_yaml(document, record, subdir, fn):
            engine.apply_patch_yaml(document, record, subdir, fn)
            return True
        return False

    document = {
        "if": {key: value for key, value in if_clause.items() if key != "extra"},
        "then": patch.document["then"],
    }
    extra_depends = record.get("extra_depends") or {}
    view = dict(record)
    view["depends"] = list(extra_depends.get(extra, []))
    if engine.test_patch_yaml(document, view, subdir, fn):
        engine.apply_patch_yaml(document, view, subdir, fn)
        if view["depends"] != extra_depends.get(extra, []):
            updated = dict(extra_depends)
            updated[extra] = view["depends"]
            record["extra_depends"] = updated
        return True
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", default=DEFAULT_CHANNEL)
    parser.add_argument("--subdir", default="noarch")
    parser.add_argument(
        "--use-cache",
        action="store_true",
        help="Reuse (and populate) $CACHE_DIR instead of always downloading.",
    )
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    shard_index = load_shard_index(args.channel, args.subdir, args.use_cache)
    instructions = build_instructions(
        load_blocks(),
        load_patches(),
        shard_index,
        lambda hex_hash: load_shard(
            hex_hash, args.channel, args.subdir, args.use_cache
        ),
        subdir=args.subdir,
        log=lambda message: print(message, file=sys.stderr),
    )
    args.output.write_text(
        json.dumps(instructions, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
