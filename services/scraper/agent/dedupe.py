from __future__ import annotations

import hashlib
import re


def normalize_title(title: str) -> str:
    t = title.lower().strip()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t


def content_hash(title: str, url: str = "") -> str:
    base = normalize_title(title)
    if url:
        base = f"{base}|{url.strip().lower()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def title_hash(title: str) -> str:
    return hashlib.sha256(normalize_title(title).encode("utf-8")).hexdigest()
