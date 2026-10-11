import Link from "next/link";
import { getArticle } from "@/lib/api";
import { timeAgo } from "@/lib/time";
import BookmarkButton from "@/components/BookmarkButton";
import MarkReadOnMount from "@/components/MarkReadOnMount";

export default async function ArticlePage({ params }) {
  const { id } = await params;
  let article;
  try {
    article = await getArticle(id);
  } catch {
    return (
      <div className="detail">
        <h1 className="page-title">Article not found</h1>
        <p className="page-sub">It may have been archived, or the API is still starting.</p>
        <Link href="/">← Back</Link>
      </div>
    );
  }

  return (
    <article className="detail fade-in">
      <MarkReadOnMount id={article.id} />
      <p className="meta">
        <span>{article.source}</span>
        <span>·</span>
        <span>{timeAgo(article.published_at)}</span>
        <span>·</span>
        <span className="importance">{article.importance}</span>
      </p>
      <h1 className="page-title">{article.title}</h1>
      <p className="summary">{article.summary}</p>
      {article.tags?.length ? (
        <div className="tags">{article.tags.map((t) => `#${t}`).join("  ")}</div>
      ) : null}
      <div className="actions">
        <a className="btn btn-accent" href={article.url} target="_blank" rel="noopener noreferrer">
          Read full article →
        </a>
        <BookmarkButton id={article.id} initial={article.bookmarked} />
        <Link href="/">← Feed</Link>
      </div>
    </article>
  );
}
