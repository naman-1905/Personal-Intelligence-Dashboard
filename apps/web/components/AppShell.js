"use client";

import { Suspense, useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import MobileNav from "@/components/MobileNav";

export default function AppShell({ categories, topics = [], children }) {
  return (
    <div className="app-shell">
      <Suspense fallback={<aside className="sidebar" />}>
        <Sidebar categories={categories} topics={topics} />
      </Suspense>
      <main className="main">{children}</main>
      <MobileNav />
    </div>
  );
}
