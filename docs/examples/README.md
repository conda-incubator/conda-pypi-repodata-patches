# Patch and block examples

Each directory under `docs/examples/` holds one input YAML file and the
`delta_patch_instructions.json` that the generator writes for it. The examples
run against a captured snapshot of the conda-pypi `noarch` channel, stored in
`tests/fixtures/conda_pypi_shards.json`. `tests/test_examples.py` rebuilds every
output offline and compares it with the committed JSON.

The block examples are illustrative and are not shipped. The package still
ships only `lerc` and `tk` under `conda_pypi_repodata_patches/blocks/`.

## Index

The table below is generated from the example directories. Each summary is the
first line of the example's input file, so change that line to change the text.

<!-- examples-index:start -->
| Example | Input | Output | Summary |
| --- | --- | --- | --- |
| `block-maintainer-prefers-feedstock` | [maintainer-prefers-feedstock.yaml](block-maintainer-prefers-feedstock/blocks/maintainer-prefers-feedstock.yaml) | [delta_patch_instructions.json](block-maintainer-prefers-feedstock/delta_patch_instructions.json) | Lists the `noja-reader` artifact under `remove`. |
| `block-mis-tagged-pure-python` | [mis-tagged-pure-python.yaml](block-mis-tagged-pure-python/blocks/mis-tagged-pure-python.yaml) | [delta_patch_instructions.json](block-mis-tagged-pure-python/delta_patch_instructions.json) | Lists the `container-env` artifact under `remove`. |
| `block-name-conflict` | [name-conflict.yaml](block-name-conflict/blocks/name-conflict.yaml) | [delta_patch_instructions.json](block-name-conflict/delta_patch_instructions.json) | Lists all 19 `six` artifacts under `remove`. |
| `condition-extra-scope` | [extra-scope.yaml](condition-extra-scope/patches/extra-scope.yaml) | [delta_patch_instructions.json](condition-extra-scope/delta_patch_instructions.json) | Adds a dependency to `extra_depends.dev` and leaves `depends` unchanged. |
| `condition-has-depends` | [has-depends.yaml](condition-has-depends/patches/has-depends.yaml) | [delta_patch_instructions.json](condition-has-depends/delta_patch_instructions.json) | Applies because `html2text` is present, then appends a dependency. |
| `condition-not-negation` | [not-negation.yaml](condition-not-negation/patches/not-negation.yaml) | [delta_patch_instructions.json](condition-not-negation/delta_patch_instructions.json) | Skips `gematriapy` 0.2.0 and patches 0.1.0 and 0.3.0. |
| `condition-when-marker` | [when-marker.yaml](condition-when-marker/patches/when-marker.yaml) | [delta_patch_instructions.json](condition-when-marker/delta_patch_instructions.json) | Removes `tomli` while its marker is attached. |
| `patch-add-constrains` | [add-constrains.yaml](patch-add-constrains/patches/add-constrains.yaml) | [delta_patch_instructions.json](patch-add-constrains/delta_patch_instructions.json) | Creates `constrains` with `setuptools>=68`. |
| `patch-add-depends` | [add-depends.yaml](patch-add-depends/patches/add-depends.yaml) | [delta_patch_instructions.json](patch-add-depends/delta_patch_instructions.json) | Appends `typing-extensions>=4` to `depends`. |
| `patch-add-track-features` | [add-track-features.yaml](patch-add-track-features/patches/add-track-features.yaml) | [delta_patch_instructions.json](patch-add-track-features/delta_patch_instructions.json) | Creates `track_features` with one feature. |
| `patch-loosen-depends` | [loosen-depends.yaml](patch-loosen-depends/patches/loosen-depends.yaml) | [delta_patch_instructions.json](patch-loosen-depends/delta_patch_instructions.json) | Resets to `foo >=1.0,<2.0a0`, then removes the upper bound. |
| `patch-relax-exact-depends` | [relax-exact-depends.yaml](patch-relax-exact-depends/patches/relax-exact-depends.yaml) | [delta_patch_instructions.json](patch-relax-exact-depends/delta_patch_instructions.json) | Resets to `foo 1.2.3 0`, then relaxes the exact pin with `max_pin: x`. |
| `patch-remove-constrains` | [remove-constrains.yaml](patch-remove-constrains/patches/remove-constrains.yaml) | [delta_patch_instructions.json](patch-remove-constrains/delta_patch_instructions.json) | Adds two constraints, then removes one. |
| `patch-remove-depends` | [remove-depends.yaml](patch-remove-depends/patches/remove-depends.yaml) | [delta_patch_instructions.json](patch-remove-depends/delta_patch_instructions.json) | Removes `html2text` and keeps the other dependencies. |
| `patch-remove-track-features` | [remove-track-features.yaml](patch-remove-track-features/patches/remove-track-features.yaml) | [delta_patch_instructions.json](patch-remove-track-features/delta_patch_instructions.json) | Adds one feature, then removes it and writes `null`. |
| `patch-rename-constrains` | [rename-constrains.yaml](patch-rename-constrains/patches/rename-constrains.yaml) | [delta_patch_instructions.json](patch-rename-constrains/delta_patch_instructions.json) | Adds a constraint, then renames it. |
| `patch-rename-depends` | [rename-depends.yaml](patch-rename-depends/patches/rename-depends.yaml) | [delta_patch_instructions.json](patch-rename-depends/delta_patch_instructions.json) | Renames `python` to `python3`. |
| `patch-replace-constrains` | [replace-constrains.yaml](patch-replace-constrains/patches/replace-constrains.yaml) | [delta_patch_instructions.json](patch-replace-constrains/delta_patch_instructions.json) | Adds a constraint, then replaces it. |
| `patch-replace-depends` | [replace-depends.yaml](patch-replace-depends/patches/replace-depends.yaml) | [delta_patch_instructions.json](patch-replace-depends/delta_patch_instructions.json) | Replaces `html2text` with `html2text>=2025.1` in place. |
| `patch-reset-constrains` | [reset-constrains.yaml](patch-reset-constrains/patches/reset-constrains.yaml) | [delta_patch_instructions.json](patch-reset-constrains/delta_patch_instructions.json) | Creates the `constrains` list. |
| `patch-reset-depends` | [reset-depends.yaml](patch-reset-depends/patches/reset-depends.yaml) | [delta_patch_instructions.json](patch-reset-depends/delta_patch_instructions.json) | Replaces the dependency list with two entries. |
| `patch-tighten-depends` | [tighten-depends.yaml](patch-tighten-depends/patches/tighten-depends.yaml) | [delta_patch_instructions.json](patch-tighten-depends/delta_patch_instructions.json) | Adds an upper bound to the bare `html2text` dependency. |
<!-- examples-index:end -->

