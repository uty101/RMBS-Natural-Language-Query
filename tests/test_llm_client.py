"""Step 4.1: the cached client (instruction 04 C)."""

import json

import anthropic
import pytest

from rmbsq.llm.client import CacheMiss, LLMClient, MissingApiKey, request_key
from tests.llm_helpers import response, seed

SYSTEM = "You are a test."
MESSAGES = [{"role": "user", "content": "Say hello."}]


def test_key_stable(cfg):
    a = LLMClient(cfg).build_request(SYSTEM, MESSAGES, [], None)
    b = dict(reversed(list(a.items())))
    b["messages"] = [dict(reversed(list(m.items()))) for m in a["messages"]]
    assert list(a) != list(b)
    assert request_key(a) == request_key(b)
    assert len(request_key(a)) == 64


def test_replay_hit(cfg, tmp_path):
    client = LLMClient(cfg, cache_dir=tmp_path)
    key = seed(client, SYSTEM, MESSAGES, [], None, "text_hello")
    assert client.call(SYSTEM, MESSAGES, [], None) == response("text_hello")
    assert client.calls == [{"key": key, "hit": True, "latency_s": 1.234, "input_tokens": 12, "output_tokens": 3}]


def test_replay_miss_raises(cfg, tmp_path):
    client = LLMClient(cfg, cache_dir=tmp_path)
    key = request_key(client.build_request(SYSTEM, MESSAGES, [], None))
    with pytest.raises(CacheMiss) as err:
        client.call(SYSTEM, MESSAGES, [], None)
    assert err.value.key == key
    assert list(tmp_path.iterdir()) == []


def _no_sdk(*args, **kwargs):
    raise AssertionError("the SDK client must not be created")


def test_record_hit_does_not_call_api(cfg, tmp_path, monkeypatch):
    monkeypatch.setattr(anthropic, "Anthropic", _no_sdk)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = LLMClient(cfg, mode="record", cache_dir=tmp_path)
    seed(client, SYSTEM, MESSAGES, [], None, "text_hello")
    assert client.call(SYSTEM, MESSAGES, [], None) == response("text_hello")
    assert client.calls[0]["hit"] is True


def test_missing_key_raises(cfg, tmp_path, monkeypatch):
    monkeypatch.setattr(anthropic, "Anthropic", _no_sdk)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    client = LLMClient(cfg, mode="record", cache_dir=tmp_path)
    with pytest.raises(MissingApiKey):
        client.call(SYSTEM, MESSAGES, [], None)
    assert list(tmp_path.iterdir()) == []


class _Message:
    def __init__(self, data):
        self.data = data

    def model_dump(self, mode):
        assert mode == "json"
        return self.data


class _FakeSdk:
    """Stands in for anthropic.Anthropic; records the create kwargs."""
    seen = []

    def __init__(self, **kwargs):
        self.messages = self

    def create(self, **kwargs):
        _FakeSdk.seen.append(kwargs)
        return _Message(response("text_hello"))


def test_cache_file_format(cfg, tmp_path, monkeypatch):
    monkeypatch.setattr(anthropic, "Anthropic", _FakeSdk)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    client = LLMClient(cfg, mode="record", cache_dir=tmp_path)
    client.call(SYSTEM, MESSAGES, [], None)
    key = client.calls[0]["key"]
    assert client.calls[0]["hit"] is False
    raw = (tmp_path / f"{key}.json").read_bytes()
    assert raw.endswith(b"}\n") and b"\r" not in raw
    entry = json.loads(raw.decode("utf-8"))
    assert list(entry) == ["key", "latency_s", "request", "response"]
    assert entry["key"] == key == request_key(entry["request"])
    assert entry["request"] == client.build_request(SYSTEM, MESSAGES, [], None)
    assert entry["response"] == response("text_hello")
    assert isinstance(entry["latency_s"], float) and round(entry["latency_s"], 3) == entry["latency_s"]
    assert raw.decode("utf-8") == json.dumps(entry, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    # a request without tools sends neither tools nor tool_choice
    assert "tools" not in _FakeSdk.seen[-1] and "tool_choice" not in _FakeSdk.seen[-1]
