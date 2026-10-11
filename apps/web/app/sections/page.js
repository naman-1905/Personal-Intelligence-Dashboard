import Link from "next/link";
import { getCategories, getTopics } from "@/lib/api";

export default async function SectionsPage() {
  let categories = [];
  let topics = [];
  try {
    [categories, topics] = await Promise.all([getCategories(), getTopics()]);
  } catch {
    // API may still be starting — render empty sections
  }

  return (
    <div>
      <h1 className="page-title">Sections</h1>
      <p className="page-sub">
        Every category and research topic, with what&apos;s waiting in each.
      </p>

      <section className="sections-block">
        <div className="section-label">Categories</div>
        {categories.length === 0 ? (
          <div className="empty">No categories available yet.</div>
        ) : (
          <ul className="section-grid">
            {categories.map((c) => (
              <li key={c.slug}>
                <Link href={`/?category=${c.slug}`} className="section-card">
                  <span className="section-name">{c.name}</span>
                  <span className="section-count">
                    {c.unread_count > 0 ? `${c.unread_count} unread` : "caught up"}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      {topics.length > 0 ? (
        <section className="sections-block">
          <div className="section-label">Research topics</div>
          <ul className="section-grid">
            {topics.map((t) => (
              <li key={t.slug}>
                <Link href={`/?topic=${t.slug}`} className="section-card">
                  <span className="section-name">{t.name}</span>
                  <span className="section-count">
                    {t.article_count > 0 ? `${t.article_count} articles` : "no articles yet"}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <section className="sections-block">
        <div className="section-label">More</div>
        <ul className="nav-list section-more">
          <li>
            <Link href="/digest">Morning briefing</Link>
          </li>
          <li>
            <Link href="/bookmarks">Bookmarks</Link>
          </li>
        </ul>
      </section>
    </div>
  );
}
