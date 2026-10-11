import Feed from "@/components/Feed";
import { getArticles, getStats } from "@/lib/api";
import { isAllowedCategory } from "@/lib/categories";

export default async function HomePage({ searchParams }) {
  const sp = await searchParams;
  const category = sp?.category && isAllowedCategory(sp.category) ? sp.category : undefined;
  const topic = sp?.topic || undefined;
  const q = sp?.q || undefined;
  const importance = sp?.importance || undefined;

  let articles = { items: [], page: 1, page_size: 20, total: 0, has_more: false };
  let stats = null;
  try {
    [articles, stats] = await Promise.all([
      getArticles({ category, topic, q, importance, page: 1, page_size: 20 }),
      getStats(),
    ]);
  } catch {
    // API may still be starting
  }

  const title = topic
    ? `Topic: ${topic.replace(/-/g, " ")}`
    : category
      ? category.charAt(0).toUpperCase() + category.slice(1)
      : "Today";
  const subtitle = topic
    ? `Research feed for “${topic.replace(/-/g, " ")}” — refreshed from topics.txt after every scrape cycle.`
    : category
      ? `Trusted sources in ${category}. Summaries only — open the original when it matters.`
      : "Cards from sources you chose. Filtered locally. Nothing ranking for engagement.";

  return (
    <Feed
      initial={articles}
      category={category}
      topic={topic}
      importance={importance}
      q={q || ""}
      title={title}
      subtitle={subtitle}
      stats={stats}
    />
  );
}
