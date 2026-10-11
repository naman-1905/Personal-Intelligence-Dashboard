"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

export default function Sidebar({ categories = [], topics = [], theme, onThemeCycle }) {
  const pathname = usePathname();
  const params = useSearchParams();
  const activeCategory = params.get("category");
  const activeTopic = params.get("topic");

  return (
    <aside className="sidebar">
      <div className="brand">
        Brief
        <span>Local news · no feed noise</span>
      </div>

      <nav>
        <ul className="nav-list">
          <li>
            <Link href="/" className={pathname === "/" && !activeCategory ? "active" : ""}>
              All
            </Link>
          </li>
          <li>
            <Link href="/digest" className={pathname === "/digest" ? "active" : ""}>
              Morning briefing
            </Link>
          </li>
          <li>
            <Link href="/bookmarks" className={pathname === "/bookmarks" ? "active" : ""}>
              Bookmarks
            </Link>
          </li>
        </ul>
      </nav>

      <nav>
        <ul className="nav-list">
          {categories.map((c) => (
            <li key={c.slug}>
              <Link
                href={`/?category=${c.slug}`}
                className={activeCategory === c.slug ? "active" : ""}
              >
                <span>{c.name}</span>
                {c.unread_count > 0 ? <span className="badge">{c.unread_count}</span> : null}
              </Link>
            </li>
          ))}
        </ul>
      </nav>

      {topics.length > 0 ? (
        <nav>
          <div className="section-label">Research topics</div>
          <ul className="nav-list">
            {topics.map((t) => (
              <li key={t.slug}>
                <Link
                  href={`/?topic=${t.slug}`}
                  className={activeTopic === t.slug ? "active" : ""}
                >
                  <span>{t.name}</span>
                  {t.article_count > 0 ? (
                    <span className="badge">{t.article_count}</span>
                  ) : null}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      ) : null}

      <div style={{ marginTop: "auto" }}>
        <ul className="nav-list">
          <li>
            <button type="button" className="linkish" onClick={onThemeCycle}>
              Theme: {theme}
            </button>
          </li>
          <li>
            <Link href="/settings" className={pathname === "/settings" ? "active" : ""}>
              Settings
            </Link>
          </li>
        </ul>
      </div>
    </aside>
  );
}
