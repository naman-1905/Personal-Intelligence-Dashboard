"use client";

import Link from "next/link";
import { timeAgo } from "@/lib/time";

export default function ArticleCard({
  article,
  focused = false,
  onBookmark,
  onMarkRead,
}) {
  return (
    <article
      className={`article-card fade-in ${article.read ? "read" : ""} ${focused ? "focused" : ""}`}
      data-id={article.id}
    >
      <div className="meta">
        <span>{article.source}</span>
        <span>·</span>
        <span>{timeAgo(article.published_at)}</span>
        {article.importance ? (
          <>
            <span>·</span>
            <span className={`importance ${article.importance === "high" ? "high" : ""}`}>
              {article.importance}
            </span>
          </>
        ) : null}
      </div>
      <h2>
        <Link href={`/article/${article.id}`} onClick={() => onMarkRead?.(article.id)}>
          {article.title}
        </Link>
      </h2>
      <p className="summary">{article.summary}</p>
      <div className="actions">
        <Link href={`/article/${article.id}`} onClick={() => onMarkRead?.(article.id)}>
          Open
        </Link>
        <a href={article.url} target="_blank" rel="noopener noreferrer">
          Read original →
        </a>
        <button
          type="button"
          className={article.bookmarked ? "bookmarked" : ""}
          onClick={() => onBookmark?.(article.id)}
        >
          {article.bookmarked ? "Bookmarked" : "Bookmark"}
        </button>
      </div>
    </article>
  );
}
