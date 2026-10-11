import Link from "next/link";
import { getDigest } from "@/lib/api";
import DigestList from "@/components/DigestList";

export default async function DigestPage() {
  let items = [];
  try {
    items = await getDigest();
  } catch {
    items = [];
  }

  return (
    <div>
      <h1 className="page-title">Morning briefing</h1>
      <p className="page-sub">
        High-importance items since your digest hour. Open once, read once — then close the app.
      </p>
      <DigestList initial={items} />
      <p style={{ marginTop: "2rem" }}>
        <Link href="/">← Full feed</Link>
      </p>
    </div>
  );
}