## Coverage

`tests/test_examples.py` fails when a block reason in `REASONS` or a `then`
operation in `_ThenClauseItem` has no example, so a new operation needs an
example directory before the tests pass. Conditions are not enumerated in one
place, so the condition examples are not checked this way.

## Snapshot

`captured_at` is `2026-10-27T14:17:04+00:00` and `captured_from` is
`https://conda.anaconda.org/conda-pypi/noarch`. The fixture keeps the index
entry and `v3.whl` records for `container-env`, `gematriapy`, `noja-reader`,
`six`, and `usagestats`.

The captured records have `depends`, `extra_depends`, `timestamp`, and the
usual wheel metadata. None of them has `constrains`, `track_features`, or
`indexed_timestamp`. The constraint and track-feature examples create the field
first so the operation has something to change. Wheel dependencies use
single-token PEP 440 specs such as `python>=3.8,<4.0`. The
`relax_exact_depends` and `loosen_depends` examples reset the dependency list to
a conda-style spec first, because those operations only recognize space
separated conda specs.

## Regenerating the outputs

`pixi run test` checks every example. To rewrite the JSON and the index after
changing an input, set `UPDATE_EXAMPLES` and run the tests again:

```powershell
$env:UPDATE_EXAMPLES = "1"
pixi run test
Remove-Item Env:\UPDATE_EXAMPLES
```

The test still fails when a patch logs a no-op or produces empty output, so a
broken example cannot pass by writing an empty file.
