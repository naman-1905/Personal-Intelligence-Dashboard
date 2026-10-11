"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import { getPreferences, updatePreferences } from "@/lib/api";

function MobileNav() {
  const pathname = usePathname();
  return (
    <nav className="mobile-nav">
      <Link href="/" className={pathname === "/" ? "active" : ""}>
        Feed
      </Link>
      <Link href="/digest" className={pathname === "/digest" ? "active" : ""}>
        Briefing
      </Link>
      <Link href="/bookmarks" className={pathname === "/bookmarks" ? "active" : ""}>
        Saved
      </Link>
      <Link href="/settings" className={pathname === "/settings" ? "active" : ""}>
        Settings
      </Link>
    </nav>
  );
}

export default function AppShell({ categories, topics = [], children }) {
  const [theme, setTheme] = useState("system");

  useEffect(() => {
    getPreferences()
      .then((p) => setTheme(p.theme || "system"))
      .catch(() => {});
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const resolved = theme === "system" ? (prefersDark ? "dark" : "light") : theme;
    root.setAttribute("data-theme", resolved);
  }, [theme]);

  async function cycleTheme() {
    const order = ["system", "light", "dark"];
    const next = order[(order.indexOf(theme) + 1) % order.length];
    setTheme(next);
    try {
      await updatePreferences({ theme: next });
    } catch {
      // local preview still updates
    }
  }

  return (
    <div className="app-shell">
      <Suspense fallback={<aside className="sidebar" />}>
        <Sidebar categories={categories} topics={topics} theme={theme} onThemeCycle={cycleTheme} />
      </Suspense>
      <main className="main">{children}</main>
      <MobileNav />
    </div>
  );
}
