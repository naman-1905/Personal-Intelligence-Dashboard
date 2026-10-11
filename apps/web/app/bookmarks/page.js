import { getBookmarks } from "@/lib/api";
import DigestList from "@/components/DigestList";

export default async function BookmarksPage() {
  let items = [];
  try {
    items = await getBookmarks();
  } catch {
    items = [];
  }

  return (
    <div>
      <h1 className="page-title">Bookmarks</h1>
      <p className="page-sub">Read later — without hunting through yesterday&apos;s feed.</p>
      <DigestList initial={items} />
    </div>
  );
}
