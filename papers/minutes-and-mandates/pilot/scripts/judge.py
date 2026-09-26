"""Pluggable org-policy judge.

Backends:
- mock: deterministic dry-run used by CI. No network and no token counts.
- llama: local llama.cpp (llama-cpp-python) on CPU, pinned GGUF.
- openai: any OpenAI-compatible chat endpoint (JUDGE_BASE_URL + JUDGE_MODEL).

Model text is schema-validated. Invalid JSON is not rewritten. One new
generation is the only retry, and its tokens are added to the step total.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

import jsonschema

from prompts import PILOT

# Optional larger pin selected with JUDGE_MODEL_PIN=qwen25-7b.
import model_pin as _model_pin_4b
import model_pin_7b as _model_pin_7b


def _active_pin_module():
    choice = os.environ.get("JUDGE_MODEL_PIN", "qwen3-4b").strip().lower()
    if choice in {"", "qwen3-4b", "4b", "default"}:
        return _model_pin_4b
    if choice in {"qwen25-7b", "7b"}:
        return _model_pin_7b
    raise SystemExit(f"unknown JUDGE_MODEL_PIN {choice}")


def ensure_gguf():
    return _active_pin_module().ensure_gguf()


def pin_record():
    return _active_pin_module().pin_record()


SCHEMA_PATH = PILOT / "schema" / "judge_output.schema.json"

RETRY_USER = (
    "The previous response failed JSON schema validation. "
    "Return one JSON object that matches the schema. Do not add prose."
)

DEFAULT_DECODE = {
    "temperature": 0.0,
    "top_p": 1.0,
    "top_k": 1,
    "min_p": 0.0,
    "typical_p": 1.0,
    "repeat_penalty": 1.0,
    "presence_penalty": 0.0,
    "frequency_penalty": 0.0,
    "max_tokens": 384,
    "seed": 20260926,
}


def load_output_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def grammar_schema() -> dict:
    """Schema passed to the llama.cpp JSON grammar. Constraints stay in validation."""
    schema = load_output_schema()
    return _strip_grammar_noise(schema)


def _strip_grammar_noise(value):
    if isinstance(value, dict):
        return {
            key: _strip_grammar_noise(item)
            for key, item in value.items()
            if key not in {"$schema", "$id", "title", "description"}
        }
    if isinstance(value, list):
        return [_strip_grammar_noise(item) for item in value]
    return value


def validator() -> jsonschema.Draft202012Validator:
    return jsonschema.Draft202012Validator(load_output_schema())


def parse_judge_output(text: str) -> tuple[dict | None, str | None]:
    """Validate model text. Does not repair, strip fences, or coerce types."""
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, f"json: {exc.msg}"
    if not isinstance(value, dict):
        return None, "json: expected an object"
    errors = sorted(validator().iter_errors(value), key=lambda err: list(err.absolute_path))
    if errors:
        return None, f"schema: {errors[0].message}"
    return value, None


class Completion:
    def __init__(
        self,
        *,
        text: str,
        tokens_in: int | None,
        tokens_out: int | None,
        wall_time_ms: int | None,
        token_count_source: str,
        finish_reason: str | None = None,
    ) -> None:
        self.text = text
        self.tokens_in = tokens_in
        self.tokens_out = tokens_out
        self.wall_time_ms = wall_time_ms
        self.token_count_source = token_count_source
        self.finish_reason = finish_reason


class MockJudge:
    """CI dry-run. Does not read the step or the policy."""

    name = "dry-run-mock"
    measures = False

    def complete(self, messages: list[dict]) -> Completion:
        del messages
        raise RuntimeError("mock judge has no model call")

    def describe(self) -> dict:
        return {"judge": self.name}


class ScriptedJudge:
    """Test double. Each complete() pops one scripted response."""

    name = "scripted"
    measures = True

    def __init__(self, texts: list[str]) -> None:
        self.texts = list(texts)
        self.seen: list[list[dict]] = []

    def complete(self, messages: list[dict]) -> Completion:
        self.seen.append(messages)
        text = self.texts.pop(0)
        return Completion(
            text=text,
            tokens_in=3,
            tokens_out=2,
            wall_time_ms=5,
            token_count_source="scripted",
            finish_reason="stop",
        )

    def describe(self) -> dict:
        return {"judge": self.name}


def messages_for_attempt(base: list[dict], previous_raw: str | None) -> list[dict]:
    if previous_raw is None:
        return list(base)
    return list(base) + [
        {"role": "assistant", "content": previous_raw},
        {"role": "user", "content": RETRY_USER},
    ]


def _mock_evaluation() -> dict:
    return {
        "decision": "allow",
        "matched_cards": [],
        "rationale": "dry-run mock; not a measured judgment",
        "risk_score": None,
        "risk_score_omitted": True,
        "parse_ok": True,
        "parse_failure_count": 0,
        "attempt_count": 0,
        "attempts": [],
        "tokens_in": None,
        "tokens_out": None,
        "wall_time_ms": None,
    }


def _accepted(parsed: dict) -> dict:
    omitted = "risk_score" not in parsed
    return {
        "decision": parsed["decision"],
        "matched_cards": parsed["matched_cards"],
        "rationale": parsed["rationale"],
        "risk_score": None if omitted else parsed["risk_score"],
        "risk_score_omitted": omitted,
    }


def evaluate(judge, messages: list[dict]) -> dict:
    """Judge one step. At most one retry. Never edits model text."""
    if not judge.measures:
        return _mock_evaluation()

    attempts = []
    tokens_in = 0
    tokens_out = 0
    wall_time_ms = 0
    previous_raw = None
    accepted = None
    for attempt_index in (1, 2):
        completion = judge.complete(messages_for_attempt(messages, previous_raw))
        if not isinstance(completion.tokens_in, int) or not isinstance(completion.tokens_out, int):
            raise RuntimeError("measuring judge returned no token counts")
        if not isinstance(completion.wall_time_ms, int):
            raise RuntimeError("measuring judge returned no wall time")
        parsed, error = parse_judge_output(completion.text)
        attempts.append(
            {
                "attempt": attempt_index,
                "parse_ok": parsed is not None,
                "parse_error": error,
                "tokens_in": completion.tokens_in,
                "tokens_out": completion.tokens_out,
                "wall_time_ms": completion.wall_time_ms,
                "token_count_source": completion.token_count_source,
                "finish_reason": completion.finish_reason,
                "raw_output": completion.text,
            }
        )
        tokens_in += completion.tokens_in
        tokens_out += completion.tokens_out
        wall_time_ms += completion.wall_time_ms
        if parsed is not None:
            accepted = _accepted(parsed)
            break
        previous_raw = completion.text

    failures = sum(1 for item in attempts if not item["parse_ok"])
    result = {
        "decision": None,
        "matched_cards": [],
        "rationale": None,
        "risk_score": None,
        "risk_score_omitted": None,
        "parse_ok": accepted is not None,
        "parse_failure_count": failures,
        "attempt_count": len(attempts),
        "attempts": attempts,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "wall_time_ms": wall_time_ms,
    }
    if accepted is not None:
        result.update(accepted)
    return result


def openai_request_body(
    model: str,
    messages: list[dict],
    decode: dict,
    response_format_mode: str,
    schema: dict,
) -> dict:
    body = {
        "model": model,
        "messages": messages,
        "temperature": decode["temperature"],
        "top_p": decode["top_p"],
        "max_tokens": decode["max_tokens"],
        "seed": decode["seed"],
    }
    if response_format_mode == "json_schema":
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": "judge_output",
                "strict": True,
                "schema": schema,
            },
        }
    elif response_format_mode == "json_object":
        body["response_format"] = {"type": "json_object"}
    elif response_format_mode == "off":
        pass
    else:
        raise SystemExit(f"unknown JUDGE_RESPONSE_FORMAT {response_format_mode}")
    return body


class OpenAICompatibleJudge:
    """Chat completions at JUDGE_BASE_URL for JUDGE_MODEL. Optional JUDGE_API_KEY."""

    name = "openai-compatible"
    measures = True

    def __init__(self, decode: dict | None = None) -> None:
        base = os.environ.get("JUDGE_BASE_URL")
        model = os.environ.get("JUDGE_MODEL")
        if not base or not model:
            raise SystemExit("openai judge requires JUDGE_BASE_URL and JUDGE_MODEL")
        self.base_url = base.rstrip("/")
        self.model = model
        self.api_key = os.environ.get("JUDGE_API_KEY")
        self.response_format_mode = os.environ.get("JUDGE_RESPONSE_FORMAT", "json_schema")
        self.timeout_s = float(os.environ.get("JUDGE_TIMEOUT_S", "600"))
        self.decode = dict(DEFAULT_DECODE if decode is None else decode)
        self.schema = grammar_schema()

    def complete(self, messages: list[dict]) -> Completion:
        body = openai_request_body(
            self.model,
            messages,
            self.decode,
            self.response_format_mode,
            self.schema,
        )
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        request = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"openai-compatible HTTP {exc.code}: {detail}") from exc
        elapsed_ms = int(round((time.perf_counter() - t0) * 1000))
        try:
            choice = payload["choices"][0]
            text = choice["message"].get("content") or ""
            usage = payload["usage"]
            tokens_in = usage["prompt_tokens"]
            tokens_out = usage["completion_tokens"]
            finish_reason = choice.get("finish_reason")
        except (KeyError, TypeError, IndexError) as exc:
            raise RuntimeError("openai-compatible response missing choices or usage") from exc
        if not isinstance(tokens_in, int) or not isinstance(tokens_out, int):
            raise RuntimeError("openai-compatible usage token counts are not integers")
        return Completion(
            text=text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            wall_time_ms=elapsed_ms,
            token_count_source="openai.usage",
            finish_reason=finish_reason,
        )

    def describe(self) -> dict:
        return {
            "judge": self.name,
            "openai_base_url": self.base_url,
            "openai_model": self.model,
            "response_format": self.response_format_mode,
        }


class LlamaCppJudge:
    """Local CPU llama.cpp. n_gpu_layers is 0. Weights stay out of git."""

    name = "llama-cpp"
    measures = True

    def __init__(
        self,
        model_path: Path,
        *,
        n_ctx: int,
        n_threads: int,
        n_batch: int,
        decode: dict | None = None,
    ) -> None:
        import llama_cpp
        from llama_cpp.llama_grammar import json_schema_to_gbnf

        self.decode = dict(DEFAULT_DECODE if decode is None else decode)
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.n_batch = n_batch
        self.model_path = Path(model_path)
        self.response_format = {"type": "json_object", "schema": grammar_schema()}
        json_schema_to_gbnf(json.dumps(self.response_format["schema"]))
        t0 = time.perf_counter()
        self.llm = llama_cpp.Llama(
            model_path=str(self.model_path),
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_threads_batch=n_threads,
            n_batch=n_batch,
            n_gpu_layers=0,
            offload_kqv=False,
            seed=self.decode["seed"],
            verbose=False,
        )
        self.load_wall_time_ms = int(round((time.perf_counter() - t0) * 1000))
        template = self.llm.metadata.get("tokenizer.chat_template")
        if not template:
            raise RuntimeError("GGUF has no tokenizer.chat_template; refusing the llama-2 fallback")
        self.chat_template = template
        self.chat_format = self.llm.chat_format
        self.system_info = llama_cpp.llama_cpp.llama_print_system_info().decode("utf-8", errors="replace")

    def complete(self, messages: list[dict]) -> Completion:
        # n_tokens must be 0 before generate(), or llama.cpp reuses a token
        # prefix from the previous call and the wall time is not a full eval.
        self.llm.reset()
        t0 = time.perf_counter()
        response = self.llm.create_chat_completion(
            messages=messages,
            temperature=self.decode["temperature"],
            top_p=self.decode["top_p"],
            top_k=self.decode["top_k"],
            min_p=self.decode["min_p"],
            typical_p=self.decode["typical_p"],
            repeat_penalty=self.decode["repeat_penalty"],
            presence_penalty=self.decode["presence_penalty"],
            frequency_penalty=self.decode["frequency_penalty"],
            max_tokens=self.decode["max_tokens"],
            seed=self.decode["seed"],
            response_format=self.response_format,
        )
        elapsed_ms = int(round((time.perf_counter() - t0) * 1000))
        choice = response["choices"][0]
        text = choice["message"].get("content") or ""
        usage = response.get("usage") or {}
        tokens_in = usage.get("prompt_tokens")
        tokens_out = usage.get("completion_tokens")
        if not isinstance(tokens_in, int) or not isinstance(tokens_out, int):
            raise RuntimeError(f"llama.cpp usage missing token counts: {usage!r}")
        return Completion(
            text=text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            wall_time_ms=elapsed_ms,
            token_count_source="llama_cpp.usage",
            finish_reason=choice.get("finish_reason"),
        )

    def describe(self) -> dict:
        pinned = pin_record()
        return {
            "judge": self.name,
            "model_repo": pinned["repo_id"],
            "model_revision": pinned["revision"],
            "model_filename": pinned["filename"],
            "model_sha256": pinned["sha256"],
            "quantization": pinned["quantization"],
            "n_threads": self.n_threads,
            "n_ctx": self.n_ctx,
            "n_batch": self.n_batch,
            "n_gpu_layers": 0,
        }


def library_versions() -> dict:
    import importlib.metadata as metadata
    import sys

    def version(dist: str) -> str | None:
        try:
            return metadata.version(dist)
        except metadata.PackageNotFoundError:
            return None

    versions = {
        "python": sys.version.split()[0],
        "jsonschema": version("jsonschema"),
        "pyyaml": version("pyyaml"),
        "llama_cpp_python": version("llama-cpp-python"),
        "huggingface_hub": version("huggingface_hub"),
    }
    return versions


def build_llama_judge(
    *,
    n_ctx: int,
    n_threads: int,
    n_batch: int,
    decode: dict | None = None,
) -> LlamaCppJudge:
    path = ensure_gguf()
    return LlamaCppJudge(
        path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        n_batch=n_batch,
        decode=decode,
    )
