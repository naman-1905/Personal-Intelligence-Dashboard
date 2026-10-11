from sources.rss import fetch_rss


def fetch_source(source: dict) -> list[dict]:
    stype = source.get("type", "rss")
    if stype == "rss":
        return fetch_rss(source)
    # html/api stubs for later phases — prefer RSS when available
    return fetch_rss(source)
