"use client";

import { useState } from "react";
import { toggleBookmark } from "@/lib/api";

export default function BookmarkButton({ id, initial = false }) {
  const [bookmarked, setBookmarked] = useState(initial);

  async function onClick() {
    const updated = await toggleBookmark(id);
    setBookmarked(Boolean(updated.bookmarked));
  }

  return (
    <button type="button" className={`bookmark-control ${bookmarked ? "is-saved" : ""}`} onClick={onClick}>
      <span aria-hidden="true">{bookmarked ? "★" : "☆"}</span>{bookmarked ? "Saved" : "Save story"}
    </button>
  );
}
