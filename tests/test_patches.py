from __future__ import annotations

import pytest

from conda_pypi_repodata_patches.patches import load_patches, normalize_extra

VALID = """\
if:
  name: six
  timestamp_lt: 1760000000
then:
  - add_depends: setuptools
"""


def load_patch(tmp_path, content):
    (tmp_path / "patch.yaml").write_text(content, encoding="utf-8")
    return load_patches(tmp_path)


def test_valid_document(tmp_path):
    patches = load_patch(tmp_path, VALID)

    assert len(patches) == 1
    assert patches[0].document["if"]["name"] == "six"


@pytest.mark.parametrize(
    ("content", "match"),
    [
        (
            """\
if:
  timestamp_lt: 1760000000
then:
  - add_depends: setuptools
""",
            "if.name",
        ),
        (
            """\
if:
  name: six*
  timestamp_lt: 1760000000
then:
  - add_depends: setuptools
""",
            "literal package name",
        ),
        (
            """\
if:
  name: six
then:
  - add_depends: setuptools
""",
            "timestamp_lt",
        ),
        (
            """\
if:
  name: six
  timestamp_lt: 1760000000
  extra: My_Extra
then:
  - add_constrains: setuptools
""",
            "extra-scoped",
        ),
        (
            """\
if:
  name: six
  timestamp_lt: 1760000000
then:
  - invalid_operation: setuptools
""",
            "invalid patch document",
        ),
    ],
    ids=[
        "missing-name",
        "glob-name",
        "missing-guard",
        "extra-constrains",
        "unknown-op",
    ],
)
def test_invalid_patch_is_rejected(tmp_path, content, match):
    with pytest.raises(ValueError, match=match):
        load_patch(tmp_path, content)


def test_extra_is_normalized(tmp_path):
    patches = load_patch(
        tmp_path,
        """\
if:
  name: six
  timestamp_lt: 1760000000
  extra: My_Extra
then:
  - add_depends: setuptools
""",
    )

    assert patches[0].document["if"]["extra"] == "my-extra"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("My_Extra", "my-extra"),
        ("My_Extra.Name", "my-extra-name"),
        ("already-normalized", "already-normalized"),
    ],
)
def test_normalize_extra(raw, expected):
    assert normalize_extra(raw) == expected
