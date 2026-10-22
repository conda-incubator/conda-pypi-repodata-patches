# `conda-pypi` repodata patches

This repository holds the block and patch definitions for the `conda-pypi`
channel and the generator that compiles them into a conda-forge-shaped
`patch_instructions.json`.

## How it works

The `conda-pypi` channel serves sharded repodata only. The index is
`repodata_shards.msgpack.zst`, a `name -> shard hash` map, plus per-name
`shards/<hash>.msgpack.zst` blobs that hold the `v3.whl` records. There is no
monolithic `repodata.json` to hotfix. The generator compiles the patch
instructions from the shard index. The channel applies that file.

```
blocks/*.yaml + patches/*.yaml  ->  generator  ->  patch_instructions.json  ->  channel
```

The generator looks up only the shard names a block or patch refers to,
expands blocked names to artifact filenames, and writes the instruction file.
The generator logs a missing name as a no-op and never fails the run.

A block lists the artifact filenames under `remove`. The shard blobs and
wheel files stay on the channel, and users can still fetch them by direct
URL. [CEP 88](https://github.com/conda/ceps/pull/88) calls this `remove`. The
generator resolves blocks and patches again on every run, so the channel
hides a new upload of a blocked name without a new PR. Delete a block's YAML
file and regenerate to restore the entry. Patch resolution is a name lookup
against shard-index keys, so the generator never scans every shard.

### Artifact contract

`patch_instructions.json` has `patch_instructions_version: 1`. A consumer
that does not understand the version or the `v3` section should reject the
file. Do not apply the parts it understands.

### Name-scoped patching

Field-level patches use the conda-forge/CEP 88 `if`/`then` vocabulary. Every
patch needs a name condition. The generator rejects channel-wide conditions.
Fix systemic metadata errors in the wheel-to-conda conversion pipeline.

## Submitting a block

Use a block only for one of these reasons:

- `mis-tagged-pure-python`: the PyPI wheel is tagged `py3-none-any` but
  contains native code, so it cannot live in the noarch channel.
- `name-conflict`: the PyPI package name shadows an existing conda-forge
  package.
- `maintainer-prefers-feedstock`: the conda-forge maintainer prefers users
  install from the feedstock rather than the converted wheel. Include an
  `issue` link where possible.

To add a block:

1. Add `conda_pypi_repodata_patches/blocks/<name>.yaml`:

   ```yaml
   name: <exact conda package name>
   reason: mis-tagged-pure-python   # or: name-conflict, maintainer-prefers-feedstock
   details: |                        # optional, free-text evidence
     Why this package should be blocked.
   issue: <optional URL>             # optional tracking link
   ```

   `name` must be the exact package name, with no globs.

2. Preview the removals with `pixi run show-diff` (see below) and validate
   locally with `pixi run validate`. Validation raises `ValueError` naming
   the offending file when a block or patch is invalid. The build test in
   `recipe/meta.yaml` also asserts that the seeded block set is exactly
   `{lerc, tk}`.

3. Open a PR with evidence for the block and paste `show_diff_result.txt`
   into the PR description.

## Previewing removals

`show_diff.py` (dev-only, not shipped) shows what the current blocks would
remove: a per-name summary and a unified diff of the affected shard records.

1. From the repository root, run:

   ```sh
   pixi run show-diff
   ```

   This writes `show_diff_result.txt` in the current directory and prints the
   same text to stdout. The script reports a blocked name that is already
   absent from the shard index as `no-op`.

2. To skip downloading the ~25 MB shard index, use:

   ```sh
   pixi run show-diff --use-cache
   ```

   Downloads go to `cache/`, which `CACHE_DIR` can override. With
   `--use-cache` the script reads that directory without touching the
   network. `--channel` and `--subdir` default to the `conda-pypi` channel's
   `noarch` subdir.

## Patch definitions

Field-level patches live in `conda_pypi_repodata_patches/patches/*.yaml` and
use the conda-forge `if`/`then` vocabulary. Every patch needs a literal
package name and a future-record guard:

```yaml
if:
  name: six
  timestamp_lt: 1760000000
  not_version: 1.12.0
then:
  - add_depends: setuptools
```

- `if.name` must match `^[a-z0-9_.-]+$`; the generator rejects globs and
  `name_in`.
- `if` must include `timestamp_lt` (or `indexed_timestamp_lt` when the index
  provides that field). Live `v3.whl` shard records carry `timestamp` but not
  `indexed_timestamp`, so `timestamp_lt` is the guard to use today.
- `if.extra` scopes a patch to one `extra_depends` entry. The generator
  normalizes extra names per PEP 685. Extra-scoped patches may only use
  `add_depends`, `remove_depends`, `replace_depends`, `reset_depends`,
  `rename_depends`, `relax_exact_depends`, `tighten_depends`, or
  `loosen_depends`.
- Dependency strings may end in `[when="..."]`. The generator splits the
  marker off, applies the operation to the bare spec, and reattaches it.

If a name is both blocked and patched, the block takes precedence.

## Generating `patch_instructions.json`

```sh
pixi run generate                  # fresh download of the shard index
pixi run generate --use-cache      # reuse cache/ from a previous run
```

The generator reads `repodata_shards.msgpack.zst`, fetches the shards that
the blocks and patches refer to, and writes `patch_instructions.json` in the
repository root:

```json
{
  "patch_instructions_version": 1,
  "packages": {},
  "packages.conda": {},
  "remove": ["lerc-2.0.0-py3-none-any.whl"],
  "revoke": [],
  "v3": {
    "whl": {
      "six-1.12.0-py2.py3_none_any_0": {
        "depends": ["python", "setuptools"]
      }
    }
  }
}
```

`remove` lists the blocked artifact filenames; users can still download them
by direct URL. `v3.whl` holds the changed keys for each patched record, keyed
by the record name without its extension. The generator expands blocked names
from their shard records and writes no `v3.whl` entry for them. It logs
missing names as no-ops and writes the file only after every required shard
fetch succeeds.

## Development environment

The repo uses [pixi](https://pixi.sh) for its dev environment, with the
manifest in `pyproject.toml`. The default environment provides Python 3.14,
`msgpack`, and an editable install of this package.

```sh
pixi install          # create all environments and write pixi.lock
pixi run validate     # check the seeded blocks and patch definitions
pixi run test         # run the unit tests
pixi run show-diff    # preview removals (add --use-cache to skip downloads)
pixi run generate     # write patch_instructions.json
```

## License

BSD-3-Clause.
