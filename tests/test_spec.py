"""Step 3.2: QuerySpec (kickoff 6.6; instruction 03 E 3.2), on the examples in
tests/fixtures/spec_examples.json."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from rmbsq.semantic.spec import QuerySpec

EXAMPLES = json.loads((Path(__file__).parent / "fixtures" / "spec_examples.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("ex", EXAMPLES["valid"], ids=lambda ex: ex["id"])
def test_valid_examples(ex):
    spec = QuerySpec.model_validate(ex["spec"])
    if "expect_time" in ex:
        assert spec.time.model_dump() == ex["expect_time"]


@pytest.mark.parametrize("ex", EXAMPLES["invalid"], ids=lambda ex: ex["id"])
def test_invalid_examples(ex):
    with pytest.raises(ValidationError):
        QuerySpec.model_validate(ex["spec"])
