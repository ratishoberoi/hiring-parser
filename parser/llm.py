"""Small Gemini REST client. No provider dependency is needed at install time."""
from __future__ import annotations
import json, os, time, urllib.error, urllib.request
from pathlib import Path
from typing import Any

PROMPT = (Path(__file__).parent / "prompts" / "system.txt").read_text(encoding="utf-8")

class LLMError(RuntimeError):
    pass

def estimate_tokens(text: str) -> int:
    # Conservative provider-independent estimate, documented as approximate.
    return max(1, (len(text) + 3) // 4)

def extract_with_gemini(brief: str, timeout: float = 20.0) -> tuple[dict[str, Any], dict[str, int | str]]:
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise LLMError("GEMINI_API_KEY is not configured")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    payload = {"system_instruction": {"parts": [{"text": PROMPT}]}, "contents": [{"parts": [{"text": brief}]}], "generationConfig": {"temperature": 0, "responseMimeType": "application/json"}}
    request = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    last: Exception | None = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = json.loads(response.read())
            text = body["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(text)
            usage = body.get("usageMetadata", {})
            stats = {"input_tokens": usage.get("promptTokenCount", estimate_tokens(PROMPT + brief)), "output_tokens": usage.get("candidatesTokenCount", estimate_tokens(text)), "source": "provider" if usage else "approximate"}
            if not isinstance(result, dict): raise ValueError("model JSON is not an object")
            return result, stats
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError, json.JSONDecodeError) as exc:
            last = exc
            if attempt == 0: time.sleep(0.2)
    raise LLMError(f"Gemini request failed: {last}")
