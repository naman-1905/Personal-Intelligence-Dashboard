import { Suspense } from "react";
import "./globals.css";
import AppShell from "@/components/AppShell";
import { getCategories, getTopics } from "@/lib/api";

export const metadata = {
  title: "Brief — Local News Dashboard",
  description: "Self-hosted personal news briefing. No algorithmic feed.",
  manifest: "/manifest.json",
};

export const viewport = {
  themeColor: "#1a1a1a",
  width: "device-width",
  initialScale: 1,
};

async function safeCategories() {
  try {
    return await getCategories();
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
