export const ALLOWED_CATEGORIES = [
  { slug: "gaming", name: "Gaming", icon: "◉" },
  { slug: "technology", name: "Technology", icon: "⌁" },
  { slug: "general", name: "General", icon: "✦" },
  { slug: "cars-f1", name: "Cars & F1", icon: "↗" },
  { slug: "marvel", name: "Marvel", icon: "✧" },
];

export function isAllowedCategory(slug = "") {
  const value = slug.toLowerCase().replace(/[_\s]/g, "-");
  return ALLOWED_CATEGORIES.some((category) => value === category.slug || value.includes(category.slug));
}
