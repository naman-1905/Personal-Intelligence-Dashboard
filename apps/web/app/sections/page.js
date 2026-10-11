import Link from "next/link";
import { getCategories } from "@/lib/api";

export default async function SectionsPage() {
  let categories = [];
  try {
    categories = await getCategories();
  } catch {
    // API may still be starting — render empty sections
  }

  return (
    <div>
      <h1 className="page-title">Sections</h1>
      <p className="page-sub">Choose a lane and keep your attention where it matters.</p>

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

    </div>
  );
}
