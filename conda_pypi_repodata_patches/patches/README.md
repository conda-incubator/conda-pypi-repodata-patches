# Patch definitions

Each `*.yaml` file in this directory holds one or more patch documents. The
generator applies them to the matching `v3.whl` records and writes the changed
keys to `delta_patch_instructions.json`.

```yaml
if:
  name: six
  timestamp_lt: 1760000000
  not_version: 1.12.0
then:
  - add_depends: setuptools
```

Rules enforced by `load_patches()`:

- `if.name` is required and must be a literal package name; globs and
  `name_in` are rejected.
- `if` must include `timestamp_lt` (or `indexed_timestamp_lt` when the index
  provides that field) so the patch cannot reach future uploads.
- `if.extra` scopes the patch to one `extra_depends` entry. The name is
  normalized per PEP 685, and extra-scoped patches may only use the dependency
  operations: `add_depends`, `remove_depends`, `replace_depends`,
  `reset_depends`, `rename_depends`, `relax_exact_depends`,
  `tighten_depends`, and `loosen_depends`.
- Dependency strings may end in `[when="..."]`; the marker is preserved while
  the operation is applied to the bare spec.
