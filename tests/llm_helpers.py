"""Fixture cache entries for the LLM tests (instruction 04 I).

A fixture response is a full Messages API response dict in
`tests/fixtures/llm_responses/<name>.json`. `seed` builds the request exactly as the code
would, keys it with the client's key function and writes `{key, request, response,
latency_s}` into the client's (temp) cache dir. No test reads `data/llm_cache/`.
"""

import json
from pathlib import Path

from rmbsq.llm.client import request_key, write_entry

RESPONSES = Path(__file__).parent / "fixtures" / "llm_responses"


def response(name: str) -> dict:
    return json.loads((RESPONSES / f"{name}.json").read_text(encoding="utf-8"))


def seed(client, system: str, messages: list, tools: list, tool_choice, resp: dict | str,
         latency_s: float = 1.234) -> str:
    resp = response(resp) if isinstance(resp, str) else resp
    request = client.build_request(system, messages, tools, tool_choice)
    key = request_key(request)
    client.cache_dir.mkdir(parents=True, exist_ok=True)
    write_entry(client.cache_dir / f"{key}.json",
                {"key": key, "request": request, "response": resp, "latency_s": latency_s})
    return key
