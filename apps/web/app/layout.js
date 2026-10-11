import { Suspense } from "react";
import "./globals.css";
import AppShell from "@/components/AppShell";
import { getCategories, getTopics } from "@/lib/api";
import { ALLOWED_CATEGORIES, isAllowedCategory } from "@/lib/categories";

export const metadata = {
  title: "Brief — Local News Dashboard",
  description: "Self-hosted personal news briefing. No algorithmic feed.",
  manifest: "/manifest.json",
};

export const viewport = {
  themeColor: "#339af0",
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

async function safeCategories() {
  try {
    const categories = await getCategories();
    return ALLOWED_CATEGORIES.map((allowed) => categories.find((category) => isAllowedCategory(category.slug) && category.slug.includes(allowed.slug)) || allowed);
  } catch {
    return [];
  }
}

async function safeTopics() {
  try {
    return await getTopics();
  } catch {
    return [];
  }
}

export default async function RootLayout({ children }) {
  const [categories, topics] = await Promise.all([safeCategories(), safeTopics()]);

  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <Suspense>
          <AppShell categories={categories} topics={topics}>
            {children}
          </AppShell>
        </Suspense>
      </body>
    </html>
  );
}
