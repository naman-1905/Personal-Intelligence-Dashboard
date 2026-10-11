"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import ArticleCard from "@/components/ArticleCard";
import {
  getArticles,
  markRead,
  toggleBookmark,
  triggerScrape,
} from "@/lib/api";
import { ALLOWED_CATEGORIES } from "@/lib/categories";

export default function Feed({
  initial,
  category,
  topic,
  importance,
  q: initialQ = "",
  title,
  subtitle,
  stats,
}) {
  const router = useRouter();
  const [data, setData] = useState(initial);
  const [query, setQuery] = useState(initialQ);
  const [focusIdx, setFocusIdx] = useState(0);
  const [loadingMore, setLoadingMore] = useState(false);
  const [scraping, setScraping] = useState(false);
  const items = data?.items || [];

  const refresh = useCallback(
    async (page = 1, append = false) => {
      const next = await getArticles({
        category,
        topic,
        importance,
        q: query || undefined,
        page,
        page_size: 20,
      });
      setData((prev) =>
        append
          ? { ...next, items: [...(prev?.items || []), ...next.items] }
          : next
      );
    },
    [category, topic, importance, query]
  );

  useEffect(() => {
    setData(initial);
    setFocusIdx(0);
  }, [initial]);

  useEffect(() => {
    function onKey(e) {
      const tag = document.activeElement?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea") {
        if (e.key === "Escape") document.activeElement.blur();
        return;
      }
      if (e.key === "/") {
        e.preventDefault();
        document.getElementById("search")?.focus();
      } else if (e.key === "j") {
        setFocusIdx((i) => Math.min(i + 1, Math.max(items.length - 1, 0)));
      } else if (e.key === "k") {
        setFocusIdx((i) => Math.max(i - 1, 0));
      } else if (e.key === "b" && items[focusIdx]) {
        handleBookmark(items[focusIdx].id);
      } else if (e.key === "Enter" && items[focusIdx]) {
        router.push(`/article/${items[focusIdx].id}`);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [items, focusIdx, router]);

  async function handleBookmark(id) {
    const updated = await toggleBookmark(id);
    setData((prev) => ({
      ...prev,
      items: prev.items.map((a) => (a.id === id ? { ...a, ...updated } : a)),
    }));
  }

  async function handleMarkRead(id) {
    try {
      const updated = await markRead(id);
      setData((prev) => ({
        ...prev,
        items: prev.items.map((a) => (a.id === id ? { ...a, ...updated } : a)),
      }));
    } catch {
      // ignore offline/read failures for navigation
    }
  }

  async function onSearch(e) {
    e.preventDefault();
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (topic) params.set("topic", topic);
    if (query) params.set("q", query);
    router.push(`/?${params.toString()}`);
    await refresh(1, false);
  }

  async function loadMore() {
    if (!data?.has_more || loadingMore) return;
    setLoadingMore(true);
    try {
      await refresh((data.page || 1) + 1, true);
    } finally {
      setLoadingMore(false);
    }
  }

  async function onScrape() {
    setScraping(true);
    try {
      await triggerScrape();
      setTimeout(() => refresh(1, false), 4000);
    } finally {
      setScraping(false);
    }
  }

  return (
    <div>
      <header className="feed-header"><div><div className="eyebrow">BRIEF / YOUR DAILY SIGNAL</div><h1 className="page-title">{category ? title : "What’s new today?"}</h1><p className="page-sub">{category ? subtitle : "The stories worth your attention, gathered in one quiet place."}</p></div><div className="avatar" aria-hidden="true">N</div></header>
      <div className="category-scroller" aria-label="News categories"><a className={!category ? "selected" : ""} href="/">For you</a>{ALLOWED_CATEGORIES.map((item) => <a key={item.slug} className={category === item.slug ? "selected" : ""} href={`/?category=${item.slug}`}><span>{item.icon}</span>{item.name}</a>)}</div>
      {stats ? (
        <p className="stat-line">
          <strong>{stats.time_saved_minutes_estimate} min</strong> estimated saved ·{" "}
          {stats.articles_filtered_today} filtered today · {stats.sources_enabled} sources
        </p>
      ) : null}

      <form className="toolbar" onSubmit={onSearch}>
        <input
          id="search"
          className="search"
          placeholder="Search title, summary, tags — press /"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className="search-btn" type="submit" aria-label="Search">⌕</button>
      </form>

      <div className="feed">
        {items.length === 0 ? (
          <div className="empty">
            No articles yet. Trigger a scrape, or wait for the scheduled run (every 6 hours).
          </div>
        ) : (
          items.map((article, idx) => (
            <ArticleCard
              key={article.id}
              article={article}
              focused={idx === focusIdx}
              onBookmark={handleBookmark}
              onMarkRead={handleMarkRead}
            />
          ))
        )}
      </div>

      {data?.has_more ? (
        <div style={{ marginTop: "1.25rem" }}>
          <button className="btn" type="button" onClick={loadMore} disabled={loadingMore}>
            {loadingMore ? "Loading…" : "Load more"}
          </button>
        </div>
      ) : null}
    </div>
  );
}
