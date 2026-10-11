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
    <button type="button" className="btn" onClick={onClick}>
      {bookmarked ? "Bookmarked" : "Bookmark"}
    </button>
  );
}
