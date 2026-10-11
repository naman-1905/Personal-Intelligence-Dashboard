"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import ArticleCard from "@/components/ArticleCard";
import { getArticles, markRead, toggleBookmark } from "@/lib/api";

export default function SearchPage() {
  const params = useSearchParams();
  const initialQ = params.get("q") || "";
  const [query, setQuery] = useState(initialQ);
  const [submitted, setSubmitted] = useState(initialQ);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function runSearch(e) {
    e?.preventDefault();
    const q = (query || "").trim();
    if (!q) return;
    setLoading(true);
    setError("");
    try {
      const data = await getArticles({ q, page: 1, page_size: 30 });
      setItems(data.items || []);
      setSubmitted(q);
    } catch (err) {
      setError(err.message || "Search failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleBookmark(id) {
    const updated = await toggleBookmark(id);
    setItems((prev) => prev.map((a) => (a.id === id ? { ...a, ...updated } : a)));
  }

  async function handleMarkRead(id) {
    try {
      const updated = await markRead(id);
      setItems((prev) => prev.map((a) => (a.id === id ? { ...a, ...updated } : a)));
    } catch {
      // ignore offline/read failures for navigation
    }
  }

  return (
    <div>
      <h1 className="page-title">Search</h1>
      <p className="page-sub">Full-text search across titles, summaries and tags.</p>

      <form className="toolbar" onSubmit={runSearch}>
        <input
          id="search"
          className="search"
          placeholder="What are you looking for?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className="btn" type="submit" disabled={loading || !query.trim()}>
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {error ? (
        <div className="empty">{error}</div>
      ) : submitted ? (
        items.length === 0 ? (
          <div className="empty">No results for “{submitted}”.</div>
        ) : (
          <div className="feed">
            {items.map((article) => (
              <ArticleCard
                key={article.id}
                article={article}
                onBookmark={handleBookmark}
                onMarkRead={handleMarkRead}
              />
            ))}
          </div>
        )
      ) : null}
    </div>
  );
}
