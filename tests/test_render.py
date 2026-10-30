"""Step 6.0: template rendering (instruction 06 B, J 6.0)."""

import pytest

from rmbsq.deliverable.render import names_used, render

TEMPLATE = (
    "Top {{a}}.\n"
    "{{#eval}}\n"
    "Recorded {{k}} with\n"
    "{{table}}\n"
    "{{/eval}}\n"
    "{{^eval}}\n"
    "Pending {{b}}.\n"
    "{{/eval}}\n"
    "End.\n"
)


def test_render_sections():
    claims = {"a": "1", "b": "2", "k": "9"}
    blocks = {"table": "| x |"}

    # pending: the {{^eval}} body only, markers and their newline removed; k is never needed
    pending = render(TEMPLATE, {"a": "1", "b": "2"}, {}, eval_recorded=False)
    assert pending == "Top 1.\nPending 2.\nEnd.\n"

    recorded = render(TEMPLATE, claims, blocks, eval_recorded=True)
    assert recorded == "Top 1.\nRecorded 9 with\n| x |\nEnd.\n"

    # a marker with no newline after it is removed alone
    assert render("x{{#eval}}y{{/eval}}z", {}, {}, eval_recorded=True) == "xyz"
    assert render("x{{^eval}}y{{/eval}}z", {}, {}, eval_recorded=True) == "xz"

    assert names_used(TEMPLATE, eval_recorded=False) == ["a", "b"]
    assert names_used(TEMPLATE, eval_recorded=True) == ["a", "k", "table"]

    with pytest.raises(KeyError, match="nope"):
        render("{{nope}}", claims, blocks, eval_recorded=False)
    # a name inside a kept section must be known
    with pytest.raises(KeyError, match="k"):
        render(TEMPLATE, {"a": "1", "b": "2"}, blocks, eval_recorded=True)
    with pytest.raises(KeyError, match="other"):
        render("{{#other}}x{{/other}}", claims, blocks, eval_recorded=True)
