from __future__ import annotations

import pytest

from conda_pypi_repodata_patches import patch_yaml_utils as engine
from conda_pypi_repodata_patches.generate import _apply_patch
from conda_pypi_repodata_patches.patches import Patch

FN = "six-1.0-py3_none_any_0"


def patch_condition(**conditions):
    return {"name": "six", "timestamp_lt": 1760000000, **conditions}


def patch_document(then, **conditions):
    return {"if": patch_condition(**conditions), "then": then}


def apply_patch(document, record):
    engine.apply_patch_yaml(document, record, "noarch", FN)
    return record


@pytest.mark.parametrize(
    ("then", "depends", "expected"),
    [
        (
            [{"remove_depends": "foo"}],
            ['foo [when="extra"]', 'bar [when="x"]'],
            ['bar [when="x"]'],
        ),
        ([{"add_depends": "foo"}], ['foo [when="extra"]'], ['foo [when="extra"]']),
        (
            [{"tighten_depends": {"name": "foo", "max_pin": "x"}}],
            ['foo >=1.0 [when="extra"]'],
            ['foo >=1.0,<2.0a0 [when="extra"]'],
        ),
        (
            [{"replace_depends": {"old": "foo", "new": "bar"}}],
            ['foo [when="extra"]'],
            ['bar [when="extra"]'],
        ),
    ],
    ids=["remove", "add-existing", "tighten", "replace"],
)
def test_dependency_markers_are_preserved(then, depends, expected):
    record = apply_patch(patch_document(then), {"name": "six", "depends": depends})

    assert record["depends"] == expected


def test_has_depends_matches_bare_spec():
    document = patch_document([{"add_depends": "bar"}], has_depends="foo")
    record = {"name": "six", "depends": ['foo [when="extra"]']}

    assert engine.test_patch_yaml(document, record, "noarch", FN)


@pytest.mark.parametrize(
    ("indexed_timestamp", "expected"),
    [(200, False), (50, True)],
    ids=["future-record", "past-record"],
)
def test_indexed_timestamp_lt_compares_integers(indexed_timestamp, expected):
    document = patch_document(
        [{"add_depends": "setuptools"}],
        indexed_timestamp_lt="100",
    )
    record = {"name": "six", "indexed_timestamp": indexed_timestamp, "depends": []}

    assert engine.test_patch_yaml(document, record, "noarch", FN) is expected


def extra_patch(then, extra="my-extra"):
    return Patch(
        document=patch_document(then, extra=extra),
        source="six.yaml",
    )


def test_extra_scope_adds_only_to_named_extra():
    record = {
        "name": "six",
        "depends": ["python"],
        "extra_depends": {"other": ["pytest"], "my-extra": ["foo"]},
    }

    _apply_patch(extra_patch([{"add_depends": "setuptools"}]), record, "noarch", FN)

    assert record["extra_depends"] == {
        "other": ["pytest"],
        "my-extra": ["foo", "setuptools"],
    }
    assert record["depends"] == ["python"]


def test_extra_scope_removes_from_named_extra():
    record = {
        "name": "six",
        "depends": ["foo"],
        "extra_depends": {"my-extra": ['foo [when="my-extra"]']},
    }

    _apply_patch(extra_patch([{"remove_depends": "foo"}]), record, "noarch", FN)

    assert record["extra_depends"] == {"my-extra": []}
