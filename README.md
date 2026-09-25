# `conda-pypi` Repodata Patching (Removals)

This repository ships a declarative list of packages to remove from the
`conda-pypi` channel index, plus a small loader/validator library. repo-core
imports the loader, resolves each block `name` against its shard index, and
applies the removals at index-write time. Other patch types may come later.

## How it works

The `conda-pypi` channel serves **sharded repodata only**: the index is
`repodata_shards.msgpack.zst` (a `name -> shard hash` map) plus per-name
`shards/<hash>.msgpack.zst` blobs holding `v3.whl` records. There is no
monolithic `repodata.json` to hotfix, so unlike the [CEP draft](https://github.com/conda/ceps/pull/88), patching
happens server-side in repo-core against the shard index.

Data flow:

```
blocks/*.yaml  ->  load_blocks()  ->  repo-core, per block name, per subdir:
                   look up shards[name] in the shard index
                   -> if present, omit the entry from the written shard index
                   -> if absent, log a no-op and continue (never fail)
```

Semantics:

- **Soft-remove.** Only the shard-index entry is dropped. The shard blob and
  wheel files stay on the channel, fetchable by direct URL. This mirrors
  CEP 88 `remove` semantics.
- **Sticky-forward.** Blocks are re-resolved every index cycle, so new
  uploads of a blocked name are hidden automatically with no new PR.
- **Unblocking.** Delete the block's YAML file; the entry is restored on the
  next cycle.
- **No-op names.** A blocked name absent from the index is a logged no-op,
  never an error.
- **Name-keyed only.** All patch resolution is O(1) name lookups against
  shard-index keys; repo-core never scans all shards.

### Schema versioning

The package exports `SCHEMA_VERSION` (currently `1`):

```python
from conda_pypi_repodata_patches import SCHEMA_VERSION
```

repo-core must check `SCHEMA_VERSION == 1` before calling `load_blocks()`
and refuse unknown versions, so an incompatible package fails cleanly at
startup. It will be bumped when new rule types land.

### Future work (not implemented)

Field-level patching will adopt the conda-forge/CEP 88 `if`/`then` rule
vocabulary with a **mandatory name condition**. Name-less channel-wide
conditions are unsupported: systemic metadata errors are fixed in the
wheel-to-conda conversion pipeline instead.

## Submitting a block

Block a package only for one of these reasons (validated by the loader):

- `mis-tagged-pure-python`: the PyPI wheel is tagged `py3-none-any` but
  contains native code, so it cannot live in the noarch channel.
- `name-conflict`: the PyPI package name shadows an existing conda-forge
  package.
- `maintainer-prefers-feedstock`: the conda-forge maintainer prefers users
  install from the feedstock rather than the converted wheel. Include an
  `issue` link where possible.

Steps:

1. Add `conda_pypi_repodata_patches/blocks/<name>.yaml`:

   ```yaml
   name: <exact conda package name>
   reason: mis-tagged-pure-python   # or: name-conflict, maintainer-prefers-feedstock
   details: |                        # optional, free-text evidence
     Why this package should be blocked.
   issue: <optional URL>             # optional tracking link
   ```

   `name` must be the exact package name (no globs).

2. Preview what your block would remove with `pixi run show-diff` (see
   below), and validate locally:

   ```sh
   python -c "from conda_pypi_repodata_patches.loader import load_blocks; load_blocks()"
   ```

    `load_blocks()` raises `ValueError` (naming the offending file) on any
    invalid block. The build test in `recipe/meta.yaml` also asserts the
    loader returns exactly the seeded block set.

3. Open a PR describing why the package should be blocked, with evidence.
   Paste the contents of `show_diff_result.txt` into the PR description.

The loader API, for consumers:

```python
SCHEMA_VERSION = 1             # checked by repo-core before consuming blocks
load_blocks() -> list[Block]   # each Block has .name .reason .details .issue
blocked_names() -> set[str]    # convenience: {b.name for b in load_blocks()}
```

## Previewing removals

`show_diff.py` (dev-only, not shipped) shows exactly what the current blocks
would remove: a per-name summary plus a unified diff of the affected shard
records. Its dependencies are provided by the pixi dev environment.

 1. From the repository root (so the package is importable), run:

    ```sh
    pixi run show-diff
    ```

   This writes `show_diff_result.txt` in the current directory and prints
   the same text to stdout. A blocked name already absent from the shard
   index is reported as `no-op`.

2. To skip re-downloading the ~25 MB shard index on every run, use:

    ```sh
    pixi run show-diff --use-cache
    ```

   Downloads are written to `cache/` (override with the `CACHE_DIR`
   environment variable); `--use-cache` reads from it without touching the
   network. `--channel` and `--subdir` default to the `conda-pypi` channel's
   `noarch` subdir.

## Development environment

The repo uses [pixi](https://pixi.sh) for its dev environment (manifest in
`pyproject.toml`). The default environment provides Python 3.14, `msgpack`,
and an editable install of this package.

```sh
pixi install          # create all environments and write pixi.lock
pixi run validate     # check SCHEMA_VERSION and the seeded block set
pixi run show-diff    # preview removals (add --use-cache to skip downloads)
```

## License

BSD-3-Clause.
