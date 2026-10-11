db = db.getSiblingDB('news_dashboard');

db.articles.createIndex({ category: 1, published_at: -1 });
db.articles.createIndex({ dedup_hash: 1 }, { unique: true });
db.articles.createIndex({ importance: 1 });
db.articles.createIndex({ title: 'text', summary: 'text', tags: 'text' });
db.articles.createIndex({ status: 1, scraped_at: -1 });

db.sources.createIndex({ name: 1 }, { unique: true });
db.sources.createIndex({ category: 1, enabled: 1 });

db.categories.createIndex({ slug: 1 }, { unique: true });
db.categories.createIndex({ display_order: 1 });

db.topics.createIndex({ slug: 1 }, { unique: true });

db.user_preferences.createIndex({ user_id: 1 }, { unique: true });

db.user_article_state.createIndex({ user_id: 1, article_id: 1 }, { unique: true });
db.user_article_state.createIndex({ user_id: 1, bookmarked: 1 });

db.scrape_runs.createIndex({ started_at: -1 });
db.scrape_runs.createIndex({ source: 1, started_at: -1 });

const categories = [
  { slug: 'technology', name: 'Technology', icon: 'cpu', display_order: 1, enabled: true },
  { slug: 'science', name: 'Science', icon: 'atom', display_order: 2, enabled: true },
  { slug: 'world', name: 'World', icon: 'globe', display_order: 3, enabled: true },
  { slug: 'business', name: 'Business', icon: 'briefcase', display_order: 4, enabled: true },
  { slug: 'topics', name: 'Topics', icon: 'tag', display_order: 5, enabled: true },
];

categories.forEach((c) => {
  db.categories.updateOne({ slug: c.slug }, { $setOnInsert: c }, { upsert: true });
});

const sources = [
  {
    name: 'arstechnica',
    display_name: 'Ars Technica',
    category: 'technology',
    type: 'rss',
    url: 'https://feeds.arstechnica.com/arstechnica/index',
    trust_tier: 1,
    enabled: true,
    parser: {},
  },
  {
    name: 'hn',
    display_name: 'Hacker News Front',
    category: 'technology',
    type: 'rss',
    url: 'https://hnrss.org/frontpage',
    trust_tier: 1,
    enabled: true,
    parser: {},
  },
  {
    name: 'nasa',
    display_name: 'NASA Breaking News',
    category: 'science',
    type: 'rss',
    url: 'https://www.nasa.gov/rss/dyn/breaking_news.rss',
    trust_tier: 1,
    enabled: true,
    parser: {},
  },
  {
    name: 'bbc-world',
    display_name: 'BBC World',
    category: 'world',
    type: 'rss',
    url: 'https://feeds.bbci.co.uk/news/world/rss.xml',
    trust_tier: 1,
    enabled: true,
    parser: {},
  },
  {
    name: 'reuters-business',
    display_name: 'Reuters Business',
    category: 'business',
    type: 'rss',
    url: 'https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best',
    trust_tier: 1,
    enabled: false,
    parser: {},
  },
];

sources.forEach((s) => {
  db.sources.updateOne({ name: s.name }, { $setOnInsert: s }, { upsert: true });
});

db.user_preferences.updateOne(
  { user_id: 'local' },
  {
    $setOnInsert: {
      user_id: 'local',
      selected_categories: ['technology', 'science', 'world', 'business'],
      category_order: ['technology', 'science', 'world', 'business'],
      mute_keywords: [],
      theme: 'system',
      digest_hour: 7,
      refresh_interval_minutes: null,
      show_thumbnails: false,
      notify_high_importance: false,
    },
  },
  { upsert: true }
);
