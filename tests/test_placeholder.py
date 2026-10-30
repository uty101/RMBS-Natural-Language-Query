"""Session 0 placeholder: the package skeleton imports and the suite collects."""

import importlib

import pytest

MODULES = [
    "rmbsq",
    "rmbsq.synth",
    "rmbsq.canonical",
    "rmbsq.semantic",
    "rmbsq.llm",
    "rmbsq.eval",
    "rmbsq.deliverable",
]


@pytest.mark.parametrize("name", MODULES)
def test_skeleton_imports(name):
    assert importlib.import_module(name).__doc__
