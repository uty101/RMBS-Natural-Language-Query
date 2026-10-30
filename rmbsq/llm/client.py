"""Cached LLM client, replay and record modes (kickoff 6.8; instruction 04 C). Step 4.1.

The request is the dict of C.1 and its key the SHA-256 of its canonical JSON (C.2). Each
cache file `cache_dir/<key>.json` holds the key, the request, the response and the live
call's latency, with no timestamp, so re-recording an identical response gives an
identical file (C.3).

`replay` never touches the network or the SDK client; a miss raises `CacheMiss`.
`record` calls the API only on a miss, creating the `anthropic.Anthropic` client on the
first one. This is the only network code in the repo (CLAUDE.md rule 8).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path

import anthropic

RETRY_STATUS = {429, 529}   # and every 5xx (C.4)
RETRY_WAITS = (2, 4, 8)     # seconds before retries 1, 2 and 3 (C.4)


class CacheMiss(Exception):
    def __init__(self, key: str):
        super().__init__(key)
        self.key = key


class MissingApiKey(Exception):
    pass


def request_key(request: dict) -> str:
    """C.2: SHA-256 hex of the request's sorted, compact JSON in UTF-8."""
    text = json.dumps(request, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_entry(path: Path, entry: dict) -> None:
    """C.3: sorted keys, indent 1, UTF-8, trailing LF."""
    text = json.dumps(entry, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    Path(path).write_bytes(text.encode("utf-8"))


def _retryable(err: anthropic.APIStatusError) -> bool:
    return err.status_code in RETRY_STATUS or err.status_code >= 500


class LLMClient:
    def __init__(self, cfg, mode: str = "replay", cache_dir: Path = Path("data/llm_cache")):
        if mode not in ("replay", "record"):
            raise ValueError(f"mode must be replay or record, got {mode}")
        self.cfg = cfg
        self.mode = mode
        self.cache_dir = Path(cache_dir)
        self.calls: list[dict] = []
        self._sdk = None

    def build_request(self, system: str, messages: list, tools: list, tool_choice) -> dict:
        """C.1."""
        llm = self.cfg.llm
        return {"model": llm.model, "max_tokens": llm.max_tokens, "temperature": llm.temperature,
                "system": system, "messages": messages, "tools": tools, "tool_choice": tool_choice}

    def call(self, system: str, messages: list, tools: list, tool_choice) -> dict:
        request = self.build_request(system, messages, tools, tool_choice)
        key = request_key(request)
        path = self.cache_dir / f"{key}.json"
        if path.exists():
            entry = json.loads(path.read_text(encoding="utf-8"))
            hit = True
        elif self.mode == "replay":
            raise CacheMiss(key)
        else:
            entry = self._record(key, request)
            write_entry(path, entry)
            hit = False
        response = entry["response"]
        usage = response.get("usage") or {}
        self.calls.append({"key": key, "hit": hit, "latency_s": entry["latency_s"],
                           "input_tokens": usage.get("input_tokens"), "output_tokens": usage.get("output_tokens")})
        return response

    def _record(self, key: str, request: dict) -> dict:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise MissingApiKey("ANTHROPIC_API_KEY is not set; record mode needs it on a cache miss")
        if self._sdk is None:
            # retries are counted here (C.4), so the SDK's own are off
            self._sdk = anthropic.Anthropic(max_retries=0)
        # a request without tools (narration) sends neither tools nor tool_choice
        kwargs = {k: v for k, v in request.items() if not (k in ("tools", "tool_choice") and not v)}
        for attempt in range(len(RETRY_WAITS) + 1):
            try:
                t0 = time.perf_counter()
                message = self._sdk.messages.create(**kwargs)
                latency = round(time.perf_counter() - t0, 3)
                break
            except anthropic.APIStatusError as err:
                if attempt == len(RETRY_WAITS) or not _retryable(err):
                    raise
                time.sleep(RETRY_WAITS[attempt])
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return {"key": key, "request": request, "response": message.model_dump(mode="json"), "latency_s": latency}
