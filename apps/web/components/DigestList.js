"use client";

import { useState } from "react";
import ArticleCard from "@/components/ArticleCard";
import { markRead, toggleBookmark } from "@/lib/api";

export default function DigestList({ initial = [] }) {
  const [items, setItems] = useState(initial);

  async function handleBookmark(id) {
    const updated = await toggleBookmark(id);
    setItems((prev) => prev.map((a) => (a.id === id ? { ...a, ...updated } : a)));
  }

  async function handleMarkRead(id) {
    try {
      const updated = await markRead(id);
      setItems((prev) => prev.map((a) => (a.id === id ? { ...a, ...updated } : a)));
    } catch {
      // ignore
    }
  }

  if (!items.length) {
    return (
      <div className="empty">
        Nothing high-priority in the briefing window yet. Trigger a scrape from the home feed.
      </div>
    );
  }

  return (
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
  );
}
