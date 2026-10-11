from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from config import get_settings

logger = logging.getLogger(__name__)

PROMPT = """You are a news relevance filter for a personal news dashboard. Given a headline and a short excerpt, return ONLY valid JSON:
{{
  "pass": true or false,
  "importance": "low" | "medium" | "high",
  "tags": ["tag1", "tag2"],
  "summary": "2-3 neutral factual sentences, no hype",
  "is_noise": true or false
}}
The excerpt may be truncated or contain site boilerplate (navigation text, link/point counts). Judge primarily from the headline. Set pass=false only when the headline itself is clickbait, a rumor, pure opinion, celebrity gossip, or empty promotion. Legitimate news headlines about technology, science, world events, and business should pass.
Title: {title}
Excerpt: {excerpt}
"""


def _heuristic(item: dict) -> dict[str, Any]:
    title = item.get("title", "")
    text = item.get("raw_text", "")[:500]
    lower = f"{title} {text}".lower()
    noise_markers = ["sponsored", "click here", "you won't believe", "deal of the day"]
    is_noise = any(m in lower for m in noise_markers)
    importance = "medium"
    if any(w in lower for w in ["breaking", "urgent", "security", "vulnerability", "launch"]):
        importance = "high"
    elif len(title) < 20:
        importance = "low"
    summary = text[:280] if text else title
    tags = [item.get("category", "general")]
    return {
        "pass": not is_noise,
        "importance": importance,
        "tags": tags,
        "summary": summary,
        "is_noise": is_noise,
    }


def _extract_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None


def filter_item(item: dict) -> dict[str, Any]:
    settings = get_settings()
    title = item.get("title", "")
    excerpt = (item.get("raw_text") or "")[:500]
    prompt = PROMPT.format(title=title, excerpt=excerpt)

    try:
        with httpx.Client(timeout=60.0) as client:
            resp = client.post(
                f"{settings.ollama_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0.1, "num_predict": 384},
                },
            )
            if resp.status_code != 200:
                logger.warning("Ollama HTTP %s — using heuristic", resp.status_code)
                return _heuristic(item)
            data = resp.json()
            parsed = _extract_json(data.get("response", ""))
            if not parsed:
                return _heuristic(item)
            return {
                "pass": bool(parsed.get("pass", True)) and not parsed.get("is_noise", False),
                "importance": parsed.get("importance", "medium")
                if parsed.get("importance") in {"low", "medium", "high"}
                else "medium",
                "tags": parsed.get("tags") or [item.get("category", "general")],
                "summary": (parsed.get("summary") or excerpt or title)[:500],
                "is_noise": bool(parsed.get("is_noise", False)),
            }
    except Exception as exc:  # noqa: BLE001
        logger.warning("Ollama unavailable (%s) — heuristic filter", exc)
        return _heuristic(item)
