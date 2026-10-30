"""Template rendering for the README and the design response (instruction 06 B). Step 6.0.

- `{{#eval}}...{{/eval}}` is kept only in the recorded state and `{{^eval}}...{{/eval}}`
  only in the pending state. The markers and the 1 newline after each are removed.
  Sections don't nest.
- `{{name}}` is a block's rendered text when `name` is in `blocks`, otherwise a claim's
  display string. An unknown name raises.

Sections are resolved first, so a name inside a dropped section is never looked up.
"""

from __future__ import annotations

import re

SECTION = re.compile(r"\{\{([#^])(\w+)\}\}\n?(.*?)\{\{/\2\}\}\n?", re.DOTALL)
NAME = re.compile(r"\{\{(\w+)\}\}")
SECTIONS = {"eval"}


def resolve_sections(template_text: str, eval_recorded: bool) -> str:
    def keep(m: re.Match) -> str:
        kind, name, body = m.groups()
        if name not in SECTIONS:
            raise KeyError(f"unknown section {name}")
        return body if (kind == "#") == eval_recorded else ""

    text = SECTION.sub(keep, template_text)
    stray = re.search(r"\{\{[#^/]\w*\}\}", text)
    if stray:
        raise ValueError(f"unbalanced or nested section marker {stray.group(0)}")
    return text


def names_used(template_text: str, eval_recorded: bool) -> list[str]:
    """The `{{name}}` placeholders left once the sections are resolved, in first-use order."""
    return list(dict.fromkeys(NAME.findall(resolve_sections(template_text, eval_recorded))))


def render(template_text: str, claims: dict, blocks: dict, eval_recorded: bool) -> str:
    def fill(m: re.Match) -> str:
        name = m.group(1)
        if name in blocks:
            return blocks[name]
        if name in claims:
            return str(claims[name])
        raise KeyError(f"unknown placeholder {name}")

    return NAME.sub(fill, resolve_sections(template_text, eval_recorded))
