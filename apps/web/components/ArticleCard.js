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
      <div className="flashcard-topline">
        <span className="category-pill">{article.category || "General"}</span>
        <span>{timeAgo(article.published_at)}</span>
      </div>
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
      <h2 className="flashcard-title">
        <Link href={`/article/${article.id}`} onClick={() => onMarkRead?.(article.id)}>
          {article.title}
        </Link>
      </h2>
      <p className="summary">{article.summary || "A concise briefing from your selected sources."}</p>
      <div className="card-footer">
        <Link className="read-story" href={`/article/${article.id}`} onClick={() => onMarkRead?.(article.id)}>
          Read story <span aria-hidden="true">→</span>
        </Link>
        <button
          type="button"
          className={article.bookmarked ? "bookmarked" : ""}
          onClick={() => onBookmark?.(article.id)}
        >
          {article.bookmarked ? "★ Saved" : "☆ Save"}
        </button>
      </div>
    </article>
  );
}
