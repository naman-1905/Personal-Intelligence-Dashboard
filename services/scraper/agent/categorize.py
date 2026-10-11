def ensure_category(item: dict, source: dict) -> str:
    return item.get("category") or source.get("category") or "general"
