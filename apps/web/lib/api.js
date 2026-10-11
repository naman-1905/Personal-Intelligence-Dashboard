const PUBLIC_API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const INTERNAL_API = process.env.INTERNAL_API_URL || PUBLIC_API;

function baseUrl() {
  if (typeof window === "undefined") {
    return INTERNAL_API;
  }
  return PUBLIC_API;
}

async function request(path, options = {}) {
  const res = await fetch(`${baseUrl()}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export function getArticles(params = {}) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") qs.set(k, String(v));
  });
  const q = qs.toString();
  return request(`/articles${q ? `?${q}` : ""}`);
}

export function getArticle(id) {
  return request(`/articles/${id}`);
}

export function getDigest() {
  return request("/articles/digest?when=morning");
}

export function getBookmarks() {
  return request("/articles/bookmarks");
}

export function getCategories() {
  return request("/categories");
}

export function getTopics() {
  return request("/topics");
}

export function getSources() {
  return request("/sources");
}

export function getPreferences() {
  return request("/preferences");
}

export function updatePreferences(body) {
  return request("/preferences", { method: "POST", body: JSON.stringify(body) });
}

export function getStats() {
  return request("/stats");
}

export function markRead(id) {
  return request(`/articles/${id}/read`, { method: "POST" });
}

export function toggleBookmark(id) {
  return request(`/articles/${id}/bookmark`, { method: "POST" });
}

export function triggerScrape() {
  return request("/admin/trigger-scrape", { method: "POST" });
}

export function getHealth() {
  return request("/health");
}
